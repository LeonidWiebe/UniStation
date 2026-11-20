"""Saved active attributes for new UniStation geometry, separate from selection."""

from dataclasses import dataclass

from unistation.i18n import tr

from unistation.palette import (
    PaletteError, PaletteProxy, PaletteViewProxy, colors_for_display, same_document,
)
from unistation import line_weights


SCHEMA = "UstnAttributesSchema"
COLOR_INDEX = "UstnActiveColorIndex"
LINE_STYLE = "UstnActiveLineStyle"
LINE_WEIGHT = "UstnActiveLineWeightIndex"
ACTIVE_LEVEL = "UstnActiveLevelId"
LEVEL_SOURCES = "UstnByLevelAttributes"
ELEMENT_SOURCES = "UstnElementByLevel"
BY_LEVEL = -1
COLOR_SOURCE, STYLE_SOURCE, WEIGHT_SOURCE = 1, 2, 4
ALL_SOURCES = COLOR_SOURCE | STYLE_SOURCE | WEIGHT_SOURCE
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
        if not names.intersection((*expected, LINE_STYLE, LINE_WEIGHT, ACTIVE_LEVEL, LEVEL_SOURCES)):
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
        _saved_sources(obj)
        if ACTIVE_LEVEL in names and obj.getTypeIdOfProperty(ACTIVE_LEVEL) != "App::PropertyString":
            raise PaletteError(tr('UniStation active attributes are damaged. Automatic repair is not performed.'))
        found.append(obj)
    if len(found) > 1:
        raise PaletteError(tr('The document contains multiple UniStation active attribute sets.'))
    return found[0] if found else None


def active_color_index(document):
    """Read the saved index; an untouched document uses index 7 in memory."""
    same_document(document)
    obj = settings_object(document)
    if obj is None:
        return DEFAULT_COLOR_INDEX
    return BY_LEVEL if _saved_sources(obj) & COLOR_SOURCE else _index(getattr(obj, COLOR_INDEX))


def color_snapshot(document):
    """Validate settings and palette before a command acquires native input."""
    index = active_color_index(document)
    _palette, colors = colors_for_display(document)
    return index, colors


def active_line_style(document):
    """Old color-only settings have an implicit Solid style, without a write."""
    same_document(document)
    obj = settings_object(document)
    if obj is None:
        return DEFAULT_LINE_STYLE
    return BY_LEVEL if _saved_sources(obj) & STYLE_SOURCE else _saved_line_style(obj)


def drawing_snapshot(document):
    """Resolve the active sources to concrete styles for preview and creation."""
    index, _colors = color_snapshot(document)
    weight, _widths = weight_snapshot(document)
    style = active_line_style(document)
    if BY_LEVEL in (index, style, weight):
        _records, selected = level_choices(document)
        index = selected.color_index if index == BY_LEVEL else index
        style = LINE_STYLES[selected.line_style] if style == BY_LEVEL else style
        weight = selected.weight_index if weight == BY_LEVEL else weight
    return index, style, weight


def active_level_sources(document):
    same_document(document)
    return _saved_sources(settings_object(document))


def element_level_sources(obj):
    if ELEMENT_SOURCES not in obj.PropertiesList:
        return 0
    sources = getattr(obj, ELEMENT_SOURCES)
    if (obj.getTypeIdOfProperty(ELEMENT_SOURCES) != "App::PropertyInteger"
            or type(sources) is not int or not 0 <= sources <= ALL_SOURCES):
        raise PaletteError(tr('The By Level settings of {} are damaged.').format(obj.Label))
    return sources


def set_element_level_sources(obj, sources):
    """Store sources inside the caller's transaction. Unmarked elements own all attributes."""
    if type(sources) is not int or not 0 <= sources <= ALL_SOURCES:
        raise PaletteError(tr('The By Level settings of {} are damaged.').format(obj.Label))
    if element_level_sources(obj) == sources:
        return
    if ELEMENT_SOURCES not in obj.PropertiesList:
        obj.addProperty("App::PropertyInteger", ELEMENT_SOURCES, "UniStation",
                        tr('By Level sources for color, line style and line weight'))
        obj.setEditorMode(ELEMENT_SOURCES, 1)
    setattr(obj, ELEMENT_SOURCES, sources)


