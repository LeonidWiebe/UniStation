"""Document-owned indexed screen widths. No global repaint or nested transactions."""

from unistation.i18n import tr

import math

from unistation.palette import PaletteError, PaletteProxy, PaletteViewProxy, same_document


SCHEMA = "UstnLineWeightSchema"
WIDTHS = "UstnLineWeightWidths"
INDEX = "UstnLineWeightIndex"
PREVIOUS_EDITOR_MODE = "UstnPreviousLineWidthEditorMode"
VERSION = 1
COUNT = 32
OBJECT_NAME = "UstnLineWeightTable"
GROUP = "Толщина UniStation"


class LineWeightProxy(PaletteProxy):
    """Shared no-op metadata persistence; widths live in native properties."""


class LineWeightViewProxy(PaletteViewProxy):
    """Table has no geometry and no links to drawing objects."""


def builtin_widths():
    return tuple(float(index + 1) for index in range(COUNT))


def require_index(index):
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < COUNT:
        raise PaletteError(tr('The line weight index must be an integer from 0 to 31.'))
    return index


def _validated_widths(values):
    if len(values) != COUNT:
        raise PaletteError(tr('The line weight table must contain exactly 32 values.'))
    result = []
    for value in values:
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 1 <= value <= 64):
            raise PaletteError(tr('A screen width in the line weight table must be a number from 1 to 64.'))
        result.append(float(value))
    return tuple(result)


def table_object(document):
    """Recognize reserved markers, reject broken/duplicate tables, never repair."""
    found = []
    for obj in document.Objects:
        names = set(obj.PropertiesList)
        if not names.intersection((SCHEMA, WIDTHS)):
            continue
        if (obj.TypeId != "App::FeaturePython"
                or SCHEMA not in names or WIDTHS not in names
                or obj.getTypeIdOfProperty(SCHEMA) != "App::PropertyInteger"
                or obj.getTypeIdOfProperty(WIDTHS) != "App::PropertyFloatList"):
            raise PaletteError(tr('The UniStation line weight table is damaged. Automatic repair is not performed.'))
        if getattr(obj, SCHEMA) != VERSION:
            raise PaletteError(tr('Unsupported UniStation line weight table version.'))
        _validated_widths(getattr(obj, WIDTHS))
        found.append(obj)
    if len(found) > 1:
        raise PaletteError(tr('The document contains multiple UniStation line weight tables.'))
    return found[0] if found else None


def indexed_objects(document):
    result = []
    for obj in document.Objects:
        if INDEX in obj.PropertiesList:
            if obj.getTypeIdOfProperty(INDEX) != "App::PropertyIntegerConstraint":
                raise PaletteError(tr('An element has a damaged UniStation line weight index.'))
            require_index(getattr(obj, INDEX))
            result.append(obj)
    return result


def widths_for_display(document):
    """An empty/old document uses defaults in memory, never over orphaned indexes."""
    same_document(document)
    table = table_object(document)
    if table is None:
        if indexed_objects(document):
            raise PaletteError(tr(('Elements have line weight indices but the table is missing. Undo the table deletion; the '
                                'built-in table is not substituted.')))
        return None, builtin_widths()
    return table, _validated_widths(getattr(table, WIDTHS))


def ensure_table_in_transaction(document):
    """Caller owns commit/abort. Never change existing table values."""
    table, widths = widths_for_display(document)
    if table is None:
        name = OBJECT_NAME
        if document.getObject(name) is not None:
            name = document.getUniqueObjectName(name)
        table = document.addObject("App::FeaturePython", name)
        if table is None or document.getObject(table.Name) is not table:
            raise PaletteError(tr('Could not save the UniStation line weight table.'))
        LineWeightProxy(table)
        table.Label = "Таблица толщин UniStation"
        table.addProperty("App::PropertyInteger", SCHEMA, GROUP, "Версия таблицы экранных толщин.")
        setattr(table, SCHEMA, VERSION)
        table.addProperty("App::PropertyFloatList", WIDTHS, GROUP,
                          "32 экранные ширины для индексов 0..31, в пикселях. Не миллиметры печати.")
        setattr(table, WIDTHS, list(widths))
        table.setEditorMode(SCHEMA, 1)
        table.setEditorMode(WIDTHS, 1)
        view = getattr(table, "ViewObject", None)
        if view is not None:
            LineWeightViewProxy(view)
            view.Visibility = False
    return table, widths


def apply_in_transaction(document, obj, index):
    """Apply only to newly created geometry inside the creator's transaction."""
    require_index(index)
    same_document(document)
    if obj.Document is not document or document.getObject(obj.Name) is not obj:
        raise PaletteError(tr('The new element is no longer available in the drawing document.'))
    view = getattr(obj, "ViewObject", None)
    if (view is None or "LineWidth" not in view.PropertiesList
            or view.getTypeIdOfProperty("LineWidth") != "App::PropertyFloatConstraint"):
        raise PaletteError(tr('The new element does not support screen line width.'))
    if INDEX in obj.PropertiesList or PREVIOUS_EDITOR_MODE in obj.PropertiesList:
        raise PaletteError(tr('The new element already has indexed line weight data.'))
    _table, widths = ensure_table_in_transaction(document)
    obj.addProperty("App::PropertyIntegerConstraint", INDEX, GROUP,
                    "Индекс толщины UniStation 0..31; ширина определяется таблицей документа.")
    setattr(obj, INDEX, (index, 0, 31, 1))
    # Preserve the original mask for a future explicit return to native width.
    modes = view.getEditorMode("LineWidth")
    mask = (1 if "ReadOnly" in modes else 0) | (2 if "Hidden" in modes else 0)
    obj.addProperty("App::PropertyInteger", PREVIOUS_EDITOR_MODE, GROUP,
                    "Режим редактора LineWidth до индексного назначения.", 0, False, True)
    setattr(obj, PREVIOUS_EDITOR_MODE, mask)
    obj.setEditorMode(INDEX, 1)
    obj.setEditorMode(PREVIOUS_EDITOR_MODE, 3)
    view.LineWidth = widths[index]
    view.setEditorMode("LineWidth", mask | 1)
