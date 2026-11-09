"""Document palette data and FreeCAD property updates for indexed color.

Pure JSON and RGB helpers do not import FreeCAD. Document changes go through
the functions below them and always belong to one caller-supplied document.
"""

from unistation.i18n import tr

import json
import os
import tempfile


FORMAT = "unistation-palette"
VERSION = 1
COLOR_COUNT = 256
MAX_BYTES = 1024 * 1024
PALETTE_OBJECT_NAME = "UstnColorPalette"
PALETTE_LABEL = "Палитра UniStation"
SCHEMA_PROPERTY = "UstnPaletteSchema"
DATA_PROPERTY = "UstnPaletteData"
MODE_PROPERTY = "UstnColorMode"
INDEX_PROPERTY = "UstnColorIndex"
EDITOR_MODE_PROPERTY = "UstnPreviousLineColorEditorMode"
COLOR_GROUP = "Цвет UniStation"
PALETTE_GROUP = "Палитра UniStation"
MODE_DIRECT = "DirectRGB"
MODE_INDEX = "PaletteIndex"
MODES = [MODE_DIRECT, MODE_INDEX]
_CUBE = (0, 95, 135, 175, 215, 255)
_BASIC = (
    (0, 0, 0),
    (128, 0, 0),
    (0, 128, 0),
    (128, 128, 0),
    (0, 0, 128),
    (128, 0, 128),
    (0, 128, 128),
    (192, 192, 192),
    (128, 128, 128),
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 0),
    (0, 0, 255),
    (255, 0, 255),
    (0, 255, 255),
    (255, 255, 255),
)


class PaletteError(Exception):
    """A refused palette operation. The document is left unchanged."""


def builtin_colors():
    """Return the 256 UniStation RGB entries. This is not a MicroStation table."""
    colors = [None] * COLOR_COUNT
    for index, rgb in enumerate(_BASIC):
        colors[index] = rgb
    for red in range(6):
        for green in range(6):
            for blue in range(6):
                colors[16 + 36 * red + 6 * green + blue] = (
                    _CUBE[red],
                    _CUBE[green],
                    _CUBE[blue],
                )
    for offset in range(24):
        level = 8 + 10 * offset
        colors[232 + offset] = (level, level, level)
    if any(item is None for item in colors) or len(colors) != COLOR_COUNT:
        raise PaletteError(tr('The built-in UniStation palette is incomplete.'))
    return tuple(colors)


def canonical_json(colors):
    """Stable ASCII JSON stored in the document. Name is not part of the snapshot."""
    return json.dumps(
        _payload(colors),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def export_text(colors, name=None):
    """Pretty UTF-8 text for a .ustnpalette.json file."""
    payload = _payload(colors)
    if name is not None:
        payload = {"name": name, **payload}
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def parse_palette_text(text):
    """Validate a whole palette document and return 256 RGB tuples in index order."""
    if not isinstance(text, str):
        raise PaletteError(tr('Palette text must be a UTF-8 string.'))
    try:
        data = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except PaletteError:
        raise
    except json.JSONDecodeError as exc:
        raise PaletteError(tr('Invalid palette JSON: ') + exc.msg) from exc
    except ValueError as exc:
        raise PaletteError(tr('Invalid palette JSON.')) from exc
    return _validate_document(data)


def parse_palette_bytes(payload):
    """Validate file bytes before any document change."""
    if not isinstance(payload, (bytes, bytearray)):
        raise PaletteError(tr('The palette file could not be read.'))
    if len(payload) > MAX_BYTES:
        raise PaletteError(tr('The palette file exceeds 1 MiB.'))
    try:
        text = bytes(payload).decode("utf-8")
    except UnicodeError as exc:
        raise PaletteError(tr('The palette file must use UTF-8 encoding.')) from exc
    return parse_palette_text(text)


def load_palette_file(path):
    """Read and fully validate a palette file. Does not touch a document."""
    if not os.path.isfile(path):
        raise PaletteError(tr('The palette file was not found.'))
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise PaletteError(tr('The palette file could not be read.')) from exc
    if size > MAX_BYTES:
        raise PaletteError(tr('The palette file exceeds 1 MiB.'))
    try:
        with open(path, "rb") as handle:
            payload = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        raise PaletteError(tr('The palette file could not be read.')) from exc
    return parse_palette_bytes(payload)


def write_palette_file(path, colors, name=None):
    """Write a complete file beside the destination, then replace it.

    Only the temporary file created by this call is removed. The destination
    is replaced after the temporary file has been fully written.
    """
    text = export_text(colors, name)
    directory = os.path.dirname(os.path.abspath(path))
    handle = None
    temporary = None
    try:
        handle, temporary = tempfile.mkstemp(
            prefix=".ustnpalette-",
            suffix=".tmp",
            dir=directory,
        )
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as output:
            handle = None
            output.write(text)
        os.replace(temporary, path)
        temporary = None
    except PaletteError:
        raise
    except OSError as exc:
        raise PaletteError(tr('Could not write the palette file: ') + str(exc)) from exc
    finally:
        if handle is not None:
            os.close(handle)
        if temporary is not None:
            try:
                os.remove(temporary)
            except OSError:
                pass


def _payload(colors):
    rows = []
    for index, rgb in enumerate(_require_table(colors)):
        rows.append({"index": index, "rgb": [rgb[0], rgb[1], rgb[2]]})
    return {"format": FORMAT, "version": VERSION, "colors": rows}


def _require_table(colors):
    if len(colors) != COLOR_COUNT:
        raise PaletteError(tr('The palette must contain exactly 256 colors.'))
    table = []
    for index, rgb in enumerate(colors):
        table.append(_require_rgb(rgb, index))
    return tuple(table)


def _require_rgb(value, index):
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, (list, tuple))
        or len(value) != 3
    ):
        raise PaletteError(tr('Color ') + str(index) + tr(' must contain three RGB channels.'))
    channels = []
    for channel in value:
        if isinstance(channel, bool) or not isinstance(channel, int) or channel < 0 or channel > 255:
            raise PaletteError(
                tr('RGB channels of color ') + str(index) + tr(' must be integers from 0 to 255.')
            )
        channels.append(channel)
    return tuple(channels)


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PaletteError(tr('Duplicate JSON key “') + str(key) + tr("”."))
        result[key] = value
    return result