def use_own_element_color(obj):
    set_element_level_sources(obj, element_level_sources(obj) & ~COLOR_SOURCE)


@dataclass(frozen=True)
class AppearanceChange:
    owner: object
    property_name: str
    before: object
    after: object

    def apply(self):
        setattr(self.owner, self.property_name, self.after)

    def restore(self):
        setattr(self.owner, self.property_name, self.before)


def level_appearance_changes(document, targets):
    """Validate inherited properties and prepare reversible writes before opening Undo."""
    from unistation import palette

    colors = (colors_for_display(document)[1]
              if any(sources & COLOR_SOURCE for _, _, sources in targets) else None)
    widths = (line_weights.widths_for_display(document)[1]
              if any(sources & WEIGHT_SOURCE for _, _, sources in targets) else None)
    changes = []
    for obj, level, sources in targets:
        view = getattr(obj, "ViewObject", None)
        if view is None:
            raise PaletteError(tr('Open the document in FreeCAD with a graphical view to update inherited attributes.'))
        if sources & COLOR_SOURCE:
            palette._require_view(obj)
            palette._require_color_properties(obj)
            if palette._color_mode(obj) != palette.MODE_INDEX:
                raise PaletteError(tr('The inherited color of {} is damaged.').format(obj.Label))
            old_index = palette._require_index(obj)
            changes.extend((
                AppearanceChange(obj, palette.INDEX_PROPERTY, (old_index, 0, 255, 1),
                                 (level.color_index, 0, 255, 1)),
                AppearanceChange(view, "LineColor", view.LineColor, palette._line_color(colors[level.color_index])),
            ))
        if sources & STYLE_SOURCE:
            style = LINE_STYLES[level.line_style]
            _require_line_style(view, style)
            changes.append(AppearanceChange(view, "DrawStyle", view.DrawStyle, style))
        if sources & WEIGHT_SOURCE:
            if ("LineWidth" not in view.PropertiesList or line_weights.INDEX not in obj.PropertiesList
                    or view.getTypeIdOfProperty("LineWidth") != "App::PropertyFloatConstraint"
                    or obj.getTypeIdOfProperty(line_weights.INDEX) != "App::PropertyIntegerConstraint"):
                raise PaletteError(tr('The inherited line weight of {} is damaged.').format(obj.Label))
            old_index = line_weights.require_index(getattr(obj, line_weights.INDEX))
            changes.extend((
                AppearanceChange(obj, line_weights.INDEX, (old_index, 0, 31, 1), (level.weight_index, 0, 31, 1)),
                AppearanceChange(view, "LineWidth", view.LineWidth, widths[level.weight_index]),
            ))
    return [change for change in changes if change.before != change.after]


def weight_snapshot(document):
    same_document(document)
    obj = settings_object(document)
    index = _saved_line_weight(obj) if obj is not None else DEFAULT_LINE_WEIGHT
    if _saved_sources(obj) & WEIGHT_SOURCE:
        index = BY_LEVEL
    _table, widths = line_weights.widths_for_display(document)
    return index, widths


def set_active_line_weight(document, index):
    """Save the active index and document table together; never repaint geometry."""
    inherited = _is_by_level(index)
    if not inherited:
        line_weights.require_index(index)
    same_document(document)
    current = settings_object(document)
    table, _widths = line_weights.widths_for_display(document)
    if (current is not None and (inherited or (LINE_WEIGHT in current.PropertiesList and table is not None))
            and weight_snapshot(document)[0] == index):
        return
    document.openTransaction(tr('UniStation: active line weight'))
    try:
        if current is None:
            current = _create_settings(document)
        if not inherited:
            if LINE_WEIGHT not in current.PropertiesList:
                _add_line_weight(current)
            line_weights.ensure_table_in_transaction(document)
            setattr(current, LINE_WEIGHT, (index, 0, 31, 1))
            current.setEditorMode(LINE_WEIGHT, 1)
        _set_source(current, WEIGHT_SOURCE, inherited)
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        raise


