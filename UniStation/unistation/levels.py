"""Document-owned level definitions, independent of the geometry and GUI."""

from dataclasses import asdict, dataclass, fields
import json
from uuid import uuid4

from unistation.attributes import (
    COLOR_SOURCE, LINE_STYLES, STYLE_SOURCE, WEIGHT_SOURCE,
    element_level_sources, level_appearance_changes,
)
from unistation.i18n import tr
from unistation.level_visibility import prepare_view_change, refresh_level_selection
from unistation.line_weights import COUNT as WEIGHT_COUNT
from unistation.palette import COLOR_COUNT, same_document


DEFAULT_ID = "default"
TABLE_NAME = "UstnLevelTable"
SCHEMA = "UstnLevelSchema"
DATA = "UstnLevelData"
ELEMENT_LEVEL = "UstnLevelId"
VERSION = 1
TABLE_PROPERTIES = {SCHEMA: "App::PropertyInteger", DATA: "App::PropertyString"}


class LevelError(ValueError):
    pass


class LevelUnavailableError(LevelError):
    pass


class LevelLockedError(LevelUnavailableError):
    pass


@dataclass(frozen=True)
class Level:
    identifier: str
    name: str
    description: str = ""
    color_index: int = 0
    line_style: int = 0
    weight_index: int = 0
    global_display: bool = True
    global_freeze: bool = False
    locked: bool = False
    plot: bool = True

    @property
    def available_for_drawing(self):
        return self.global_display and not self.global_freeze


DEFAULT_LEVEL = Level(DEFAULT_ID, "Default")


def new_level(names):
    used = {name.strip().casefold() for name in names}
    number = 1
    while True:
        name = tr('Level {}').format(number)
        if name.casefold() not in used:
            return Level(uuid4().hex, name)
        number += 1


def validate_name(name, used):
    if not isinstance(name, str) or not name.strip():
        raise LevelError(tr('Each level must have a name.'))
    name = name.strip()
    if name.casefold() in used:
        raise LevelError(tr('Level names must be unique: {}').format(name))
    return name


def _validate(levels):
    identifiers = set()
    names = set()
    for level in levels:
        identifier = level.identifier
        if not isinstance(identifier, str) or not identifier or identifier in identifiers:
            raise LevelError(tr('The level table contains an invalid or duplicate identifier.'))
        identifiers.add(identifier)
        names.add(validate_name(level.name, names).casefold())
        if not isinstance(level.description, str):
            raise LevelError(tr('The level table contains an invalid description.'))
        for value, limit in ((level.color_index, COLOR_COUNT),
                             (level.line_style, len(LINE_STYLES)),
                             (level.weight_index, WEIGHT_COUNT)):
            if type(value) is not int or not 0 <= value < limit:
                raise LevelError(tr('A level has an invalid color, line style, or line weight index.'))
        if not all(type(flag) is bool for flag in
                   (level.global_display, level.global_freeze, level.locked, level.plot)):
            raise LevelError(tr('The level table contains an invalid flag.'))
    if DEFAULT_ID not in identifiers:
        raise LevelError(tr('The level table must contain one default level.'))


def read_table(document):
    """Return (table object, records), or (None, None) for a document without a table."""
    candidates = [obj for obj in document.Objects
                  if set(TABLE_PROPERTIES).intersection(obj.PropertiesList)]
    if not candidates:
        return None, None
    if len(candidates) != 1:
        raise LevelError(tr('The document contains more than one UniStation level table.'))
    table = candidates[0]
    if (table.TypeId != "App::DocumentObject"
            or any(name not in table.PropertiesList or table.getTypeIdOfProperty(name) != kind
                   for name, kind in TABLE_PROPERTIES.items())):
        raise LevelError(tr('The UniStation level table is damaged.'))
    if getattr(table, SCHEMA) != VERSION:
        raise LevelError(tr('This UniStation level table version is not supported.'))
    try:
        records = json.loads(getattr(table, DATA))
        if not isinstance(records, list):
            raise TypeError("Expected a list of levels")
        keys = {field.name for field in fields(Level)}
        if not all(isinstance(record, dict) and record.keys() == keys for record in records):
            raise TypeError("Unexpected level fields")
        levels = tuple(Level(**record) for record in records)
    except (ValueError, TypeError) as exc:
        raise LevelError(tr('The UniStation level table is damaged.')) from exc
    _validate(levels)
    return table, levels


