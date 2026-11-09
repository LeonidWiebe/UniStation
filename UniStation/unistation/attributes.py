"""Saved active attributes for new UniStation geometry, separate from selection."""

from unistation.i18n import tr

from unistation.palette import (
    PaletteError, PaletteProxy, PaletteViewProxy, colors_for_display, same_document,
)
from unistation import line_weights


SCHEMA = "UstnAttributesSchema"
COLOR_INDEX = "UstnActiveColorIndex"
LINE_STYLE = "UstnActiveLineStyle"
LINE_WEIGHT = "UstnActiveLineWeightIndex"
DEFAULT_LINE_WEIGHT = 0
LINE_STYLES = ("Solid", "Dashed", "Dotted", "Dashdot")
DEFAULT_LINE_STYLE = "Solid"
VERSION = 1
DEFAULT_COLOR_INDEX = 7
OBJECT_NAME = "UstnActiveAttributes"
GROUP = "Активные атрибуты UniStation"


class AttributesProxy(PaletteProxy):
    """Persistent metadata only; inherited execution/serialization are no-ops."""


class AttributesViewProxy(PaletteViewProxy):
    """A tree item without geometry, using the shared metadata view provider."""


def settings_object(document):
    """Find a single valid settings object without creating or repairing data."""
    found = []
    expected = {SCHEMA: "App::PropertyInteger",
                COLOR_INDEX: "App::PropertyIntegerConstraint"}
    for obj in document.Objects:
        names = set(obj.PropertiesList)
        if not names.intersection((*expected, LINE_STYLE, LINE_WEIGHT)):
            continue
        if (obj.TypeId != "App::FeaturePython"
                or any(name not in names or obj.getTypeIdOfProperty(name) != kind
                       for name, kind in expected.items())):
            raise PaletteError(tr('UniStation active attributes are damaged. Automatic repair is not performed.'))
        if getattr(obj, SCHEMA) != VERSION:
            raise PaletteError(tr('Unsupported UniStation active attributes version.'))
        _index(getattr(obj, COLOR_INDEX))
        _saved_line_style(obj)
        _saved_line_weight(obj)
        found.append(obj)
    if len(found) > 1:
        raise PaletteError(tr('The document contains multiple UniStation active attribute sets.'))
    return found[0] if found else None


def active_color_index(document):
    """Read the saved index; an untouched document uses index 7 in memory."""
    same_document(document)
    obj = settings_object(document)
    return _index(getattr(obj, COLOR_INDEX)) if obj is not None else DEFAULT_COLOR_INDEX


def color_snapshot(document):
    """Validate settings and palette before a command acquires native input."""
    index = active_color_index(document)
    _palette, colors = colors_for_display(document)
    return index, colors


def active_line_style(document):
    """Old color-only settings have an implicit Solid style, without a write."""
    same_document(document)
    obj = settings_object(document)
    return _saved_line_style(obj) if obj is not None else DEFAULT_LINE_STYLE


def drawing_snapshot(document):
    """Validate/freeze active indexes/style before a creating command gets input."""
    index, _colors = color_snapshot(document)
    weight, _widths = weight_snapshot(document)
    return index, active_line_style(document), weight


def weight_snapshot(document):
    same_document(document)
    obj = settings_object(document)
    index = _saved_line_weight(obj) if obj is not None else DEFAULT_LINE_WEIGHT
    _table, widths = line_weights.widths_for_display(document)
    return index, widths


def set_active_line_weight(document, index):
    """Save the active index and document table together; never repaint geometry."""
    line_weights.require_index(index)
    same_document(document)
    current = settings_object(document)
    table, _widths = line_weights.widths_for_display(document)
    if (current is not None and LINE_WEIGHT in current.PropertiesList and table is not None
            and _saved_line_weight(current) == index):
        return
    document.openTransaction(tr('UniStation: active line weight'))
    try:
        if current is None:
            current = _create_settings(document)
        if LINE_WEIGHT not in current.PropertiesList:
            _add_line_weight(current)
        line_weights.ensure_table_in_transaction(document)
        setattr(current, LINE_WEIGHT, (index, 0, 31, 1))
        current.setEditorMode(LINE_WEIGHT, 1)
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        raise


def set_active_line_style(document, style):
    """Persist a style in its own Undo step, preserving the active color."""
    _style(style)
    same_document(document)
    current = settings_object(document)
    if (current is not None and LINE_STYLE in current.PropertiesList
            and _saved_line_style(current) == style):
        return
    document.openTransaction(tr('UniStation: active line style'))
    try:
        if current is None:
            current = _create_settings(document)
        if LINE_STYLE not in current.PropertiesList:
            _add_line_style(current)
        setattr(current, LINE_STYLE, style)
        current.setEditorMode(LINE_STYLE, 1)
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        raise


