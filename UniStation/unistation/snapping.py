"""UniStation snap toolbar sharing Draft's live modes and AxisFlow's enable flag."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore

from unistation.i18n import QT_TRANSLATE_NOOP, tr


MASTER = "UniStation_Snap_Lock"
MODES = (
    "Endpoint", "Midpoint", "Center", "Angle", "Intersection",
    "Perpendicular", "Extension", "Parallel", "Special", "Near", "Ortho",
    "Grid", "WorkingPlane", "Dimensions",
)
_controller = None


def _engines():
    import AxisFlow
    snapper = getattr(Gui, "Snapper", None)
    if (snapper is None or not callable(getattr(snapper, "toggle_snap", None))
            or not callable(getattr(AxisFlow, "getSettings", None))
            or not callable(getattr(AxisFlow, "setSetting", None))):
        raise RuntimeError(tr('Draft and AxisFlow snapping controls are unavailable.'))
    return snapper, AxisFlow


def _enabled():
    snapper, axisflow = _engines()
    return "Lock" in snapper.active_snaps and bool(axisflow.getSettings()["useSnapping"])


class SnapLockCommand:
    def GetResources(self):
        return {
            "Pixmap": "Draft_Snap_Lock",
            "MenuText": QT_TRANSLATE_NOOP("UniStation_Snap_Lock", "Enable snapping"),
            "ToolTip": QT_TRANSLATE_NOOP("UniStation_Snap_Lock",
                "Enable or disable snapping in UniStation (Draft and AxisFlow)"),
            "CmdType": "ForEdit NoTransaction",
            "Checkable": False,
        }

    def IsActive(self):
        try:
            _engines()
            return True
        except (ImportError, RuntimeError):
            return False

    def Activated(self, status):
        snapper, axisflow = _engines()
        previous = bool(axisflow.getSettings()["useSnapping"])
        enabled = bool(status)
        try:
            axisflow.setSetting("useSnapping", enabled)
            if ("Lock" in snapper.active_snaps) != enabled:
                # FreeCAD 1.1.4 treats set_to=False as toggle; toggle only when
                # the live state differs, instead of relying on that argument.
                snapper.toggle_snap("Lock")
        except Exception as exc:
            axisflow.setSetting("useSnapping", previous)
            App.Console.PrintError(tr('UniStation: could not change snapping: {0}').format(exc) + "\n")
        if _controller is not None:
            _controller.refresh()


def register():
    # Initialize the same Snapper/resources used by AxisFlow, also when the
    # user activates UniStation directly without visiting Draft first.
    import DraftTools  # noqa: F401
    from draftguitools import gui_snaps  # noqa: F401
    Gui.addIconPath(":/icons")
    Gui.addLanguagePath(":/translations")
    Gui.addCommand(MASTER, SnapLockCommand())
    commands = ["Draft_Snap_" + mode for mode in MODES]
    missing = set(commands).difference(Gui.listCommands())
    if missing:
        raise RuntimeError(tr('Draft snap commands are unavailable: {0}').format(
            ", ".join(sorted(missing))))
    Gui.updateLocale()
    return [MASTER] + commands


def activate():
    global _controller
    deactivate()
    _controller = SnapState()
    _controller.refresh()


def deactivate():
    global _controller
    if _controller is not None:
        _controller.timer.stop()
        _controller.deleteLater()
        _controller = None


class SnapState(QtCore.QObject):
    def __init__(self):
        super().__init__(Gui.getMainWindow())
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()

    def refresh(self):
        try:
            enabled = _enabled()
            snapper = Gui.Snapper
            # Native Draft actions are shared across its toolbar, AxisFlow and
            # this toolbar. Refresh their checks after changes from elsewhere.
            states = [(MASTER, enabled), ("Draft_Snap_Lock", "Lock" in snapper.active_snaps)]
            states += [("Draft_Snap_" + mode, mode in snapper.active_snaps) for mode in MODES]
            for name, checked in states:
                for action in Gui.Command.get(name).getAction():
                    blocked = action.blockSignals(True)
                    try:
                        action.setChecked(checked)
                    finally:
                        action.blockSignals(blocked)
        except (ImportError, RuntimeError):
            pass  # Unavailable engines or widgets being destroyed at shutdown.