def available_levels(document):
    return read_table(document)[1] or (DEFAULT_LEVEL,)


def element_level_id(obj):
    """Read the saved assignment. Empty or absent values imply Default."""
    if ELEMENT_LEVEL not in obj.PropertiesList:
        return None
    if obj.getTypeIdOfProperty(ELEMENT_LEVEL) != "App::PropertyString":
        raise LevelError(tr('The level assignment of {} is damaged.').format(obj.Label))
    return getattr(obj, ELEMENT_LEVEL)


def level_for_element(obj, by_id):
    return by_id.get(element_level_id(obj) or DEFAULT_ID)


def is_level_element(obj):
    """Recognize the geometry and explicit assignments managed by the level table."""
    return obj.isDerivedFrom("Part::Feature") or bool(element_level_id(obj))


def require_editable_elements(objects, by_id):
    if not any(level.locked for level in by_id.values()):
        return
    for obj in objects:
        level = level_for_element(obj, by_id)
        if level is not None and level.locked:
            raise LevelLockedError(tr('Object “{}” is on locked level “{}”. Unlock the level to edit it.')
                                   .format(obj.Label, level.name))


def require_unlocked_level(level):
    if level.locked:
        raise LevelLockedError(tr('Level “{}” is locked. Unlock it or choose an unlocked level.')
                               .format(level.name))


def set_element_level(obj, identifier):
    """Write an assignment as part of the caller's document transaction."""
    old = element_level_id(obj)
    if old == identifier:
        return
    if old is None:
        obj.addProperty("App::PropertyString", ELEMENT_LEVEL, "UniStation",
                        tr('Identifier of the assigned UniStation level'), read_only=True, hidden=True)
    setattr(obj, ELEMENT_LEVEL, identifier)


def used_level_ids(document):
    return {identifier for obj in document.Objects if (identifier := element_level_id(obj))}


def assign_elements(document, baseline, objects, identifier):
    """Commit all requested assignments together after validating their targets."""
    same_document(document)
    table, records = read_table(document)
    if table is not baseline[0] or records != baseline[1]:
        raise LevelError(tr('The level table changed. Reopen the assignment dialog.'))
    by_id = {level.identifier: level for level in (records or ())}
    target = by_id.get(identifier)
    if target is None:
        raise LevelError(tr('The selected level is no longer available.'))
    if document.HasPendingTransaction:
        raise LevelError(tr('Finish the current task first.'))
    changes = []
    for obj in objects:
        if obj.Document is not document or document.getObject(obj.Name) is not obj:
            raise LevelError(tr('The selected objects or document changed'))
        saved = element_level_id(obj)
        if saved != identifier:
            changes.append((obj, saved))
    if not changes:
        return
    require_editable_elements((obj for obj, _saved in changes), by_id)
    require_unlocked_level(target)
    inherited = []
    for obj, saved in changes:
        sources = element_level_sources(obj)
        if sources and (saved or DEFAULT_ID) != identifier:
            inherited.append((obj, target, sources))
    appearance = level_appearance_changes(document, inherited)
    view_changes = [change for obj, _saved in changes
                    if (change := prepare_view_change(obj, target.available_for_drawing,
                                                     target.global_freeze)) is not None]

    undo_enabled = bool(document.UndoMode)
    document.openTransaction(tr('UniStation: assign level'))
    try:
        for obj, _saved in changes:
            set_element_level(obj, identifier)
        for change in appearance:
            change.apply()
        for change in view_changes:
            change.apply()
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        if not undo_enabled:
            for change in reversed(view_changes):
                change.restore()
            for change in reversed(appearance):
                change.restore()
            for obj, saved in reversed(changes):
                if saved is None:
                    if ELEMENT_LEVEL in obj.PropertiesList:
                        obj.removeProperty(ELEMENT_LEVEL)
                elif element_level_id(obj) != saved:
                    set_element_level(obj, saved)
        raise
    if view_changes:
        refresh_level_selection(document, (change.obj for change in view_changes))


