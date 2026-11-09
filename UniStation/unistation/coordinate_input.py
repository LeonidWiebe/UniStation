"""Independent modeless window for the existing explicit coordinate input."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from unistation.i18n import (
    QT_TRANSLATE_NOOP, bind, tr, translated_button, translated_label,
)
from unistation.keyin import parse_point
from unistation.line import LineSession, PointResult
from unistation.wire import WireSession
from unistation.circle import CircleSession


_window = None


def _current_session():
    from unistation.gui import active_input
    session = active_input()
    if (type(session) in (LineSession, WireSession, CircleSession)
            and not session.closed and session.backend.alive()):
        return session
    return None


def reset_for(session):
    if _window is not None and _window.session is session:
        _window.clear_entry()
        _window.generation = None
        QtCore.QTimer.singleShot(0, _window.refresh)


def deactivate():
    if _window is not None:
        _window.close()


class CoordinateEdit(QtWidgets.QLineEdit):
    def event(self, event):
        if event.type() == QtCore.QEvent.ShortcutOverride and event.key() in (
                QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Escape):
            event.accept()
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            event.accept()
            self.window().close()
            return
        super().keyPressEvent(event)


class CoordinateWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__(Gui.getMainWindow(), QtCore.Qt.Tool)
        self.setObjectName("unistation_coordinate_input")
        self.setModal(False)
        bind(self, "setWindowTitle", "Coordinate Input")
        self.resize(560, 190)
        self.session = None
        self.generation = None
        self.applying = False
        layout = QtWidgets.QVBoxLayout(self)
        self.status = QtWidgets.QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        label = translated_label('World coordinates; values without units are in mm')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.coordinate_edit = CoordinateEdit()
        self.coordinate_edit.setObjectName("unistation_keyin")
        self.coordinate_edit.setPlaceholderText("abs 10; 20; 0   /   rel 5 cm; 0; 0")
        layout.addWidget(self.coordinate_edit)
        self.coordinate_error = QtWidgets.QLabel()
        self.coordinate_error.setObjectName("unistation_keyin_error")
        self.coordinate_error.setWordWrap(True)
        layout.addWidget(self.coordinate_error)
        buttons = QtWidgets.QHBoxLayout()
        self.coordinate_apply = translated_button('Apply')
        self.coordinate_apply.setObjectName("unistation_keyin_apply")
        self.coordinate_apply.setAutoDefault(False)
        self.coordinate_apply.setDefault(False)
        buttons.addWidget(self.coordinate_apply)
        close = translated_button('Close')
        close.setAutoDefault(False)
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.coordinate_edit.returnPressed.connect(self.apply_coordinates)
        self.coordinate_apply.clicked.connect(self.apply_coordinates)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.refresh)

    def clear_entry(self):
        self.coordinate_edit.clear()
        self.coordinate_error.clear()

    def refresh(self):
        session = _current_session()
        generation = session._input_generation if session is not None else None
        if session is not self.session or generation != self.generation:
            self.clear_entry()
            self.session = session
            self.generation = generation
        self.coordinate_edit.setEnabled(session is not None)
        self.coordinate_apply.setEnabled(session is not None)
        if session is None:
            bind(self.status, 'setText', 'Start Line, Wire or Circle to enter coordinates.')
        else:
            bind(self.status, 'setText', 'Input target: {0}',
                 session.backend.panel.form.windowTitle())

    def focus_input(self):
        if self.session is not None:
            self.raise_()
            self.activateWindow()
            self.coordinate_edit.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        self.timer.start()
        self.focus_input()

    def hideEvent(self, event):
        self.timer.stop()
        self.clear_entry()
        self.session = None
        self.generation = None
        super().hideEvent(event)

    def apply_coordinates(self):
        if self.applying:
            return
        session = _current_session()
        if (session is None or session is not self.session
                or session._input_generation != self.generation):
            self.refresh()
            return
        self.applying = True
        try:
            try:
                if type(session) is WireSession:
                    base = tuple(session.points[-1]) if session.points else None
                else:
                    base = tuple(session.first) if session.first is not None else None
                point = App.Vector(*parse_point(self.coordinate_edit.text(), base))
            except ValueError as exc:
                self.coordinate_error.setText(str(exc))
                self.focus_input()
                self.coordinate_edit.selectAll()
                return
            result = session.submit_point(point)
            if session.closed:
                self.refresh()
                return
            if result is PointResult.ACCEPTED:
                self.clear_entry()
            else:
                self.coordinate_error.setText(session.last_error)
                self.coordinate_edit.selectAll()
            self.focus_input()
        except Exception as exc:
            self.coordinate_error.setText(tr('Coordinate input failed: {0}').format(str(exc)))
            self.focus_input()
        finally:
            self.applying = False


class CoordinateCommand:
    def GetResources(self):
        return {
            "CmdType": "ForEdit NoTransaction",
            "MenuText": QT_TRANSLATE_NOOP("UniStation_CoordinateInput", "Coordinate Input..."),
            "ToolTip": QT_TRANSLATE_NOOP("UniStation_CoordinateInput",
                "Open the separate coordinate input window"),
        }

    def IsActive(self):
        return True

    def Activated(self):
        global _window
        if _window is None:
            _window = CoordinateWindow()
        _window.show()
        _window.raise_()
        _window.activateWindow()
        _window.refresh()
        _window.focus_input()


def register():
    Gui.addCommand("UniStation_CoordinateInput", CoordinateCommand())
