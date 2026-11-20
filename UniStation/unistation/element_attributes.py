"""Resolve and apply an element attribute patch in one document transaction."""

from dataclasses import dataclass

from unistation import attributes, levels, line_weights, palette
from unistation.i18n import tr
from unistation.level_visibility import is_frozen, prepare_view_change, refresh_level_selection


KEEP_RGB = -2


@dataclass(frozen=True)
class AttributePatch:
    level: str | None = None
    color: int | None = None
    style: str | int | None = None
    weight: int | None = None


@dataclass(frozen=True)
class _Edit:
    obj: object
    level_id: str | None
    color: int | None
    style: str | None
    weight: int | None
    sources: int
    view_change: object | None


def _prepare_edit(obj, patch, by_id, destination, has_table, checked, requested_sources):
    original = levels.element_level_id(obj)
    original_id = original or levels.DEFAULT_ID
    target = destination if destination is not None else by_id.get(original_id)
    level_id = patch.level if has_table and patch.level != original else None
    if not has_table and destination is not None and original_id != levels.DEFAULT_ID:
        level_id = ""
    moved = level_id is not None and (level_id or levels.DEFAULT_ID) != original_id
    old_sources = attributes.element_level_sources(obj)
    sources = (old_sources & ~checked) | requested_sources
    inherit = sources & (attributes.ALL_SOURCES if moved else checked)
    if inherit and target is None:
        raise levels.LevelError(tr('The layer of {} is missing. Choose an existing layer.').format(obj.Label))
    color = target.color_index if inherit & attributes.COLOR_SOURCE else patch.color
    style = attributes.LINE_STYLES[target.line_style] if inherit & attributes.STYLE_SOURCE else patch.style
    weight = target.weight_index if inherit & attributes.WEIGHT_SOURCE else patch.weight

    if color is not None:
        palette._require_view(obj)
        mode = palette._color_mode(obj)
        color_properties = (palette.MODE_PROPERTY, palette.INDEX_PROPERTY, palette.EDITOR_MODE_PROPERTY)
        if any(name in obj.PropertiesList for name in color_properties):
            palette._require_color_properties(obj)
        if color == KEEP_RGB and mode != palette.MODE_INDEX:
            color = None
    if style is not None:
        attributes._require_line_style(obj.ViewObject, style)
    if weight is not None:
        line_weights.require_element_width(obj)
    view_change = (prepare_view_change(obj, target.available_for_drawing, target.global_freeze)
                   if level_id is not None else None)
    if all(value is None for value in (level_id, color, style, weight)) and sources == old_sources:
        return None
    return _Edit(obj, level_id, color, style, weight, sources, view_change)


def _property_snapshot(owner, names):
    return [(owner, name, (getattr(owner, name), palette._editor_mask(owner, name))
             if name in owner.PropertiesList else None) for name in names]


def _undo_disabled_snapshot(edits):
    snapshots = []
    for edit in edits:
        obj = edit.obj
        model_names = [attributes.ELEMENT_SOURCES]
        view_names = []
        if edit.level_id is not None:
            model_names.append(levels.ELEMENT_LEVEL)
        if edit.color is not None:
            model_names.extend((palette.MODE_PROPERTY, palette.INDEX_PROPERTY, palette.EDITOR_MODE_PROPERTY))
            view_names.append("LineColor")
        if edit.style is not None:
            view_names.append("DrawStyle")
        if edit.weight is not None:
            model_names.extend((line_weights.INDEX, line_weights.PREVIOUS_EDITOR_MODE))
            view_names.append("LineWidth")
        snapshots.extend(_property_snapshot(obj, model_names))
        if view_names:
            snapshots.extend(_property_snapshot(obj.ViewObject, view_names))
    return snapshots


def _restore_properties(snapshots):
    for owner, name, state in reversed(snapshots):
        if state is None:
            if name in owner.PropertiesList:
                owner.setPropertyStatus(name, "-LockDynamic")
                owner.removeProperty(name)
        else:
            value, mode = state
            if getattr(owner, name) != value:
                setattr(owner, name, value)
            owner.setEditorMode(name, mode)