def _edited_level_appearance(document, previous, records):
    old = {level.identifier: level for level in (previous or (DEFAULT_LEVEL,))}
    edits = {}
    for level in records:
        prior = old.get(level.identifier)
        if prior is None:
            continue
        mask = ((COLOR_SOURCE if prior.color_index != level.color_index else 0)
                | (STYLE_SOURCE if prior.line_style != level.line_style else 0)
                | (WEIGHT_SOURCE if prior.weight_index != level.weight_index else 0))
        if mask:
            edits[level.identifier] = level, mask
    if not edits:
        return []

    inherited = []
    for obj in document.Objects:
        sources = element_level_sources(obj)
        if not sources:
            continue
        edit = edits.get(element_level_id(obj) or DEFAULT_ID)
        if edit is not None:
            level, changed = edit
            if sources & changed:
                inherited.append((obj, level, sources & changed))
    return level_appearance_changes(document, inherited)


def _edited_level_visibility(document, previous, records):
    old = {level.identifier: (level.available_for_drawing, level.global_freeze)
           for level in (previous or (DEFAULT_LEVEL,))}
    edits = {}
    for level in records:
        flags = level.available_for_drawing, level.global_freeze
        if old.get(level.identifier, (True, False)) != flags:
            edits[level.identifier] = flags
    if not edits:
        return []

    changes = []
    for obj in document.Objects:
        if not is_level_element(obj):
            continue
        flags = edits.get(element_level_id(obj) or DEFAULT_ID)
        if flags is not None:
            change = prepare_view_change(obj, *flags)
            if change is not None:
                changes.append(change)
    return changes


def save_table(document, baseline, levels):
    """Validate and replace the table in one undoable operation."""
    _validate(levels)
    same_document(document)
    table, previous = read_table(document)
    if table is not baseline[0] or previous != baseline[1]:
        raise LevelError(tr('The level table changed. Reopen the Level Manager to continue.'))
    if previous == levels:
        return
    remaining_ids = {level.identifier for level in levels}
    removed = [level for level in (previous or ()) if level.identifier not in remaining_ids]
    if removed:
        used = used_level_ids(document)
        for level in removed:
            if level.identifier in used:
                raise LevelError(tr('Cannot remove a level assigned to elements: {}').format(level.name))
    if document.HasPendingTransaction:
        raise LevelError(tr('Finish the current task first.'))
    appearance = _edited_level_appearance(document, previous, levels)
    view_changes = _edited_level_visibility(document, previous, levels)
    data = json.dumps([asdict(level) for level in levels], separators=(",", ":"))
    undo_enabled = bool(document.UndoMode)
    original_data = getattr(table, DATA) if table is not None else None

    document.openTransaction(tr('UniStation: edit levels'))
    try:
        if table is None:
            table = document.addObject("App::DocumentObject", TABLE_NAME)
            table.Label = tr('UniStation level table')
            for name, kind in TABLE_PROPERTIES.items():
                table.addProperty(kind, name, "UniStation", locked=True)
                table.setEditorMode(name, 1)
            setattr(table, SCHEMA, VERSION)
        setattr(table, DATA, data)
        for change in appearance:
            change.apply()
        for change in view_changes:
            change.apply()
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        # FreeCAD cannot roll back transactions with Undo disabled.
        if not undo_enabled and table is not None:
            for change in reversed(view_changes):
                change.restore()
            for change in reversed(appearance):
                change.restore()
            if previous is None:
                document.removeObject(table.Name)
            elif getattr(table, DATA) != original_data:
                setattr(table, DATA, original_data)
        raise
    if view_changes:
        refresh_level_selection(document, (change.obj for change in view_changes))
