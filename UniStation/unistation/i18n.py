"""Qt Linguist translations using FreeCAD's current application language."""

from pathlib import Path
import sys


def tr(source):
    # Keep geometry/validation modules usable without loading a GUI binding.
    try:
        from PySide import QtCore
    except ImportError:
        return source
    return QtCore.QCoreApplication.translate("UniStation", source)


def QT_TRANSLATE_NOOP(context, source):
    """Mark native FreeCAD command resources; FreeCAD translates their context."""
    return source


def bind(widget, method, source, *args, percent=None):
    """The usual retranslateUi operation, retaining a widget's current values."""
    from PySide import QtCore

    binding = getattr(widget, "_ustn_translation_binding", None)
    if binding is None:
        class Binding(QtCore.QObject):
            def __init__(self, target):
                super().__init__(target)
                self.entries = {}
                target.installEventFilter(self)

            def apply(self, name):
                text, values, percent_values = self.entries[name]
                translated = tr(text)
                if values:
                    translated = translated.format(*(v() if callable(v) else v for v in values))
                if percent_values is not None:
                    translated %= percent_values
                getattr(self.parent(), name)(translated)

            def eventFilter(self, watched, event):
                if event.type() == QtCore.QEvent.LanguageChange:
                    for name in self.entries:
                        self.apply(name)
                return False

        binding = Binding(widget)
        widget._ustn_translation_binding = binding
    binding.entries[method] = (source, args, percent)
    binding.apply(method)
    return widget


def translated_label(source, *args):
    from PySide import QtWidgets
    return bind(QtWidgets.QLabel(), "setText", source, *args)


def translated_button(source, *args):
    from PySide import QtWidgets
    return bind(QtWidgets.QPushButton(), "setText", source, *args)


def translated_dialog_button(box, source, role):
    button = box.addButton(tr(source), role)
    return bind(button, "setText", source)


# The names are persistent native toolbar identities, not visible translations.
TOOLBAR_LABELS = {
    "UniStation": "UniStation",
    "Рисование": QT_TRANSLATE_NOOP("UniStation", "Drawing"),
    "Манипуляции": QT_TRANSLATE_NOOP("UniStation", "Manipulations"),
    "Палитра": QT_TRANSLATE_NOOP("UniStation", "Palette"),
    "Атрибуты": QT_TRANSLATE_NOOP("UniStation", "Attributes"),
    "Привязки": QT_TRANSLATE_NOOP("UniStation", "Snapping"),
}
_observer = None


def install():
    """Register QM catalogs once; the FreeCAD translator owns language choice."""
    global _observer
    if _observer is not None:
        return
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui, QtWidgets

    class LocaleObserver(QtCore.QObject):
        def __init__(self, window):
            super().__init__(window)
            self.timer = QtCore.QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.refresh)
            window.installEventFilter(self)
            window.workbenchActivated.connect(self.schedule)

        def schedule(self, *args):
            self.timer.start(0)

        def eventFilter(self, watched, event):
            if event.type() in (QtCore.QEvent.LanguageChange, QtCore.QEvent.ChildAdded):
                self.schedule()
            return False

        def refresh(self):
            for toolbar in self.parent().findChildren(QtWidgets.QToolBar):
                source = TOOLBAR_LABELS.get(toolbar.objectName())
                if source and any(str(a.data()).startswith("UniStation_") for a in toolbar.actions()):
                    toolbar.setWindowTitle(tr(source))
            action_type = getattr(QtGui, "QAction", None) or QtWidgets.QAction
            for action in self.parent().findChildren(action_type):
                if action.objectName() == "UniStationWorkbench":
                    action.setToolTip(tr("Draft geometry with AxisFlow coordinate input"))
            module = sys.modules.get("unistation.attributes_gui")
            controller = getattr(module, "_controller", None)
            if controller is not None:
                controller.schedule_refresh()

    Gui.addLanguagePath(str(Path(__file__).resolve().parent / "translations"))
    _observer = LocaleObserver(Gui.getMainWindow())
    Gui.updateLocale()
    _observer.timer.start(0)