def apply_line_style_in_transaction(document, obj, style):
    """Set native DrawStyle; creation owns the transaction and its rollback."""
    _style(style)
    same_document(document)
    if obj.Document is not document or document.getObject(obj.Name) is not obj:
        raise PaletteError(tr('The new element is no longer available in the drawing document.'))
    view = getattr(obj, "ViewObject", None)
    if (view is None or "DrawStyle" not in view.PropertiesList
            or view.getTypeIdOfProperty("DrawStyle") != "App::PropertyEnumeration"
            or style not in (view.getEnumerationsOfProperty("DrawStyle") or ())):
        raise PaletteError(tr('The new element does not support the selected line style.'))
    view.DrawStyle = style


def set_active_color(document, index):
    """Persist only the active index in one Undo step; existing elements stay as is."""
    _index(index)
    same_document(document)
    colors_for_display(document)
    current = settings_object(document)
    if current is not None and _index(getattr(current, COLOR_INDEX)) == index:
        return
    document.openTransaction(tr('UniStation: active color'))
    try:
        if current is None:
            current = _create_settings(document)
        setattr(current, COLOR_INDEX, (index, 0, 255, 1))
        current.setEditorMode(SCHEMA, 1)
        current.setEditorMode(COLOR_INDEX, 1)
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        raise


def _create_settings(document):
    name = OBJECT_NAME
    if document.getObject(name) is not None:
        name = document.getUniqueObjectName(name)
    obj = document.addObject("App::FeaturePython", name)
    if obj is None or document.getObject(obj.Name) is not obj:
        raise PaletteError(tr('Could not save UniStation active attributes.'))
    AttributesProxy(obj)
    obj.Label = "Активные атрибуты UniStation"
    obj.addProperty("App::PropertyInteger", SCHEMA, GROUP, "Версия активных атрибутов.")
    setattr(obj, SCHEMA, VERSION)
    obj.addProperty("App::PropertyIntegerConstraint", COLOR_INDEX, GROUP,
                    "Индекс цвета новых элементов UniStation: 0..255. Не меняет выделение.")
    setattr(obj, COLOR_INDEX, (DEFAULT_COLOR_INDEX, 0, 255, 1))
    _add_line_style(obj)
    _add_line_weight(obj)
    obj.setEditorMode(SCHEMA, 1)
    obj.setEditorMode(COLOR_INDEX, 1)
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        AttributesViewProxy(view)
        view.Visibility = False
    return obj


def _add_line_style(obj):
    obj.addProperty("App::PropertyEnumeration", LINE_STYLE, GROUP,
                    "Штатный стиль линии новых элементов UniStation.")
    setattr(obj, LINE_STYLE, list(LINE_STYLES))
    setattr(obj, LINE_STYLE, DEFAULT_LINE_STYLE)
    obj.setEditorMode(LINE_STYLE, 1)


def _add_line_weight(obj):
    obj.addProperty("App::PropertyIntegerConstraint", LINE_WEIGHT, GROUP,
                    "Индекс толщины новых элементов UniStation: 0..31.")
    setattr(obj, LINE_WEIGHT, (DEFAULT_LINE_WEIGHT, 0, 31, 1))
    obj.setEditorMode(LINE_WEIGHT, 1)


def _saved_line_weight(obj):
    if LINE_WEIGHT not in obj.PropertiesList:
        return DEFAULT_LINE_WEIGHT
    if obj.getTypeIdOfProperty(LINE_WEIGHT) != "App::PropertyIntegerConstraint":
        raise PaletteError(tr('UniStation active line weight data is damaged.'))
    return line_weights.require_index(getattr(obj, LINE_WEIGHT))


def _saved_line_style(obj):
    if LINE_STYLE not in obj.PropertiesList:
        return DEFAULT_LINE_STYLE  # Optional additive field of schema 1.
    if (obj.getTypeIdOfProperty(LINE_STYLE) != "App::PropertyEnumeration"
            or tuple(obj.getEnumerationsOfProperty(LINE_STYLE) or ()) != LINE_STYLES):
        raise PaletteError(tr('UniStation active line style data is damaged.'))
    return _style(getattr(obj, LINE_STYLE))


def _style(value):
    if not isinstance(value, str) or value not in LINE_STYLES:
        raise PaletteError(tr('Unknown UniStation active line style.'))
    return value


def _index(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise PaletteError(tr('The active color index must be an integer from 0 to 255.'))
    return value
