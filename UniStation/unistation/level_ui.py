"""Integrate level names and the Delete guard with the FreeCAD workbench UI."""

from html import escape

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from unistation import attributes, levels, line_weights, palette
from unistation.attributes_gui import STYLE_LABELS
from unistation.i18n import tr
from unistation.mouse import _inside, _viewport


ELEMENT_LEVEL_NAME = "UstnLevelName"
# App::Prop_ReadOnly | App::Prop_Output | App::Prop_NoPersist
_NAME_PROPERTY_FLAGS = 1 | 8 | 32
_controller = None


def _level_name(level):
    return level.name if level is not None else tr('Missing level')


def _update_level_property(obj, by_id):
    name = _level_name(levels.level_for_element(obj, by_id))
    if ELEMENT_LEVEL_NAME not in obj.PropertiesList:
        obj.addProperty("App::PropertyString", ELEMENT_LEVEL_NAME, "UniStation",
                        tr('Name of the assigned UniStation level'), _NAME_PROPERTY_FLAGS)
        obj.setPropertyStatus(ELEMENT_LEVEL_NAME, "NoModify")
    if getattr(obj, ELEMENT_LEVEL_NAME) != name:
        setattr(obj, ELEMENT_LEVEL_NAME, name)
    if levels.ELEMENT_LEVEL in obj.PropertiesList and "Hidden" not in obj.getEditorMode(levels.ELEMENT_LEVEL):
        obj.setEditorMode(levels.ELEMENT_LEVEL, 3)


def _require_deletable(objects):
    """Check the whole selection and group contents before calling native Delete."""
    pending = list(objects)
    visited = set()
    by_document = {}
    while pending:
        obj = pending.pop()
        key = obj.Document.Name, obj.Name
        if key in visited:
            continue
        visited.add(key)
        if obj.hasExtension("App::GroupExtension", True):
            pending.extend(obj.Group)
        if levels.is_level_element(obj):
            by_document.setdefault(key[0], []).append(obj)
    for targets in by_document.values():
        levels.require_editable_elements(targets, _level_lookup(targets[0].Document))


def _level_lookup(document):
    return {level.identifier: level for level in levels.available_levels(document)}


def _hover_label(view):
    picked = view.getObjectInfo(view.getCursorPos())
    if not picked:
        return None
    document = App.listDocuments().get(picked["Document"])
    if document is None:
        return None
    obj = document.getObject(picked["Object"])
    if obj is None or not levels.is_level_element(obj):
        return None
    level = levels.level_for_element(obj, _level_lookup(document))
    lines = [tr('Level: {}').format(_level_name(level))]
    lines.extend(_attribute_labels(obj))
    if level is not None:
        if level.locked:
            lines.append(tr('Locked level'))
        if not level.plot:
            lines.append(tr('Plot disabled'))
    return "\n".join(lines)


def _attribute_labels(obj):
    view = obj.ViewObject
    if view is None:
        return []
    try:
        sources = attributes.element_level_sources(obj)
    except palette.PaletteError:
        sources = 0

    def label(value, source):
        return tr('{} ({})').format(value, tr('By level')) if sources & source else value

    lines = []
    if hasattr(view, "LineColor"):
        try:
            if palette._color_mode(obj) == palette.MODE_INDEX:
                value = tr('Index {}').format(palette._require_index(obj))
            else:
                value = tr('RGB {}, {}, {}').format(*palette.displayed_rgb(obj))
            lines.append(tr('Color: {}').format(label(value, attributes.COLOR_SOURCE)))
        except palette.PaletteError:
            pass
    style = getattr(view, "DrawStyle", None)
    if style:
        value = tr(STYLE_LABELS.get(style, style))
        lines.append(tr('Line style: {}').format(label(value, attributes.STYLE_SOURCE)))
    width = getattr(view, "LineWidth", None)
    if width is not None:
        value = tr('{:g} px').format(float(width))
        if line_weights.INDEX in obj.PropertiesList:
            try:
                index = line_weights.require_index(getattr(obj, line_weights.INDEX))
                value = tr('Index {0}: screen width {1:g} px').format(index, float(width))
            except palette.PaletteError:
                pass
        lines.append(tr('Line weight: {}').format(label(value, attributes.WEIGHT_SOURCE)))
    return lines


