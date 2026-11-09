"""Temporary whole-object locate for one UniStation command step.

The controller owns one 3D view and one document. It does not change the
navigation style, AxisFlow, or point-entry commands. Callers supply a
predicate and a continuation. The continuation runs only after the mouse
gesture has finished and this controller has removed its callbacks.
"""

from unistation.i18n import (tr, translated_button)
from unistation.input_events import ResettableCommand

import math

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

_current = None


class LocateError(Exception):
    """The locate step could not start. The document is unchanged."""


def is_active():
    return _current is not None and not _current.closed


def active_session():
    return _current if is_active() else None


def cancel():
    if _current is not None:
        _current.stop()


def begin(document, predicate, continuation):
    """Start locate. ``predicate`` returns an error string or None.

    ``continuation`` receives a list with the accepted object and is called
    after locate has stopped, from the Qt event loop, not from a Coin callback.
    """
    if is_active():
        raise LocateError(tr('Element locate is already active.'))
    session = _Session(document, predicate, continuation)
    session.start()
    return session


class _Panel:
    def __init__(self, session):
        self.session = session
        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.form)
        reset_button = translated_button('Reset')
        reset_button.setObjectName("unistation_locate_reset")
        reset_button.setAutoDefault(False)

        def send_reset():
            from unistation.gui import reset
            reset(expected=self.session, source="task")

        reset_button.clicked.connect(send_reset)
        layout.addWidget(reset_button)

    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Close

    def reject(self):
        self.session.stop()
        return True

    def isAllowedAlterDocument(self):
        return False

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterSelection(self):
        return True


class _ViewFilter(QtCore.QObject):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.Leave:
            self.session.hide_marker()
        elif kind == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
            QtCore.QTimer.singleShot(0, self.session.try_accept)
        return False


class _Observer:
    def __init__(self, session):
        self.session = session

    def slotDeletedDocument(self, document):
        if document.Document is self.session.document:
            self.session.request_stop()

    def slotActivateDocument(self, document):
        if document.Document is not self.session.document:
            self.session.request_stop()

    def slotDeletedObject(self, view_provider):
        self.session.invalidate()


