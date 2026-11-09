"""Route the assigned Reset click before Qt forwards it to Coin/navigation."""

import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from unistation import preferences


_controller = None


def activate():
    global _controller
    if _controller is None:
        _controller = MouseController()
        QtWidgets.QApplication.instance().installEventFilter(_controller)


def deactivate():
    global _controller
    if _controller is not None:
        QtWidgets.QApplication.instance().removeEventFilter(_controller)
        _controller.deleteLater()
        _controller = None


def _viewport():
    area = Gui.getMainWindow().findChild(QtWidgets.QMdiArea)
    host = area.activeSubWindow().widget() if area and area.activeSubWindow() else None
    if host is not None:
        for widget in host.findChildren(QtWidgets.QWidget):
            if widget.inherits("SIM::Coin3D::Quarter::QuarterWidget"):
                return widget
    return None


def _inside(widget, viewport):
    return (viewport is not None and isinstance(widget, QtWidgets.QWidget)
            and (widget is viewport or viewport.isAncestorOf(widget)))


class MouseController(QtCore.QObject):
    def __init__(self):
        super().__init__(Gui.getMainWindow())
        self.gesture = None
        self.suppress_context = None

    def eventFilter(self, watched, event):
        try:
            return self.route(watched, event)
        except (RuntimeError, ReferenceError):
            # Qt may be deleting the original view during document shutdown.
            self.gesture = None
            self.suppress_context = None
            return False

    def route(self, watched, event):
        kind = event.type()
        if kind == QtCore.QEvent.ContextMenu:
            if (event.reason() == QtGui.QContextMenuEvent.Mouse
                    and _inside(watched, self.suppress_context)):
                self.suppress_context = None
                return True
            return False
        if kind not in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonDblClick,
                        QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.MouseMove):
            return False
        # QApplication first sees the platform QWindow event, then the QWidget
        # delivery. A QWindow release must not clear a gesture captured on the
        # viewport widget: otherwise the real release never reaches the command.
        if not isinstance(watched, QtWidgets.QWidget):
            return False

        from unistation.gui import active_input, reset

        press = kind in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.MouseButtonDblClick)
        if self.gesture is not None:
            session, viewport, start, armed = self.gesture
            if (event.modifiers() != QtCore.Qt.NoModifier
                    or event.buttons() & (QtCore.Qt.LeftButton | QtCore.Qt.MiddleButton)
                    or (event.globalPos() - start).manhattanLength()
                    > QtWidgets.QApplication.startDragDistance()):
                armed = False
                self.gesture = (session, viewport, start, armed)
            if kind == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.RightButton:
                self.gesture = None
                # Windows can generate a context-menu event even for a consumed click.
                self.suppress_context = viewport
                if (armed and _inside(watched, viewport) and active_input() is session
                        and QtWidgets.QApplication.activeModalWidget() is None
                        and QtWidgets.QApplication.activePopupWidget() is None):
                    # Dispatch to the captured command only; never a newer command.
                    QtCore.QTimer.singleShot(0, lambda: reset(expected=session, source="mouse"))
                return True
            if press and event.button() == QtCore.Qt.RightButton:
                return True
            if kind == QtCore.QEvent.MouseMove:
                return _inside(watched, viewport)
            return False

        if not press:
            return False
        self.suppress_context = None
        if (event.button() != QtCore.Qt.RightButton
                or event.modifiers() != QtCore.Qt.NoModifier
                or event.buttons() != QtCore.Qt.RightButton
                or QtWidgets.QApplication.activeModalWidget() is not None
                or QtWidgets.QApplication.activePopupWidget() is not None
                or preferences.right_button_action() != preferences.RESET):
            return False
        session = active_input()
        if session is None:
            return False
        backend = getattr(session, "backend", None)
        view = backend.view if backend is not None else session.view
        if Gui.activeDocument() is None or Gui.activeDocument().activeView() != view:
            return False
        viewport = _viewport()
        if not _inside(watched, viewport):
            return False
        self.gesture = (session, viewport, event.globalPos(), True)
        self.suppress_context = viewport
        return True