class DeleteGuard:
    def __init__(self):
        self.action, = Gui.Command.get("Std_Delete").getAction()
        self.receiver = self.action.parent()
        sender_meta, receiver_meta = self.action.metaObject(), self.receiver.metaObject()
        signal_index = sender_meta.indexOfSignal("triggered(bool)")
        slot_index = receiver_meta.indexOfSlot("onActivated()")
        if signal_index < 0 or slot_index < 0:
            raise RuntimeError("The FreeCAD Delete action is unavailable")
        self.signal = sender_meta.method(signal_index)
        self.slot = receiver_meta.method(slot_index)
        # Limit the interception to the native command receiver. Menus, shortcuts
        # and other observers keep the same shared QAction.
        if not QtCore.QObject.disconnect(self.action, self.signal, self.receiver, QtCore.QMetaMethod()):
            raise RuntimeError("Cannot intercept the FreeCAD Delete action")
        try:
            self.action.triggered.connect(self.trigger)
        except Exception:
            self.restore()
            raise

    def restore(self):
        if not QtCore.QObject.connect(self.action, self.signal, self.receiver, self.slot):
            raise RuntimeError("Cannot restore the FreeCAD Delete action")

    def close(self):
        self.action.triggered.disconnect(self.trigger)
        self.restore()

    def trigger(self, _checked=False):
        try:
            _require_deletable(item.Object for item in Gui.Selection.getSelectionEx() if item.Object is not None)
        except levels.LevelError as exc:
            Gui.getMainWindow().statusBar().showMessage(str(exc), 8000)
            App.Console.PrintWarning("UniStation: " + str(exc) + "\n")
            return
        self.slot.invoke(self.receiver, QtCore.Qt.DirectConnection)


class LevelDisplay(QtCore.QObject):
    def __init__(self):
        super().__init__(Gui.getMainWindow())
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update_selection)
        App.addDocumentObserver(self)
        Gui.Selection.addObserver(self)
        QtWidgets.QApplication.instance().installEventFilter(self)
        self.timer.start(0)

    def close(self):
        self.timer.stop()
        QtWidgets.QApplication.instance().removeEventFilter(self)
        Gui.Selection.removeObserver(self)
        App.removeDocumentObserver(self)
        self.deleteLater()

    def addSelection(self, _document, _object, _subelement, _point):
        self.timer.start(0)

    def setSelection(self, _document):
        self.timer.start(0)

    def slotActivateDocument(self, _document):
        self.timer.start(0)

    def slotUndoDocument(self, _document):
        self.timer.start(0)

    slotRedoDocument = slotUndoDocument

    def slotChangedObject(self, _obj, prop):
        if prop in (levels.DATA, levels.SCHEMA, levels.ELEMENT_LEVEL):
            self.timer.start(0)

    def update_selection(self):
        if App.ActiveDocument is None:
            return
        by_document = {}
        try:
            for item in Gui.Selection.getSelectionEx():
                obj = item.Object
                if obj is None or not levels.is_level_element(obj):
                    continue
                document = obj.Document
                if document.Name not in by_document:
                    by_document[document.Name] = _level_lookup(document)
                _update_level_property(obj, by_document[document.Name])
        except (levels.LevelError, ReferenceError):
            return

    def eventFilter(self, watched, event):
        if event.type() != QtCore.QEvent.ToolTip or not _inside(watched, _viewport()):
            return False
        try:
            gui_document = Gui.activeDocument()
            if gui_document is None:
                return False
            message = _hover_label(gui_document.activeView())
            if not message:
                return False
            html = "<br>".join(escape(line) for line in message.splitlines())
            QtWidgets.QToolTip.showText(event.globalPos(), "<qt>" + html + "</qt>", watched)
            return True
        except (AttributeError, levels.LevelError, KeyError, ReferenceError, RuntimeError):
            return False


def activate():
    global _controller
    if _controller is not None:
        return
    display = LevelDisplay()
    try:
        guard = DeleteGuard()
    except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
        App.Console.PrintError(tr('UniStation could not protect locked levels from Delete.') + " " + str(exc) + "\n")
        guard = None
    _controller = display, guard


def deactivate():
    global _controller
    if _controller is not None:
        display, guard = _controller
        _controller = None
        try:
            if guard is not None:
                guard.close()
        finally:
            display.close()