class _Session(ResettableCommand):
    def __init__(self, document, predicate, continuation):
        self.document = document
        self.doc_name = document.Name
        self.predicate = predicate
        self.continuation = continuation
        self.view = None
        self.viewer = None
        self.widget = None
        self.old_cursor = None
        self.popup_enabled = None
        self.navigation_name = None
        self.workbench_name = None
        self.graph = None
        self.graph_held = False
        self.marker = None
        self.switch = None
        self.camera = None
        self.translation = None
        self.circle_coords = None
        self.circle_lines = None
        self.cross_coords = None
        self.drawn_radius = None
        self.drawn_size = None
        self.callback = None
        self.callback_fn = None
        self.filter = None
        self.observer = None
        self.panel = None
        self.panel_shown = False
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._guard)
        self.selection_snapshot = []
        self.keys = []
        self.index = 0
        self.last_pos = None
        self.armed = False
        self.accepted = False
        self.closing = False
        self.closed = False
        self._stop_posted = False

    def start(self):
        global _current
        view = _active_view()
        if view is None:
            raise LocateError(tr('No 3D view is available for element locate.'))
        navigation = _navigation_name(view)
        if not _is_cad_navigation(navigation):
            raise LocateError(
                tr('Element locate requires CAD navigation. The current style is “') + navigation + tr('”. The navigation style was not changed.')
            )
        self.view = view
        self.viewer = view.getViewer()
        self.navigation_name = navigation
        self.workbench_name = _workbench_name()
        self.selection_snapshot = _selection_snapshot(self.document)
        _current = self
        try:
            self._build_marker()
            self._install_cursor()
            self._disable_popup()
            self.observer = _Observer(self)
            Gui.addDocumentObserver(self.observer)
            self.callback_fn = self._on_event
            self.callback = self.view.addEventCallback("SoEvent", self.callback_fn)
            self._install_filter()
            self.panel = _Panel(self)
            Gui.Control.showDialog(self.panel)
            self.panel_shown = True
            self.timer.start()
            self._set_status(tr('Point to an object.'))
        except Exception:
            self.stop()
            raise

    def request_stop(self):
        if self.closed or self._stop_posted:
            return
        self.closing = True
        self._stop_posted = True
        QtCore.QTimer.singleShot(0, self.stop)

    def cancel(self):
        self.stop()

    def reset_step(self):
        if not self._alive() or not self._same_context():
            self.stop()
            return
        self.armed = False
        self.last_pos = None
        self.invalidate()
        self.hide_marker()
        Gui.Selection.clearPreselection()
        self._set_status(tr('Reset: point to an object, or Reset again to exit.'))

    def stop(self):
        global _current
        if self.closed:
            return
        self.closed = True
        self.closing = True
        self.timer.stop()
        self._remove_callback()
        self._remove_filter()
        self._remove_marker()
        self._restore_cursor()
        self._restore_popup()
        self._remove_observer()
        try:
            Gui.Selection.clearPreselection()
        except Exception:
            pass
        if not self.accepted:
            _restore_selection(self.document, self.doc_name, self.selection_snapshot)
        if _current is self:
            _current = None
        if self.panel_shown:
            self.panel_shown = False
            Gui.Control.closeDialog()

    def invalidate(self):
        self.keys = []
        self.index = 0

    def hide_marker(self):
        if self.switch is not None:
            self.switch.whichChild = -1
        if self.widget is not None and self.old_cursor is not None and not self.closed:
            try:
                self.widget.setCursor(self.old_cursor)
            except Exception:
                pass

    def try_accept(self):
        if self.closed or self.closing or not self.armed:
            return
        try:
            self._accept_if_released()
        except Exception as exc:
            App.Console.PrintError("UniStation Locate: " + str(exc) + "\n")
            self.stop()

    def _accept_if_released(self):
        if QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton:
            return
        self.armed = False
        if not self._alive():
            self.stop()
            return
        keys = self._replace_keys(self.last_pos, keep_current=True)
        if not keys:
            self._highlight([])
            return
        obj = self._object(keys[self.index])
        if obj is None or self.predicate(obj):
            self._highlight(self._replace_keys(self.last_pos, keep_current=False))
            return
        continuation = self.continuation
        self.continuation = None
        self.accepted_input()
        self.accepted = True
        self.stop()
        if continuation is None:
            return
        if App.listDocuments().get(self.doc_name) is not self.document:
            return
        try:
            Gui.Selection.clearSelection(self.doc_name)
            if self.document.getObject(obj.Name) is obj:
                Gui.Selection.addSelection(obj)
        except Exception:
            pass
        continuation([obj])

    def _on_event(self, arg):
        if self.closed or self.closing:
            return
        try:
            self._handle(arg)
        except Exception as exc:
            App.Console.PrintError("UniStation Locate: " + str(exc) + "\n")
            self.request_stop()

    def _handle(self, arg):
        if not self._alive():
            self.request_stop()
            return
        position = arg.get("Position")
        if position is not None:
            self.last_pos = (int(position[0]), int(position[1]))
            self._place_marker(self.last_pos)
        kind = arg.get("Type")
        if kind == "SoLocation2Event":
            self._highlight(self._replace_keys(self.last_pos, keep_current=True))
            return
        if kind == "SoKeyboardEvent" and arg.get("Key") == "ESCAPE" and arg.get("State") == "DOWN":
            self.request_stop()
            return
        if kind != "SoMouseButtonEvent":
            return
        if arg.get("ShiftDown") or arg.get("CtrlDown") or arg.get("AltDown"):
            return
        button = arg.get("Button")
        down = arg.get("State") == "DOWN"
        pressed = QtWidgets.QApplication.mouseButtons()
        if button == "BUTTON2" and down:
            if pressed & QtCore.Qt.LeftButton:
                return
            self._cycle()
            return
        if button != "BUTTON1":
            return
        if down:
            if pressed & (QtCore.Qt.RightButton | QtCore.Qt.MiddleButton):
                return
            self.armed = True
            self._highlight(self._replace_keys(self.last_pos, keep_current=True))
            return
        if self.armed:
            QtCore.QTimer.singleShot(0, self.try_accept)

    def _guard(self):
        if self.closed:
            return
        try:
            if not self._alive() or not self._same_context():
                self.stop()
                return
            self._sync_marker_shape()
            if self.last_pos is not None:
                self._highlight(self._replace_keys(self.last_pos, keep_current=True))
            if self.armed and not (QtWidgets.QApplication.mouseButtons() & QtCore.Qt.LeftButton):
                self.try_accept()
        except Exception as exc:
            App.Console.PrintError("UniStation Locate: " + str(exc) + "\n")
            self.stop()

    def _cycle(self):
        keys = self._collect(self.last_pos)
        if not keys:
            self._highlight([])
            return
        current = self.keys[self.index] if self.keys and self.index < len(self.keys) else None
        self.keys = keys
        if current in keys:
            self.index = (keys.index(current) + 1) % len(keys)
        else:
            self.index = 0
        self._highlight(keys)

    def _replace_keys(self, pos, keep_current):
        keys = self._collect(pos)
        current = self.keys[self.index] if self.keys and self.index < len(self.keys) else None
        self.keys = keys
        if keys and keep_current and current in keys:
            self.index = keys.index(current)
        else:
            self.index = 0
        return keys

    def _collect(self, pos):
        if pos is None or self.closed:
            return []
        try:
            found = self.view.getObjectsInfo(pos, self._radius())
        except TypeError:
            found = self.view.getObjectsInfo(pos)
        except Exception:
            return []
        if not found:
            return []
        if isinstance(found, dict):
            found = [found]
        keys = []
        seen = set()
        for item in found:
            key = _whole_key(item, self.doc_name)
            if key is None or key in seen:
                continue
            obj = self.document.getObject(key[1])
            if obj is None or not _pickable(obj) or self.predicate(obj):
                continue
            seen.add(key)
            keys.append(key)
        return keys

    def _highlight(self, keys):
        self.keys = keys
        if not keys:
            self.index = 0
            _clear_preselection()
            self._set_status(tr('Locate an element. The ring shows the pick radius.'))
            return
        if self.index >= len(keys):
            self.index = 0
        obj = self._object(keys[self.index])
        if obj is None:
            _clear_preselection()
            self._set_status(tr('Locate an element. The ring shows the pick radius.'))
            return
        try:
            Gui.Selection.setPreselection(obj, "")
        except Exception:
            pass
        from unistation import preferences
        if preferences.right_button_action() == preferences.RESET:
            text = tr('Object “{0}”, {1} of {2}. Right-click: Reset; left-click: accept.')
        else:
            text = tr('Object “{0}”, {1} of {2}. Right-click: next; left-click: accept.')
        self._set_status(text.format(obj.Label, self.index + 1, len(keys)))

    def _object(self, key):
        if key[0] != self.doc_name:
            return None
        obj = self.document.getObject(key[1])
        if obj is None or obj.Document is not self.document:
            return None
        return obj

    def _set_status(self, text):
        try:
            Gui.getMainWindow().showMessage(text, 0)
        except Exception:
            pass

    def _alive(self):
        try:
            if App.listDocuments().get(self.doc_name) is not self.document:
                return False
            if App.ActiveDocument is not self.document:
                return False
            gui_doc = Gui.getDocument(self.doc_name)
            return gui_doc is not None and gui_doc.activeView() == self.view
        except Exception:
            return False

    def _same_context(self):
        try:
            return (_navigation_name(self.view) == self.navigation_name
                    and _workbench_name() == self.workbench_name)
        except Exception:
            return False

    def _radius(self):
        try:
            radius = float(self.viewer.getPickRadius())
        except Exception:
            radius = 5.0
        if radius < 0.5:
            return 0.5
        return radius

    def _build_marker(self):
        from pivy import coin
        group = coin.SoType.fromName("SoSkipBoundingGroup").createInstance()
        if group is None:
            raise LocateError(tr('Could not create the locate cursor.'))
        try:
            group.mode.setValue(1)
        except Exception as exc:
            raise LocateError(tr('Could not create the locate cursor.')) from exc
        switch = coin.SoSwitch()
        switch.whichChild = -1
        root = coin.SoAnnotation()
        pick = coin.SoPickStyle()
        pick.style = coin.SoPickStyle.UNPICKABLE
        camera = coin.SoOrthographicCamera()
        camera.viewportMapping = coin.SoCamera.LEAVE_ALONE
        light = coin.SoLightModel()
        light.model = coin.SoLightModel.BASE_COLOR
        translation = coin.SoTranslation()
        style = coin.SoDrawStyle()
        style.lineWidth = 1
        color = coin.SoBaseColor()
        color.rgb = (1.0, 0.85, 0.0)
        circle_coords = coin.SoCoordinate3()
        circle_lines = coin.SoLineSet()
        cross_coords = coin.SoCoordinate3()
        cross_lines = coin.SoLineSet()
        for node in (pick, camera, light, translation, style, color,
                     circle_coords, circle_lines, cross_coords, cross_lines):
            root.addChild(node)
        switch.addChild(root)
        group.addChild(switch)
        self.graph = self.view.getSceneGraph()
        self.graph.ref()
        self.graph_held = True
        self.graph.addChild(group)
        self.marker = group
        self.switch = switch
        self.camera = camera
        self.translation = translation
        self.circle_coords = circle_coords
        self.circle_lines = circle_lines
        self.cross_coords = cross_coords
        self.cross_lines = cross_lines
        self._sync_marker_shape()

    def _sync_marker_shape(self):
        if self.camera is None:
            return
        width, height = _viewport_size(self.viewer)
        if width < 1 or height < 1:
            return
        size = (width, height)
        radius = self._radius()
        if size != self.drawn_size:
            self.camera.aspectRatio = width / float(height)
            self.camera.height = height
            self.camera.position.setValue(width / 2.0, height / 2.0, 10.0)
            self.camera.nearDistance = 1
            self.camera.farDistance = 20
            self.camera.focalDistance = 10
            self.drawn_size = size
        if radius != self.drawn_radius:
            self._write_crosshair(radius)
            self.drawn_radius = radius

    def _write_crosshair(self, radius):
        steps = 64
        points = []
        for step in range(steps + 1):
            angle = 2 * math.pi * step / steps
            points.append((radius * math.cos(angle), radius * math.sin(angle), 0.0))
        self.circle_coords.point.setValues(0, len(points), points)
        self.circle_lines.numVertices.setValue(len(points))
        arm = 8.0
        cross = [(-arm, 0.0, 0.0), (arm, 0.0, 0.0), (0.0, -arm, 0.0), (0.0, arm, 0.0)]
        self.cross_coords.point.setValues(0, 4, cross)
        vertices = self.cross_lines.numVertices
        vertices.setNum(2)
        vertices.set1Value(0, 2)
        vertices.set1Value(1, 2)

    def _place_marker(self, pos):
        if self.translation is None or pos is None:
            return
        self._sync_marker_shape()
        self.translation.translation.setValue(float(pos[0]), float(pos[1]), 0.0)
        if self.switch is not None:
            self.switch.whichChild = 0
        self._blank_cursor()

    def _install_cursor(self):
        self.widget = _quarter_widget()
        if self.widget is None:
            return
        self.old_cursor = QtGui.QCursor(self.widget.cursor())

    def _blank_cursor(self):
        if self.widget is None or self.old_cursor is None:
            return
        self.widget.setCursor(QtCore.Qt.BlankCursor)

    def _restore_cursor(self):
        widget = self.widget
        self.widget = None
        if widget is None or self.old_cursor is None:
            return
        try:
            widget.setCursor(self.old_cursor)
        except Exception:
            pass

    def _disable_popup(self):
        self.popup_enabled = bool(self.view.isPopupMenuEnabled())
        self.view.setPopupMenuEnabled(False)

    def _restore_popup(self):
        if self.popup_enabled is None or self.view is None:
            return
        try:
            self.view.setPopupMenuEnabled(bool(self.popup_enabled))
        except Exception:
            pass

    def _install_filter(self):
        if self.widget is None:
            return
        self.filter = _ViewFilter(self)
        self.widget.installEventFilter(self.filter)

    def _remove_filter(self):
        if self.widget is not None and self.filter is not None:
            try:
                self.widget.removeEventFilter(self.filter)
            except Exception:
                pass
        self.filter = None

    def _remove_callback(self):
        if self.view is not None and self.callback_fn is not None:
            try:
                self.view.removeEventCallback("SoEvent", self.callback_fn)
            except Exception:
                pass
        self.callback = None
        self.callback_fn = None

    def _remove_marker(self):
        if not self.graph_held:
            return
        self.graph_held = False
        try:
            if self.marker is not None:
                self.graph.removeChild(self.marker)
        except Exception:
            pass
        finally:
            try:
                self.graph.unref()
            except Exception:
                pass
        self.marker = None

    def _remove_observer(self):
        if self.observer is None:
            return
        try:
            Gui.removeDocumentObserver(self.observer)
        except Exception:
            pass
        self.observer = None