def set_active_line_style(document, style):
    """Persist a style in its own Undo step, preserving the active color."""
    inherited = _is_by_level(style)
    if not inherited:
        _style(style)
    same_document(document)
    current = settings_object(document)
    if (current is not None and (inherited or LINE_STYLE in current.PropertiesList)
            and active_line_style(document) == style):
        return
    document.openTransaction(tr('UniStation: active line style'))
    try:
        if current is None:
            current = _create_settings(document)
        if not inherited:
            if LINE_STYLE not in current.PropertiesList:
                _add_line_style(current)
            setattr(current, LINE_STYLE, style)
            current.setEditorMode(LINE_STYLE, 1)
        _set_source(current, STYLE_SOURCE, inherited)
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
    _require_line_style(view, style)
    view.DrawStyle = style


def _require_line_style(view, style):
    if (view is None or "DrawStyle" not in view.PropertiesList
            or view.getTypeIdOfProperty("DrawStyle") != "App::PropertyEnumeration"
            or style not in (view.getEnumerationsOfProperty("DrawStyle") or ())):
        raise PaletteError(tr('The new element does not support the selected line style.'))


def set_active_color(document, index):
    """Persist only the active index in one Undo step; existing elements stay as is."""
    inherited = _is_by_level(index)
    if not inherited:
        _index(index)
    same_document(document)
    colors_for_display(document)
    current = settings_object(document)
    if current is not None and active_color_index(document) == index:
        return
    document.openTransaction(tr('UniStation: active color'))
    try:
        if current is None:
            current = _create_settings(document)
        if not inherited:
            setattr(current, COLOR_INDEX, (index, 0, 255, 1))
        _set_source(current, COLOR_SOURCE, inherited)
        current.setEditorMode(SCHEMA, 1)
        current.setEditorMode(COLOR_INDEX, 1)
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        raise


def level_choices(document):
    from unistation.levels import available_levels

    same_document(document)
    records = available_levels(document)
    return records, _selected_level(document, records)


def placement_level_id(document):
    from unistation.levels import LevelUnavailableError, read_table, require_unlocked_level

    same_document(document)
    _table, records = read_table(document)
    if records is None:
        return None
    level = _selected_level(document, records)
    require_unlocked_level(level)
    if not level.available_for_drawing:
        raise LevelUnavailableError(tr('The active level “{}” is off or frozen. Choose a visible, thawed level.')
                                    .format(level.name))
    return level.identifier


def _selected_level(document, records):
    from unistation.levels import DEFAULT_ID

    obj = settings_object(document)
    identifier = getattr(obj, ACTIVE_LEVEL, DEFAULT_ID)
    lookup = {level.identifier: level for level in records}
    return lookup.get(identifier, lookup[DEFAULT_ID])


def set_active_level(document, identifier):
    records, current = level_choices(document)
    if identifier == current.identifier:
        return
    if not any(level.identifier == identifier for level in records):
        raise PaletteError(tr('The selected level is no longer available.'))
    if document.HasPendingTransaction:
        raise PaletteError(tr('Finish the current task first.'))
    obj = settings_object(document)
    document.openTransaction(tr('UniStation: active level'))
    try:
        if obj is None:
            obj = _create_settings(document)
        if ACTIVE_LEVEL not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", ACTIVE_LEVEL, GROUP, locked=True)
            obj.setEditorMode(ACTIVE_LEVEL, 1)
        setattr(obj, ACTIVE_LEVEL, identifier)
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        raise


def _is_by_level(value):
    return type(value) is int and value == BY_LEVEL


def _saved_sources(obj):
    if obj is None or LEVEL_SOURCES not in obj.PropertiesList:
        return 0
    mask = getattr(obj, LEVEL_SOURCES)
    if obj.getTypeIdOfProperty(LEVEL_SOURCES) != "App::PropertyInteger" or type(mask) is not int or not 0 <= mask <= ALL_SOURCES:
        raise PaletteError(tr('UniStation active attributes are damaged. Automatic repair is not performed.'))
    return mask


def _set_source(obj, bit, inherited):
    mask = _saved_sources(obj)
    updated = (mask | bit) if inherited else (mask & ~bit)
    if updated == mask:
        return
    if LEVEL_SOURCES not in obj.PropertiesList:
        obj.addProperty("App::PropertyInteger", LEVEL_SOURCES, GROUP, locked=True)
        obj.setEditorMode(LEVEL_SOURCES, 1)
    setattr(obj, LEVEL_SOURCES, updated)


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
