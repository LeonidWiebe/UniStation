"""Native title bars and profile layout for UniStation's own toolbars only."""

from unistation.i18n import TOOLBAR_LABELS, tr

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets
from unistation.toolbar_layout import KEYS, LayoutStore


TOOLBAR_NAMES = tuple(KEYS)
FRAME_HINTS = (QtCore.Qt.FramelessWindowHint | QtCore.Qt.X11BypassWindowManagerHint
               | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint
               | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowCloseButtonHint
               | QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowMaximizeButtonHint
               | QtCore.Qt.WindowContextHelpButtonHint)
TITLE_HINTS = (QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint
               | QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowCloseButtonHint)
_controller = None


def activate():
    global _controller
    deactivate()
    _controller = ToolbarTitles()
    _controller.schedule_scan()


def deactivate():
    global _controller
    if _controller is not None:
        _controller.stop()
        _controller = None


class ToolbarTitles(QtCore.QObject):
    def __init__(self):
        super().__init__(Gui.getMainWindow())
        self.running = True
        self.watchers = []
        self.store = LayoutStore()
        self.flush_timer = QtCore.QTimer(self)
        self.flush_timer.setSingleShot(True)
        self.flush_timer.timeout.connect(self.flush_profile)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.scan)
        Gui.getMainWindow().installEventFilter(self)
        Gui.getMainWindow().workbenchActivated.connect(self.after_restore)
        Gui.getMainWindow().mainWindowClosed.connect(self.flush_all)
        self.window_params = App.ParamGet("User parameter:BaseApp/Preferences/MainWindow")
        self.window_params.Attach(self)

    def onChange(self, group, name):
        if name == "WindowStateRestored":
            self.after_restore()

    def after_restore(self, *args):
        if self.running:
            self.schedule_scan()
            for watcher in self.watchers:
                watcher.request_restore()

    def saved(self):
        if self.running:
            self.flush_timer.start(500)

    def flush_profile(self):
        self.flush_timer.stop()
        try:
            self.store.flush()
        except Exception as exc:
            App.Console.PrintError(tr('UniStation: saving toolbar positions: ') + str(exc) + "\n")

    def flush_all(self, *args):
        for watcher in self.watchers:
            if watcher.user_layout:
                watcher.capture(force=True)
            watcher.flush_pending()
        self.flush_timer.stop()
        self.flush_profile()

    def schedule_scan(self):
        if self.running:
            self.timer.start(0)

    def eventFilter(self, watched, event):
        # New native toolbars are first parented to MainWindow. Wait until their
        # construction/action population is complete before inspecting them.
        if event.type() in (QtCore.QEvent.ChildAdded, QtCore.QEvent.ChildRemoved):
            self.schedule_scan()
        elif event.type() == QtCore.QEvent.Close:
            self.flush_all()
        return False

    def scan(self):
        if not self.running:
            return
        try:
            retained = []
            for item in self.watchers:
                if item.toolbar is None:
                    item.deleteLater()
                else:
                    retained.append(item)
            self.watchers = retained
            known = [item.toolbar for item in self.watchers]
            for toolbar in Gui.getMainWindow().findChildren(QtWidgets.QToolBar):
                if toolbar in known or toolbar.objectName() not in TOOLBAR_NAMES:
                    continue
                if not any(str(action.data()).startswith("UniStation_")
                           for action in toolbar.actions()):
                    continue  # A similarly named toolbar of another Workbench.
                if toolbar.objectName() in ("Рисование", "Манипуляции", "Привязки"):
                    toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
                self.watchers.append(FloatingTitle(toolbar, self))
        except RuntimeError:
            pass  # Main window/toolbar may be going away during application exit.

    def stop(self):
        self.flush_all()
        self.running = False
        self.timer.stop()
        self.flush_timer.stop()
        self.window_params.Detach(self)
        window = Gui.getMainWindow()
        if window is not None:
            window.removeEventFilter(self)
            window.workbenchActivated.disconnect(self.after_restore)
            window.mainWindowClosed.disconnect(self.flush_all)
        for watcher in self.watchers:
            watcher.stop()
        self.watchers.clear()
        self.deleteLater()