def _active_view():
    gui_doc = getattr(Gui, "ActiveDocument", None)
    if gui_doc is None:
        return None
    view = gui_doc.activeView()
    if view is None or not hasattr(view, "getObjectsInfo"):
        return None
    return view


def _navigation_name(view):
    try:
        return str(view.getNavigationType())
    except Exception as exc:
        raise LocateError(tr('Could not read the navigation style. It was not changed.')) from exc


def _is_cad_navigation(name):
    return name.endswith("CADNavigationStyle") and "Tinker" not in name


def _workbench_name():
    try:
        workbench = Gui.activeWorkbench()
    except Exception:
        return ""
    for attr in ("name", "MenuText"):
        value = getattr(workbench, attr, None)
        if callable(value):
            try:
                return str(value())
            except Exception:
                continue
        elif value:
            return str(value)
    return type(workbench).__name__


def _selection_snapshot(document):
    items = []
    try:
        selection = Gui.Selection.getSelectionEx(document.Name)
    except Exception:
        return items
    for item in selection:
        items.append((item.Object.Name, tuple(item.SubElementNames)))
    return items


def _restore_selection(document, doc_name, snapshot):
    try:
        if App.listDocuments().get(doc_name) is not document:
            return
        Gui.Selection.clearSelection(doc_name)
        for name, subs in snapshot:
            obj = document.getObject(name)
            if obj is None:
                continue
            if not subs:
                Gui.Selection.addSelection(obj)
            else:
                for sub in subs:
                    Gui.Selection.addSelection(obj, sub)
    except Exception:
        pass


def _clear_preselection():
    try:
        Gui.Selection.clearPreselection()
    except Exception:
        pass


def _whole_key(item, doc_name):
    if not isinstance(item, dict):
        return None
    if item.get("ParentObject") or item.get("SubName"):
        return None
    document_name = item.get("Document")
    object_name = item.get("Object")
    if document_name != doc_name or not object_name:
        return None
    return (document_name, object_name)


def _pickable(obj):
    view = getattr(obj, "ViewObject", None)
    if view is None:
        return False
    if getattr(view, "Visibility", True) is False:
        return False
    if getattr(view, "Selectable", True) is False:
        return False
    return True


def _viewport_size(viewer):
    region = viewer.getSoRenderManager().getViewportRegion()
    size = region.getViewportSizePixels().getValue()
    return float(size[0]), float(size[1])


def _quarter_widget():
    window = Gui.getMainWindow()
    area = window.findChild(QtWidgets.QMdiArea)
    if area is None or area.activeSubWindow() is None:
        return None
    host = area.activeSubWindow().widget()
    if host is None:
        return None
    for child in host.findChildren(QtWidgets.QWidget):
        if child.inherits("SIM::Coin3D::Quarter::QuarterWidget"):
            return child
    return None
