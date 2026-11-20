"""Conservative whole-object selection and atomic Draft transforms."""

from unistation.i18n import tr
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
from unistation.gui import Backend
from unistation.level_visibility import copy_view_state, is_frozen, prepare_view_change


def _frozen_level_error(obj):
    return tr('The level of {} is frozen. Thaw the level to select its elements.').format(obj.Label)


def whole_object_error(obj):
    """Return the Move/Copy rejection text, or None when the whole object is usable."""
    from draftutils.utils import get_type
    if obj.Document is not App.ActiveDocument:
        return tr('Select objects from the active document only')
    if is_frozen(obj):
        return _frozen_level_error(obj)
    if (not hasattr(obj, "Shape") or not hasattr(obj, "Placement")
            or (get_type(obj) not in ("Wire", "Circle") and obj.TypeId != "Part::Feature")):
        return tr('Supported: independent Draft wires/circles/arcs and simple Part features')
    if (obj.InList or obj.OutList or getattr(obj, "ExpressionEngine", [])
            or str(getattr(obj, "MapMode", "Deactivated")) != "Deactivated"):
        return tr('Attached, nested or dependent objects are not supported yet: ') + obj.Label
    if obj.Shape.isNull() or not obj.Shape.isValid():
        return tr('Invalid shape: ') + obj.Label
    return None


def selected_objects(empty_message=None):
    selection = Gui.Selection.getSelectionEx()
    if not selection:
        raise RuntimeError(empty_message or tr('Select whole objects before starting Move or Copy'))
    objects = []
    for item in selection:
        if item.SubElementNames:
            raise RuntimeError(tr('Select whole objects, not edges or vertices'))
        reason = whole_object_error(item.Object)
        if reason:
            raise RuntimeError(reason)
        if item.Object not in objects:
            objects.append(item.Object)
    return objects


def transform_levels(document, objects, copy):
    """Check a Move, or return a new destination for each locked Copy source."""
    from unistation.attributes import placement_level_id
    from unistation.levels import available_levels, level_for_element, require_editable_elements

    by_id = {level.identifier: level for level in available_levels(document)}
    if not copy:
        require_editable_elements(objects, by_id)
        return ()
    if not any(level.locked for level in by_id.values()):
        return (None,) * len(objects)
    sources = [level_for_element(obj, by_id) for obj in objects]
    locked = [level is not None and level.locked for level in sources]
    destination = by_id[placement_level_id(document)] if any(locked) else None
    return tuple(destination if redirect else None for redirect in locked)


class TransformBackend(Backend):
    def __init__(self, axisflow, objects):
        self.objects = objects
        self.snapshot = [(o.Name, o, App.Placement(o.Placement), o.Shape) for o in objects]
        super().__init__(axisflow)
        try:
            from pivy import coin
            self.ghost = coin.SoSwitch()
            self.translation = coin.SoTranslation()
            self.ghost.addChild(self.translation)
            pick = coin.SoPickStyle()
            pick.style = coin.SoPickStyle.UNPICKABLE
            self.ghost.addChild(pick)
            for obj in objects:
                # Plain shape nodes carry no ViewProvider/selection pointers into
                # the source object, which may be deleted while input is active.
                source = coin.SoInput()
                source.setBuffer(obj.Shape.writeInventor())
                shape_node = coin.SoDB.readAll(source)
                if shape_node is None:
                    raise RuntimeError(tr('Cannot build transform preview'))
                self.ghost.addChild(shape_node)
            self.node.addChild(self.ghost)
            self.hide_ghost()
        except Exception:
            self.close()
            raise

    def slotDeletedObject(self, view_provider):
        if view_provider.Object in self.objects:
            from unistation.gui import cancel
            cancel()

    def alive(self):
        if not super().alive():
            return False
        try:
            return all(self.doc.getObject(name) is obj and obj.Placement == placement
                       and obj.Shape.isEqual(shape) and not obj.InList and not obj.OutList
                       and not getattr(obj, "ExpressionEngine", [])
                       and str(getattr(obj, "MapMode", "Deactivated")) == "Deactivated"
                       for name, obj, placement, shape in self.snapshot)
        except (RuntimeError, AttributeError):
            return False

    def preview_transform(self, delta):
        from pivy import coin
        self.translation.translation.setValue(delta.x, delta.y, delta.z)
        self.ghost.whichChild = coin.SO_SWITCH_ALL

    def hide_ghost(self):
        from pivy import coin
        self.ghost.whichChild = coin.SO_SWITCH_NONE

    def reset_input(self):
        self.hide_ghost()
        super().reset_input()

    def defer(self, callback):
        QtCore.QTimer.singleShot(0, callback)

    def transform(self, delta, copy):
        import Draft
        from unistation.attributes import (
            element_level_sources, level_appearance_changes, set_element_level_sources,
        )
        from unistation.levels import element_level_id, set_element_level
        if not self.alive():
            raise RuntimeError(tr('The selected objects or document changed'))
        for obj in self.objects:
            if is_frozen(obj):
                raise RuntimeError(_frozen_level_error(obj))
        destinations = transform_levels(self.doc, self.objects, copy)
        bindings = [(element_level_id(obj), element_level_sources(obj)) for obj in self.objects] if copy else ()
        # Abort does not remove new objects when FreeCAD Undo is disabled.
        existing = {obj.Name for obj in self.doc.Objects} if copy and not self.doc.UndoMode else None
        self.doc.openTransaction(tr('UniStation Copy') if copy else tr('UniStation Move'))
        try:
            result = Draft.move(self.objects, delta, copy=copy)
            result = result if isinstance(result, list) else [result]
            if len(result) != len(self.objects) or any(obj is None for obj in result):
                raise RuntimeError(tr('Draft.move did not transform every selected object'))
            self.doc.recompute()
            for obj in result:
                if obj.Shape.isNull() or not obj.Shape.isValid():
                    raise RuntimeError(tr('Draft.move produced invalid geometry'))
            inherited = []
            for obj, source, (identifier, sources), destination in zip(
                    result, self.objects, bindings, destinations):
                if destination is not None:
                    identifier = destination.identifier
                if identifier:
                    set_element_level(obj, identifier)
                set_element_level_sources(obj, sources)
                copy_view_state(source, obj)
                if destination is not None:
                    view_change = prepare_view_change(obj, available=True, frozen=False)
                    if view_change is not None:
                        view_change.apply()
                    if sources:
                        inherited.append((obj, destination, sources))
            for change in level_appearance_changes(self.doc, inherited):
                change.apply()
            self.doc.commitTransaction()
        except Exception:
            self.doc.abortTransaction()
            if existing is not None:
                for obj in reversed(self.doc.Objects):
                    if obj.Name not in existing:
                        self.doc.removeObject(obj.Name)
            raise
        from unistation.operation_selection import finish
        finish(self.doc, result)
