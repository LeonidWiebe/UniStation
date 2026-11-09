"""Conservative whole-object selection and atomic Draft transforms."""

from unistation.i18n import tr
import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore
from unistation.gui import Backend


def whole_object_error(obj):
    """Return the Move/Copy rejection text, or None when the whole object is usable."""
    from draftutils.utils import get_type
    if obj.Document is not App.ActiveDocument:
        return tr('Select objects from the active document only')
    if (not hasattr(obj, "Shape") or not hasattr(obj, "Placement")
            or (get_type(obj) not in ("Wire", "Circle") and obj.TypeId != "Part::Feature")):
        return tr('Supported: independent Draft wires/circles/arcs and simple Part features')
    if (obj.InList or obj.OutList or getattr(obj, "ExpressionEngine", [])
            or str(getattr(obj, "MapMode", "Deactivated")) != "Deactivated"):
        return tr('Attached, nested or dependent objects are not supported yet: ') + obj.Label
    if obj.Shape.isNull() or not obj.Shape.isValid():
        return tr('Invalid shape: ') + obj.Label
    return None


def selected_objects():
    selection = Gui.Selection.getSelectionEx()
    if not selection:
        raise RuntimeError(tr('Select whole objects before starting Move or Copy'))
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
        if not self.alive():
            raise RuntimeError(tr('The selected objects or document changed'))
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
            self.doc.commitTransaction()
        except Exception:
            self.doc.abortTransaction()
            raise
        from unistation.operation_selection import finish
        finish(self.doc, result)