def _reject_constant(name):
    raise PaletteError(tr('Invalid JSON value ') + str(name) + ".")


def _validate_document(data):
    if not isinstance(data, dict):
        raise PaletteError(tr('The palette JSON root must be an object.'))
    extra = set(data) - {"format", "version", "colors", "name"}
    if extra:
        names = ", ".join(sorted(str(item) for item in extra))
        raise PaletteError(tr('Unknown fields in palette v1: ') + names + ".")
    if data.get("format") != FORMAT:
        raise PaletteError(tr('Expected format="') + FORMAT + "\".")
    version = data.get("version")
    if isinstance(version, bool) or version != VERSION:
        raise PaletteError(tr('Only version=1 is supported.'))
    if "name" in data and not isinstance(data["name"], str):
        raise PaletteError(tr('The name field must be a string.'))
    rows = data.get("colors")
    if not isinstance(rows, list) or len(rows) != COLOR_COUNT:
        raise PaletteError(tr('The colors field must contain exactly 256 entries.'))
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            raise PaletteError(tr('A color entry must be an object.'))
        row_extra = set(row) - {"index", "rgb"}
        if row_extra:
            names = ", ".join(sorted(str(item) for item in row_extra))
            raise PaletteError(tr('Unknown fields in a color entry: ') + names + ".")
        index = row.get("index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index > 255:
            raise PaletteError(tr('A color index must be an integer from 0 to 255.'))
        if index in found:
            raise PaletteError(tr('Index ') + str(index) + tr(' is specified twice.'))
        found[index] = _require_rgb(row.get("rgb"), index)
    missing = [index for index in range(COLOR_COUNT) if index not in found]
    if missing:
        raise PaletteError(tr('Missing palette index ') + str(missing[0]) + ".")
    return tuple(found[index] for index in range(COLOR_COUNT))


class PaletteProxy:
    """Keeps the metadata object executable. Colors live in document properties."""

    def __init__(self, obj):
        obj.Proxy = self

    def execute(self, obj):
        return

    def dumps(self):
        return None

    def loads(self, state):
        return None


class PaletteViewProxy:
    """No geometry. The object stays in the tree so it can be undone if removed."""

    def __init__(self, view):
        view.Proxy = self

    def attach(self, view):
        self.Object = view.Object

    def getDisplayModes(self, view):
        return ["Default"]

    def getDefaultDisplayMode(self):
        return "Default"

    def setDisplayMode(self, mode):
        return mode

    def onChanged(self, view, prop):
        return

    def updateData(self, obj, prop):
        return

    def dumps(self):
        return None

    def loads(self, state):
        return None


def same_document(document):
    """Raise if the captured document is gone or is no longer the active one."""
    import FreeCAD as App

    try:
        name = document.Name
        listed = App.listDocuments().get(name)
        active = App.ActiveDocument
    except (AttributeError, RuntimeError) as exc:
        raise PaletteError(tr('The palette document is no longer available. The command was canceled.')) from exc
    if listed is not document or active is not document:
        raise PaletteError(tr('The active document changed. The command was canceled.'))


def classify_palettes(document):
    """Return the single valid palette, or raise on duplicates and damaged data."""
    valid = []
    for obj in list(document.Objects):
        kind = _palette_kind(obj)
        if kind == "valid":
            valid.append(obj)
        elif kind == "corrupt":
            raise PaletteError(
                tr(('The UniStation palette is damaged. It is not repaired automatically. Undo the last deletion or '
                 'edit if possible.'))
            )
    if len(valid) > 1:
        raise PaletteError(
            tr(('The document contains multiple UniStation palettes. The command stopped; extra objects are not '
             'deleted.'))
        )
    return valid[0] if valid else None


def indexed_objects(document):
    """Objects whose saved mode is PaletteIndex. Direct RGB objects are omitted."""
    result = []
    for obj in list(document.Objects):
        if _color_mode(obj) == MODE_INDEX:
            result.append(obj)
    return result


def read_colors(palette):
    """Read the canonical table. Does not substitute the built-in palette."""
    if palette is None:
        raise PaletteError(tr('The document has no UniStation palette.'))
    try:
        text = palette.UstnPaletteData
    except AttributeError as exc:
        raise PaletteError(tr('The palette has no saved color table.')) from exc
    try:
        return parse_palette_text(text)
    except PaletteError as exc:
        raise PaletteError(
            tr('The saved palette is damaged and is not replaced with the built-in table.')
        ) from exc


def colors_for_display(document):
    """Colors for an open dialog. Missing palette uses the built-in table in memory.

    Indexed objects without a palette are an error: the built-in table must not
    silently repaint them.
    """
    palette = classify_palettes(document)
    indexed = indexed_objects(document)
    if palette is None and indexed:
        raise PaletteError(
            tr(('The document has indexed-color objects but no palette. The built-in table is not substituted. '
             'Undo the palette deletion or load a palette file.'))
        )
    if palette is None:
        return None, builtin_colors()
    return palette, read_colors(palette)


def displayed_rgb(obj):
    """Byte RGB currently shown by LineColor, without matching it to an index."""
    view = _require_view(obj)
    color = view.LineColor
    try:
        return tuple(
            max(0, min(255, int(round(float(color[channel]) * 255.0))))
            for channel in range(3)
        )
    except (TypeError, ValueError, IndexError) as exc:
        raise PaletteError(tr('Could not read LineColor of “') + obj.Label + tr("”.")) from exc


def color_drift(obj, colors):
    """True when a palette index is stored but LineColor no longer matches it."""
    if _color_mode(obj) != MODE_INDEX:
        return False
    index = _require_index(obj)
    return displayed_rgb(obj) != colors[index]


def assign_index(document, objects, index):
    """Create the palette if needed and set one index on all objects."""
    _require_index_value(index)
    same_document(document)
    targets = _require_targets(document, objects)
    palette = classify_palettes(document)
    if palette is None and indexed_objects(document):
        raise PaletteError(
            tr(('Indexed objects exist without a palette. The built-in table is not created and colors are not '
             'recalculated. Load a palette or undo the deletion.'))
        )

    def change():
        apply_index_in_transaction(document, targets, index)

    _transaction(document, tr('UniStation: indexed color'), change)


def apply_index_in_transaction(document, objects, index):
    """Apply an index inside a transaction owned and rolled back by the caller.

    Geometry creation uses this operation to keep the palette, metadata and
    displayed color in the same Undo step as the new geometry. This function
    deliberately does not open or commit a nested transaction.
    """
    _require_index_value(index)
    same_document(document)
    targets = _require_targets(document, objects)
    current, colors = colors_for_display(document)
    if current is None:
        _create_palette(document, colors)
    for obj in targets:
        _set_index(obj, index, colors[index])


def release_rgb(document, objects):
    """Leave indexed mode and keep the RGB that is already visible."""
    same_document(document)
    targets = [obj for obj in _require_targets(document, objects) if _color_mode(obj) == MODE_INDEX]
    if not targets:
        raise PaletteError(tr('The selected objects have no indexed color.'))

    def change():
        same_document(document)
        for obj in _require_targets(document, targets):
            if _color_mode(obj) != MODE_INDEX:
                raise PaletteError(tr('The object set changed. The command was canceled.'))
            _set_direct(obj)

    _transaction(document, tr('UniStation: direct RGB'), change)


def replace_palette(document, colors, title=tr('UniStation: load palette')):
    """Store a validated table and repaint only PaletteIndex objects in this document."""
    table = _require_table(colors)
    same_document(document)
    classify_palettes(document)
    pending = indexed_objects(document)
    for obj in pending:
        _require_view(obj)
        _require_color_properties(obj)
        _require_index(obj)

    def change():
        same_document(document)
        current = classify_palettes(document)
        if current is None:
            current = _create_palette(document, table)
        else:
            _store_colors(current, table)
        for obj in indexed_objects(document):
            _repaint_index(obj, table)
        document.recompute()

    _transaction(document, title, change)


def _transaction(document, title, change):
    document.openTransaction(title)
    try:
        change()
    except Exception:
        document.abortTransaction()
        raise
    else:
        try:
            document.commitTransaction()
        except Exception:
            document.abortTransaction()
            raise


def _create_palette(document, colors):
    name = PALETTE_OBJECT_NAME
    taken = document.getObject(name)
    if taken is not None:
        name = document.getUniqueObjectName(PALETTE_OBJECT_NAME)
    obj = document.addObject("App::FeaturePython", name)
    if obj is None or document.getObject(obj.Name) is not obj:
        raise PaletteError(tr('Could not create the document palette.'))
    PaletteProxy(obj)
    obj.Label = PALETTE_LABEL
    _add(
        obj,
        "App::PropertyInteger",
        SCHEMA_PROPERTY,
        PALETTE_GROUP,
        "Версия схемы палитры UniStation.",
        hidden=False,
    )
    obj.UstnPaletteSchema = VERSION
    _add(
        obj,
        "App::PropertyString",
        DATA_PROPERTY,
        PALETTE_GROUP,
        "Каноническая таблица из 256 цветов RGB.",
        hidden=False,
    )
    _store_colors(obj, colors)
    obj.setEditorMode(SCHEMA_PROPERTY, 1)
    obj.setEditorMode(DATA_PROPERTY, 1)
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        PaletteViewProxy(view)
        view.Visibility = False
    if _palette_kind(obj) != "valid":
        raise PaletteError(tr('The new palette failed validation and was not saved.'))
    return obj


def _store_colors(palette, colors):
    palette.UstnPaletteSchema = VERSION
    palette.UstnPaletteData = canonical_json(colors)


def _set_index(obj, index, rgb):
    _ensure_color_properties(obj, index)
    if str(obj.UstnColorMode) != MODE_INDEX:
        obj.UstnPreviousLineColorEditorMode = _editor_mask(obj.ViewObject, "LineColor")
    obj.UstnColorMode = MODE_INDEX
    obj.UstnColorIndex = (index, 0, 255, 1)
    obj.ViewObject.LineColor = _line_color(rgb)
    obj.ViewObject.setEditorMode("LineColor", 1)
    obj.setEditorMode(MODE_PROPERTY, 1)
    obj.setEditorMode(INDEX_PROPERTY, 1)


def _set_direct(obj):
    _require_color_properties(obj)
    mask = int(obj.UstnPreviousLineColorEditorMode)
    obj.UstnColorMode = MODE_DIRECT
    obj.ViewObject.setEditorMode("LineColor", mask)
    obj.setEditorMode(MODE_PROPERTY, 1)
    obj.setEditorMode(INDEX_PROPERTY, 1)


def _repaint_index(obj, colors):
    _require_color_properties(obj)
    index = _require_index(obj)
    obj.UstnColorIndex = (index, 0, 255, 1)
    obj.ViewObject.LineColor = _line_color(colors[index])
    obj.ViewObject.setEditorMode("LineColor", 1)


def _ensure_color_properties(obj, index):
    if MODE_PROPERTY not in obj.PropertiesList:
        if INDEX_PROPERTY in obj.PropertiesList or EDITOR_MODE_PROPERTY in obj.PropertiesList:
            raise PaletteError(tr('Color properties of “') + obj.Label + tr('” are incomplete.'))
        _add(
            obj,
            "App::PropertyEnumeration",
            MODE_PROPERTY,
            COLOR_GROUP,
            "Источник цвета: прямой RGB или индекс палитры. Индекс не означает «По слою».",
            enum_vals=MODES,
        )
        _add(
            obj,
            "App::PropertyIntegerConstraint",
            INDEX_PROPERTY,
            COLOR_GROUP,
            "Индекс палитры документа от 0 до 255. Ноль не является «По слою».",
        )
        _add(
            obj,
            "App::PropertyInteger",
            EDITOR_MODE_PROPERTY,
            COLOR_GROUP,
            "Режим редактора LineColor до включения индексного цвета.",
            hidden=True,
        )
        obj.UstnColorMode = MODES
        obj.UstnColorMode = MODE_DIRECT
        obj.UstnColorIndex = (index, 0, 255, 1)
        obj.UstnPreviousLineColorEditorMode = _editor_mask(obj.ViewObject, "LineColor")
    _require_color_properties(obj)


def _require_color_properties(obj):
    expected = {
        MODE_PROPERTY: "App::PropertyEnumeration",
        INDEX_PROPERTY: "App::PropertyIntegerConstraint",
        EDITOR_MODE_PROPERTY: "App::PropertyInteger",
    }
    for name, type_name in expected.items():
        if name not in obj.PropertiesList or obj.getTypeIdOfProperty(name) != type_name:
            raise PaletteError(tr('Color properties of “') + obj.Label + tr('” have an invalid type.'))
    try:
        values = list(obj.getEnumerationsOfProperty(MODE_PROPERTY))
    except AttributeError:
        values = []
    if values and values != MODES:
        raise PaletteError(tr('Color mode of “') + obj.Label + tr('” contains unknown values.'))


def _add(obj, type_name, name, group, tip, hidden=False, enum_vals=None):
    kwargs = {}
    if enum_vals is not None:
        kwargs["enum_vals"] = enum_vals
    obj.addProperty(type_name, name, group, tip, 0, False, hidden, True, **kwargs)


def _palette_kind(obj):
    try:
        names = set(obj.PropertiesList)
    except (AttributeError, RuntimeError):
        return None
    if SCHEMA_PROPERTY not in names and DATA_PROPERTY not in names:
        return None
    try:
        if obj.TypeId != "App::FeaturePython":
            return "corrupt"
        if obj.getTypeIdOfProperty(SCHEMA_PROPERTY) != "App::PropertyInteger":
            return "corrupt"
        if obj.getTypeIdOfProperty(DATA_PROPERTY) != "App::PropertyString":
            return "corrupt"
        if int(obj.UstnPaletteSchema) != VERSION:
            return "corrupt"
        parse_palette_text(obj.UstnPaletteData)
    except (AttributeError, RuntimeError, TypeError, ValueError, PaletteError):
        return "corrupt"
    return "valid"


def _color_mode(obj):
    try:
        if MODE_PROPERTY not in obj.PropertiesList:
            return None
        if obj.getTypeIdOfProperty(MODE_PROPERTY) != "App::PropertyEnumeration":
            raise PaletteError(tr('Color mode of “') + obj.Label + tr('” is damaged.'))
        mode = obj.UstnColorMode
        if mode is None:
            raise PaletteError(tr('Color mode of “') + obj.Label + tr('” is not set.'))
        return str(mode)
    except PaletteError:
        raise
    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
        raise PaletteError(tr('Could not read the color mode.')) from exc


def _require_index(obj):
    try:
        if obj.getTypeIdOfProperty(INDEX_PROPERTY) != "App::PropertyIntegerConstraint":
            raise PaletteError(tr('Color index of “') + obj.Label + tr('” is damaged.'))
        value = obj.UstnColorIndex
        if isinstance(value, (list, tuple)):
            value = value[0]
        index = int(value)
    except PaletteError:
        raise
    except (AttributeError, RuntimeError, TypeError, ValueError, IndexError) as exc:
        raise PaletteError(tr('Could not read the index of “') + obj.Label + tr("”.")) from exc
    _require_index_value(index)
    return index


def _require_index_value(index):
    if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index > 255:
        raise PaletteError(tr('The index must be an integer from 0 to 255.'))


def _require_targets(document, objects):
    if not objects:
        raise PaletteError(tr('Select one or more whole objects.'))
    checked = []
    for obj in objects:
        try:
            if obj.Document is not document:
                raise PaletteError(tr('The object belongs to another document.'))
        except (AttributeError, RuntimeError) as exc:
            raise PaletteError(tr('The selected object is no longer available.')) from exc
        _require_view(obj)
        checked.append(obj)
    return checked


def _require_view(obj):
    view = getattr(obj, "ViewObject", None)
    if view is None or not hasattr(view, "LineColor"):
        raise PaletteError(tr('Object “') + getattr(obj, "Label", "") + tr('” has no line color.'))
    return view


def _line_color(rgb):
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def _editor_mask(container, name):
    modes = container.getEditorMode(name)
    mask = 0
    if "ReadOnly" in modes:
        mask |= 1
    if "Hidden" in modes:
        mask |= 2
    return mask