def apply(document, objects, patch):
    """Apply only requested fields and resolve inherited values against the final layer."""
    options = ((attributes.COLOR_SOURCE, patch.color), (attributes.STYLE_SOURCE, patch.style),
               (attributes.WEIGHT_SOURCE, patch.weight))
    checked = sum(bit for bit, value in options if value is not None)
    if not checked and patch.level is None:
        return
    requested_sources = sum(bit for bit, value in options if attributes._is_by_level(value))
    keep_rgb = type(patch.color) is int and patch.color == KEEP_RGB
    if patch.color is not None and not keep_rgb and not requested_sources & attributes.COLOR_SOURCE:
        palette._require_index_value(patch.color)
    if patch.style is not None and not requested_sources & attributes.STYLE_SOURCE:
        attributes._style(patch.style)
    if patch.weight is not None and not requested_sources & attributes.WEIGHT_SOURCE:
        line_weights.require_index(patch.weight)

    palette.same_document(document)
    if document.HasPendingTransaction:
        raise palette.PaletteError(tr('Finish the current task first.'))
    targets = list(objects)
    if not targets:
        raise palette.PaletteError(tr('Select one or more whole objects.'))
    for obj in targets:
        if obj.Document is not document or document.getObject(obj.Name) is not obj:
            raise levels.LevelError(tr('The selected objects or document changed'))
        if is_frozen(obj):
            raise levels.LevelUnavailableError(
                tr('The level of {} is frozen. Thaw the level to select its elements.').format(obj.Label))

    _table, records = levels.read_table(document)
    by_id = {level.identifier: level for level in records or (levels.DEFAULT_LEVEL,)}
    levels.require_editable_elements(targets, by_id)
    destination = by_id.get(patch.level)
    if patch.level is not None:
        if destination is None:
            raise levels.LevelError(tr('The selected level is no longer available.'))
        levels.require_unlocked_level(destination)
    edits = [edit for obj in targets if (edit := _prepare_edit(
        obj, patch, by_id, destination, records is not None, checked, requested_sources)) is not None]
    if not edits:
        return

    use_palette = any(edit.color is not None and edit.color != KEEP_RGB for edit in edits)
    color_table, colors = palette.colors_for_display(document) if use_palette else (None, None)
    use_weights = any(edit.weight is not None for edit in edits)
    if use_weights:
        line_weights.widths_for_display(document)
    view_changes = [edit.view_change for edit in edits if edit.view_change is not None]
    original_names = snapshots = None
    if not document.UndoMode:
        original_names = {obj.Name for obj in document.Objects}
        snapshots = _undo_disabled_snapshot(edits)

    document.openTransaction(tr('UniStation Change Attributes'))
    try:
        if use_palette and color_table is None:
            palette._create_palette(document, colors)
        if use_weights:
            _table, widths = line_weights.ensure_table_in_transaction(document)
        for edit in edits:
            obj = edit.obj
            if edit.level_id is not None:
                levels.set_element_level(obj, edit.level_id)
            if edit.color == KEEP_RGB:
                palette._set_direct(obj)
            elif edit.color is not None:
                palette._set_index(obj, edit.color, colors[edit.color])
            if edit.style is not None:
                obj.ViewObject.DrawStyle = edit.style
            if edit.weight is not None:
                line_weights.set_element_index(obj, edit.weight, widths)
            attributes.set_element_level_sources(obj, edit.sources)
        for change in view_changes:
            change.apply()
        document.commitTransaction()
    except Exception:
        document.abortTransaction()
        if snapshots is not None:
            for change in reversed(view_changes):
                change.restore()
            _restore_properties(snapshots)
            for obj in reversed(document.Objects):
                if obj.Name not in original_names:
                    document.removeObject(obj.Name)
        raise
    if view_changes:
        refresh_level_selection(document, (change.obj for change in view_changes))
