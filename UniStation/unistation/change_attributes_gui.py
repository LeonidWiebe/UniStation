"""Select an attribute patch, then apply it to selected or located elements."""

from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from unistation import attributes, element_attributes, levels
from unistation.attributes_gui import (
    ColorPanel, LineStylePanel, STYLE_LABELS, _color_icon, _line_style_icon,
)
from unistation.element_attributes import AttributePatch, KEEP_RGB
from unistation.i18n import QT_TRANSLATE_NOOP, bind, tr, translated_button
from unistation.input_events import ResettableCommand
from unistation.line_weight_widgets import LineWeightPanel, weight_icon
from unistation.locate import LocateError, begin
from unistation.palette import PaletteError, color_drift, same_document
from unistation.palette_gui import _require_idle
from unistation.transform_gui import selected_objects, whole_object_error


COMMAND = "UniStation_ChangeAttributes"
_current = None


def active_session():
    return _current


def cancel():
    if _current is not None:
        _current.cancel()


def register():
    Gui.addCommand(COMMAND, ChangeAttributesCommand())
    # Preserve the entry point for existing macros and customized toolbars.
    Gui.addCommand("UniStation_IndexedColor", ChangeAttributesCommand())


class ChangeAttributesCommand:
    def GetResources(self):
        return {
            "CmdType": "NoTransaction",
            "Pixmap": str(Path(__file__).resolve().parent / "icons" / "change-attributes.svg"),
            "MenuText": QT_TRANSLATE_NOOP('UniStation_ChangeAttributes', 'Change Attributes'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_ChangeAttributes', 'Change the layer or line attributes of selected elements'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            _require_idle()
            document = App.ActiveDocument
            if document is None:
                return
            objects = (selected_objects(tr('Select one or more whole objects.'))
                       if Gui.Selection.getSelectionEx(document.Name) else [])
            ChangeAttributesTask(document, objects).show()
        except (levels.LevelError, PaletteError, RuntimeError) as exc:
            _warn(str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            _warn(tr('Could not change element attributes.'))


def _warn(message):
    QtWidgets.QMessageBox.warning(Gui.getMainWindow(), tr('UniStation Change Attributes'), message)


def _apply(document, objects, patch):
    same_document(document)
    for obj in objects:
        if document.getObject(getattr(obj, "Name", "")) is not obj:
            raise levels.LevelError(tr('The selected objects or document changed'))
        reason = whole_object_error(obj)
        if reason:
            raise levels.LevelError(reason)
    element_attributes.apply(document, objects, patch)


class ChangeAttributesTask(ResettableCommand):
    def __init__(self, document, objects):
        self.document = document
        self.objects = objects
        gui_document = Gui.activeDocument()
        self.view = gui_document.activeView() if gui_document is not None else None
        self.locator = None
        self.closed = False
        records, active = attributes.level_choices(document)
        color, self.colors = attributes.color_snapshot(document)
        weight, self.widths = attributes.weight_snapshot(document)
        self.initial_values = {"color": color, "style": attributes.active_line_style(document), "weight": weight}
        self.values = self.initial_values.copy()
        self.checks = {}
        self.pickers = {}

        self.form = QtWidgets.QWidget()
        self.form.setObjectName("UstnChangeAttributes")
        bind(self.form, 'setWindowTitle', 'UniStation Change Attributes')
        layout = QtWidgets.QVBoxLayout(self.form)
        self.fields = QtWidgets.QWidget(self.form)
        fields = QtWidgets.QGridLayout(self.fields)
        fields.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.fields)
        self.layer = QtWidgets.QComboBox(self.fields)
        for level in records:
            self.layer.addItem(_color_icon(self.colors[level.color_index]), level.name, level.identifier)
        self.initial_layer = self.layer.findData(active.identifier)
        self.layer.setCurrentIndex(self.initial_layer)
        self.layer.currentIndexChanged.connect(self.changed)
        self.add_row(fields, 0, "level", QT_TRANSLATE_NOOP('UniStation', 'Level'), self.layer)
        for row, field, label in ((1, "color", 'Color'),
                                  (2, "style", QT_TRANSLATE_NOOP('UniStation', 'Style')),
                                  (3, "weight", QT_TRANSLATE_NOOP('UniStation', 'Weight'))):
            button = QtWidgets.QToolButton(self.fields)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            button.setIconSize(QtCore.QSize(42, 18))
            button.setMinimumWidth(120)
            self.pickers[field] = button
            self.add_row(fields, row, field, label, button)
            self.refresh_picker(field)

        self.install_picker("color", ColorPanel, 'Color', self.load_color)
        self.install_picker("style", LineStylePanel, 'Line style', lambda panel: panel.load(self.values["style"]))
        self.install_picker("weight", LineWeightPanel, 'Line weight',
                            lambda panel: panel.load(self.values["weight"], self.widths))
        self.notice = QtWidgets.QLabel(self.form)
        self.notice.setWordWrap(True)
        self.notice.hide()
        layout.addWidget(self.notice)
        self.confirm = translated_button('Apply') if objects else translated_button('Select element…')
        self.confirm.setEnabled(False)
        self.confirm.clicked.connect(self.submit)
        layout.addWidget(self.confirm)
        self.reset_button = translated_button('Reset')
        self.reset_button.setObjectName("unistation_reset")
        self.reset_button.clicked.connect(self.send_reset)
        layout.addWidget(self.reset_button)

    def show(self):
        global _current
        Gui.Control.showDialog(self)
        _current = self
        App.addDocumentObserver(self)
        self.form.destroyed.connect(self.form_destroyed)

    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Close

    def isAllowedAlterDocument(self):
        return False

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterSelection(self):
        return self.locator is not None

    def slotActivateDocument(self, document):
        if document is not self.document:
            QtCore.QTimer.singleShot(0, self.cancel)

    slotCreatedDocument = slotActivateDocument

    def slotDeletedDocument(self, document):
        if document is self.document:
            QtCore.QTimer.singleShot(0, self.cancel)

    def send_reset(self):
        from unistation.gui import reset
        reset(expected=self.locator or self, source="task")

    def reset_step(self):
        self.values = self.initial_values.copy()
        for field, check in self.checks.items():
            with QtCore.QSignalBlocker(check):
                check.setChecked(False)
            picker = self.layer if field == "level" else self.pickers[field]
            picker.setEnabled(False)
        with QtCore.QSignalBlocker(self.layer):
            self.layer.setCurrentIndex(self.initial_layer)
        for field in self.pickers:
            self.refresh_picker(field)
        self.update_controls()

    def stop(self):
        global _current
        if self.closed:
            return False
        self.closed = True
        _current = None
        App.removeDocumentObserver(self)
        if self.locator is not None:
            self.locator.stop()
            self.locator = None
        return True

    def cancel(self):
        if self.stop():
            Gui.Control.closeDialog()

    def reject(self):
        self.stop()
        return True

    def form_destroyed(self, _object=None):
        self.stop()

    def add_row(self, layout, row, field, label, picker):
        check = QtWidgets.QCheckBox(self.fields)
        bind(check, 'setText', label)
        bind(picker, 'setAccessibleName', label)
        check.setObjectName("UstnChange_" + field)
        picker.setEnabled(False)
        check.toggled.connect(picker.setEnabled)
        check.toggled.connect(self.changed)
        self.checks[field] = check
        layout.addWidget(check, row, 0)
        layout.addWidget(picker, row, 1)

    def install_picker(self, field, panel_type, title, load):
        button = self.pickers[field]
        menu = QtWidgets.QMenu(button)

        def choose(value):
            self.values[field] = value
            self.refresh_picker(field)
            self.changed()
            menu.close()

        if field == "color":
            direct = menu.addAction(tr('Keep RGB'))
            direct.triggered.connect(lambda: choose(KEEP_RGB))
        panel = panel_type(choose, menu.close, menu, title=title)
        item = QtWidgets.QWidgetAction(menu)
        item.setDefaultWidget(panel)
        menu.addAction(item)
        menu.aboutToShow.connect(lambda: load(panel))
        button.setMenu(menu)
        button.setPopupMode(QtWidgets.QToolButton.InstantPopup)

    def load_color(self, panel):
        index = self.values["color"]
        panel.load(self.colors, attributes.DEFAULT_COLOR_INDEX if index == KEEP_RGB else index)

    def refresh_picker(self, field):
        button = self.pickers[field]
        value = self.values[field]
        icon = QtGui.QIcon()
        if value == attributes.BY_LEVEL:
            text = tr('By level')
        elif field == "color":
            text = tr('Keep RGB') if value == KEEP_RGB else str(value)
            if value != KEEP_RGB:
                icon = _color_icon(self.colors[value])
        elif field == "style":
            text = tr(STYLE_LABELS[value])
            icon = _line_style_icon(value, button.palette(), sample_width=36)
        else:
            text = str(value)
            icon = weight_icon(self.widths[value], button.palette(), height=18, sample_width=36)
        button.setText(text)
        button.setIcon(icon)

    def changed(self, _value=None):
        self.accepted_input()
        self.update_controls()

    def update_controls(self):
        self.notice.hide()
        self.confirm.setEnabled(self.locator is None and any(check.isChecked() for check in self.checks.values()))
        if self.checks["color"].isChecked():
            try:
                if any(color_drift(obj, self.colors) for obj in self.objects):
                    self.notice.setText(tr('Color changed outside UniStation'))
                    self.notice.show()
            except PaletteError:
                # A malformed color is diagnosed by the selected edit on Apply.
                pass

    def patch(self):
        choices = {"level": self.layer.currentData(), **self.values}
        return AttributePatch(**{field: value for field, value in choices.items()
                                 if self.checks[field].isChecked()})

    def submit(self):
        if self.closed or not self.confirm.isEnabled():
            return
        patch = self.patch()
        if self.objects:
            self.apply_to(self.objects, patch)
            return
        try:
            same_document(self.document)
            self.locator = begin(self.document, whole_object_error, lambda targets: self.apply_to(targets, patch),
                                 task=self)
            self.accepted_input()
            self.fields.setEnabled(False)
            self.confirm.setEnabled(False)
            self.notice.setText(tr('Point to an object.'))
            self.notice.show()
        except (PaletteError, RuntimeError, LocateError) as exc:
            self.show_error(str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            self.show_error(tr('Could not change element attributes.'))

    def locate_finished(self, session):
        if self.closed or session is not self.locator:
            return
        self.locator = None
        if not session.accepted:
            self.cancel()
            return
        self.fields.setEnabled(True)
        self.changed()

    def apply_to(self, objects, patch):
        if self.closed:
            return
        try:
            _apply(self.document, objects, patch)
        except (levels.LevelError, PaletteError, RuntimeError) as exc:
            self.show_error(str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            self.show_error(tr('Could not change element attributes.'))
        else:
            self.cancel()

    def show_error(self, message):
        self.notice.setText(message)
        self.notice.show()