class FloatingTitle(QtCore.QObject):
    def __init__(self, toolbar, parent):
        super().__init__(parent)
        self.toolbar = toolbar
        self.name = toolbar.objectName()
        self.running = True
        self.updating = False
        self.failed = False
        self.ready = False
        self.restoring = False
        self.restore_pending = True
        self.user_layout = False
        self.pending = None
        self.bad_record = False
        try:
            self.state = parent.store.load(self.name)
        except (ValueError, TypeError) as exc:
            self.state = None
            self.bad_record = True
            App.Console.PrintWarning(tr('UniStation: position of toolbar “') + tr(TOOLBAR_LABELS[self.name])
                                     + tr('” was not restored: ') + str(exc) + "\n")
        self.original_hints = None
        self.delete_on_close = toolbar.testAttribute(QtCore.Qt.WA_DeleteOnClose)
        # Native QWidget.close() must hide the toolbar and update toggleViewAction,
        # not delete the commands, controls or saved active attribute values.
        toolbar.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.sync)
        self.save_timer = QtCore.QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.capture)
        self.settle_timer = QtCore.QTimer(self)
        self.settle_timer.setSingleShot(True)
        self.settle_timer.timeout.connect(self.finish_restore)
        toolbar.installEventFilter(self)
        toolbar.topLevelChanged.connect(self.top_level_changed)
        toolbar.destroyed.connect(self.toolbar_deleted)
        self.schedule()

    def schedule(self, *args):
        if self.running and not self.failed and not self.updating:
            self.timer.start(0)

    def eventFilter(self, watched, event):
        kind = event.type()
        if not self.updating:
            if kind in (QtCore.QEvent.MouseButtonPress, QtCore.QEvent.NonClientAreaMouseButtonPress):
                if event.button() == QtCore.Qt.LeftButton:
                    self.begin_user_layout()
            elif kind in (QtCore.QEvent.Move, QtCore.QEvent.Resize):
                if self.ready and not self.restoring and not self.restore_pending:
                    self.queue_capture()
            elif kind in (QtCore.QEvent.MouseButtonRelease, QtCore.QEvent.NonClientAreaMouseButtonRelease):
                if self.user_layout:
                    self.queue_capture()
            elif kind == QtCore.QEvent.Close:
                if self.ready:
                    self.capture(force=True)
                self.flush_pending()
                self.parent().flush_profile()
            elif kind == QtCore.QEvent.Show and self.ready and not self.user_layout:
                self.request_restore()
        if event.type() in (QtCore.QEvent.Show, QtCore.QEvent.WinIdChange,
                            QtCore.QEvent.ParentChange, QtCore.QEvent.MouseButtonRelease):
            self.schedule()
        # Mouse/close/docking events continue through the native FreeCAD/Qt code.
        return False

    def begin_user_layout(self):
        self.user_layout = True
        self.restore_pending = False
        self.restoring = False
        self.ready = True
        self.settle_timer.stop()

    def top_level_changed(self, floating):
        if self.ready and not self.updating and not self.restoring and not self.restore_pending:
            self.queue_capture()
        self.schedule()

    def request_restore(self):
        if self.running and not self.user_layout:
            self.settle_timer.stop()
            self.restoring = False
            self.restore_pending = True
            self.ready = False
            self.pending = None
            self.save_timer.stop()
            self.schedule()

    def queue_capture(self):
        # Cache the actual event geometry now. Workbench deactivation/close can
        # happen before the debounce expires or after FreeCAD hides the toolbar.
        if (self.toolbar is not None and self.ready and not self.restoring
                and not self.updating and not self.restore_pending and self.toolbar.isVisible()):
            value = self.snapshot()
            if value is not None:
                self.pending = value
        self.save_timer.start(250)

    def snapshot(self):
        toolbar = self.toolbar
        floating = toolbar.isFloating()
        rect = self.state["rect"] if self.state else None
        screen = self.state["screen"] if self.state else ""
        orientation = "vertical" if toolbar.orientation() == QtCore.Qt.Vertical else "horizontal"
        if floating:
            if (toolbar.windowFlags() & FRAME_HINTS) != TITLE_HINTS:
                return None  # Intermediate frameless native drag/restore geometry.
            frame = toolbar.frameGeometry()
            rect = [frame.x(), frame.y(), toolbar.width(), toolbar.height()]
            if toolbar.screen() is not None:
                screen = toolbar.screen().name()
        return {"version": 1, "floating": floating, "rect": rect,
                "screen": screen, "orientation": orientation}

    def capture(self, force=False):
        if (self.toolbar is None or not self.ready or self.updating or self.restore_pending
                or (self.restoring and not (force and self.user_layout))):
            return
        if not force and QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
            self.save_timer.start(40)
            return
        try:
            if self.toolbar.isVisible():
                self.pending = self.snapshot() or self.pending
            self.flush_pending()
            self.user_layout = False
        except RuntimeError:
            self.toolbar_deleted()

    def flush_pending(self):
        self.save_timer.stop()
        if self.pending is not None:
            try:
                self.parent().store.save(self.name, self.pending)
                self.state = self.pending
                self.pending = None
                self.bad_record = False
                self.parent().saved()
            except Exception as exc:
                App.Console.PrintError(tr('UniStation: position of toolbar “') + tr(TOOLBAR_LABELS[self.name])
                                       + tr('” was not saved: ') + str(exc) + "\n")

    def finish_restore(self):
        self.restoring = False
        self.ready = True
        if self.user_layout:
            self.queue_capture()
        elif self.state is None and not self.bad_record and self.toolbar is not None:
            if self.toolbar.isFloating():
                self.capture()

    def toolbar_deleted(self, *args):
        self.toolbar = None
        self.timer.stop()
        self.save_timer.stop()
        self.settle_timer.stop()
        self.running = False
        self.parent().schedule_scan()

    def sync(self):
        if not self.running or self.failed or self.toolbar is None:
            return
        try:
            toolbar = self.toolbar
            if self.restore_pending and toolbar.isVisible():
                if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
                    self.timer.start(40)
                    return
                self.restore_saved()
            if not toolbar.isFloating():
                self.original_hints = None
                return  # Never change flags/layout/height of a docked toolbar.
            if not toolbar.isVisible():
                return  # In particular, do not reopen a toolbar closed by the user.
            # Qt recreates the frameless platform window while unplugging and at
            # drag end, sometimes without another topLevelChanged signal. Wait
            # for release instead of recreating a window that owns a mouse grab.
            if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
                self.timer.start(40)
                return
            flags = toolbar.windowFlags()
            wanted = (flags & ~FRAME_HINTS) | TITLE_HINTS
            if wanted != flags:
                if self.original_hints is None:
                    self.original_hints = flags & FRAME_HINTS
                self.swap_flags(wanted)
                self.keep_on_screen()
                self.schedule()  # One settling pass after native frame creation.
                # Frame recreation is not a user move/resize.
                self.save_timer.stop()
                self.restoring = True
                self.settle_timer.start(150)
        except RuntimeError:
            self.toolbar_deleted()
        except Exception as exc:
            self.failed = True
            App.Console.PrintError(tr('UniStation: title of toolbar “') + tr(TOOLBAR_LABELS[self.name])
                                   + tr("”: ") + str(exc) + "\n")

    def restore_saved(self):
        toolbar = self.toolbar
        if QtWidgets.QApplication.mouseButtons() != QtCore.Qt.NoButton:
            return
        self.restore_pending = False
        self.restoring = True
        self.save_timer.stop()
        if self.state and self.state["floating"]:
            if not toolbar.isFloating():
                if toolbar.parentWidget() is not Gui.getMainWindow():
                    # Native menu/status-bar areas have their own layout and prefs.
                    self.restoring = False
                    self.ready = True
                    App.Console.PrintWarning(tr('UniStation: toolbar “') + tr(TOOLBAR_LABELS[self.name])
                                             + tr('” has a saved floating position; its special docked area is left to FreeCAD.\n'))
                    return
                flags = (toolbar.windowFlags() & ~QtCore.Qt.WindowType_Mask) | QtCore.Qt.Tool
                if self.original_hints is None:
                    self.original_hints = flags & FRAME_HINTS
                self.swap_flags((flags & ~FRAME_HINTS) | TITLE_HINTS)
                toolbar.topLevelChanged.emit(True)
            elif (toolbar.windowFlags() & FRAME_HINTS) != TITLE_HINTS:
                if self.original_hints is None:
                    self.original_hints = toolbar.windowFlags() & FRAME_HINTS
                self.swap_flags((toolbar.windowFlags() & ~FRAME_HINTS) | TITLE_HINTS)
            self.restore_rect(self.state)
        self.settle_timer.start(150)

    def restore_rect(self, state):
        toolbar = self.toolbar
        x, y, width, height = state["rect"]
        screens = QtWidgets.QApplication.screens()
        screen = next((item for item in screens if item.name() == state["screen"]), None)
        if screen is None:
            saved = QtCore.QRect(x, y, width, height)
            screen = max(screens, key=lambda item: _intersection_area(item.availableGeometry(), saved),
                         default=toolbar.screen())
        if screen is None:
            return
        area = screen.availableGeometry()
        frame = toolbar.frameGeometry()
        margin_w = max(0, frame.width() - toolbar.width())
        margin_h = max(0, frame.height() - toolbar.height())
        toolbar.setOrientation(QtCore.Qt.Vertical if state["orientation"] == "vertical"
                               else QtCore.Qt.Horizontal)
        toolbar.resize(min(width, max(1, area.width() - margin_w)),
                       min(height, max(1, area.height() - margin_h)))
        toolbar.move(x, y)
        self.keep_on_screen(area)

    def swap_flags(self, flags):
        toolbar = self.toolbar
        position = toolbar.pos()
        visible = toolbar.isVisible()
        no_activate = toolbar.testAttribute(QtCore.Qt.WA_ShowWithoutActivating)
        self.updating = True
        try:
            toolbar.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, True)
            toolbar.setWindowFlags(flags)
            toolbar.move(position)
            if visible:
                toolbar.show()
        finally:
            try:
                toolbar.setAttribute(QtCore.Qt.WA_ShowWithoutActivating, no_activate)
            finally:
                self.updating = False

    def keep_on_screen(self, area=None):
        toolbar = self.toolbar
        if area is None:
            screen = toolbar.screen()
            if screen is None:
                return
            area = screen.availableGeometry()
        frame = toolbar.frameGeometry()
        left = min(max(frame.left(), area.left()), max(area.left(), area.right() - frame.width() + 1))
        top = min(max(frame.top(), area.top()), max(area.top(), area.bottom() - frame.height() + 1))
        if frame.topLeft() != QtCore.QPoint(left, top):
            was_updating = self.updating
            self.updating = True
            try:
                toolbar.move(left, top)
            finally:
                self.updating = was_updating

    def stop(self):
        self.flush_pending()
        self.running = False
        self.timer.stop()
        self.save_timer.stop()
        self.settle_timer.stop()
        toolbar = self.toolbar
        if toolbar is not None:
            try:
                toolbar.removeEventFilter(self)
                toolbar.topLevelChanged.disconnect(self.top_level_changed)
                toolbar.destroyed.disconnect(self.toolbar_deleted)
                if toolbar.isFloating() and self.original_hints is not None:
                    self.swap_flags((toolbar.windowFlags() & ~FRAME_HINTS) | self.original_hints)
                toolbar.setAttribute(QtCore.Qt.WA_DeleteOnClose, self.delete_on_close)
            except RuntimeError:
                pass
        self.toolbar = None
        self.deleteLater()


def _intersection_area(first, second):
    overlap = first.intersected(second)
    return max(0, overlap.width()) * max(0, overlap.height())
