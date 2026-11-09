"""Category-based UniStation settings dialog, independent of document geometry."""

import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from unistation import preferences
from unistation.i18n import (
    QT_TRANSLATE_NOOP, bind, tr, translated_dialog_button, translated_label,
)


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("unistation_preferences")
        bind(self, "setWindowTitle", "UniStation Settings")
        self.resize(740, 440)
        layout = QtWidgets.QVBoxLayout(self)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        layout.addWidget(splitter, 1)

        self.categories = QtWidgets.QTreeWidget(splitter)
        self.categories.setObjectName("unistation_settings_categories")
        self.categories.setHeaderHidden(True)
        self.categories.setRootIsDecorated(False)
        self.category = QtWidgets.QTreeWidgetItem(self.categories)
        self.category.setData(0, QtCore.Qt.UserRole, 0)
        self.operations_category = QtWidgets.QTreeWidgetItem(self.categories)
        self.operations_category.setData(0, QtCore.Qt.UserRole, 1)
        self.pages = QtWidgets.QStackedWidget(splitter)
        page = QtWidgets.QWidget()
        self.pages.addWidget(page)
        page_layout = QtWidgets.QVBoxLayout(page)
        heading = translated_label("Mouse Settings")
        font = heading.font()
        font.setBold(True)
        heading.setFont(font)
        page_layout.addWidget(heading)

        group = QtWidgets.QGroupBox()
        bind(group, "setTitle", "Button assignments")
        page_layout.addWidget(group)
        form = QtWidgets.QFormLayout(group)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form.addRow(translated_label("Left mouse button:"),
                    translated_label("FreeCAD / AxisFlow"))
        form.addRow(translated_label("Middle mouse button:"),
                    translated_label("FreeCAD navigation"))
        self.right_button = QtWidgets.QComboBox()
        self.right_button.setObjectName("unistation_right_button_action")
        self.right_button.addItem("", preferences.NATIVE)
        self.right_button.addItem("", preferences.RESET)
        label = translated_label("Right mouse button:")
        label.setBuddy(self.right_button)
        form.addRow(label, self.right_button)
        self.right_button.setCurrentIndex(
            self.right_button.findData(preferences.right_button_action()))
        note = translated_label(
            "Reset is handled by the current command. First Reset returns to the previous "
            "input state; another Reset without a new point exits the command. "
            "Wire and Arc remove the last entered point.")
        note.setWordWrap(True)
        page_layout.addWidget(note)
        scope = translated_label(
            "The assignment applies to a single right-click in the 3D view while a "
            "UniStation command is active, including element locate. Other buttons and "
            "idle right-clicks keep their current behavior.")
        scope.setWordWrap(True)
        page_layout.addWidget(scope)
        page_layout.addStretch()

        operations_page = QtWidgets.QWidget()
        self.pages.addWidget(operations_page)
        operations_layout = QtWidgets.QVBoxLayout(operations_page)
        operations_heading = translated_label("Operations")
        operations_heading.setFont(font)
        operations_layout.addWidget(operations_heading)
        self.auto_select = QtWidgets.QCheckBox()
        self.auto_select.setObjectName("unistation_auto_select_result")
        bind(self.auto_select, "setText", "Automatically select elements after operations")
        self.auto_select.setChecked(preferences.auto_select_result())
        operations_layout.addWidget(self.auto_select)
        operations_note = translated_label(
            "Applies after creating Line, Wire, Circle or Arc, and after Move or Copy. "
            "When off, the result is left unselected. Cancel and Reset keep their selection behavior.")
        operations_note.setWordWrap(True)
        operations_layout.addWidget(operations_note)
        operations_layout.addStretch()
        self.categories.currentItemChanged.connect(self.select_category)
        self.categories.setCurrentItem(self.category)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([190, 550])

        buttons = QtWidgets.QDialogButtonBox()
        ok = translated_dialog_button(buttons, "OK", QtWidgets.QDialogButtonBox.AcceptRole)
        apply = translated_dialog_button(buttons, "Apply", QtWidgets.QDialogButtonBox.ApplyRole)
        translated_dialog_button(buttons, "Cancel", QtWidgets.QDialogButtonBox.RejectRole)
        ok.setDefault(True)
        apply.clicked.connect(self.apply)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.retranslate()

    def retranslate(self):
        self.category.setText(0, tr("Mouse Settings"))
        self.operations_category.setText(0, tr("Operations"))
        self.right_button.setItemText(0, tr("Default action"))
        self.right_button.setItemText(1, tr("Reset"))

    def select_category(self, current, previous):
        if current is not None:
            self.pages.setCurrentIndex(int(current.data(0, QtCore.Qt.UserRole)))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.LanguageChange:
            self.retranslate()

    def apply(self):
        try:
            preferences.save_settings(self.right_button.currentData(), self.auto_select.isChecked())
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, tr("UniStation Settings"),
                tr("Could not save UniStation settings: {0}").format(str(exc)))
            return False
        return True

    def accept(self):
        if self.apply():
            super().accept()


class PreferencesCommand:
    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP("UniStation_Preferences", "Settings..."),
            "ToolTip": QT_TRANSLATE_NOOP("UniStation_Preferences", "Configure UniStation mouse and operation settings"),
        }

    def IsActive(self):
        from unistation.gui import active_input
        return active_input() is None and not Gui.Control.activeDialog()

    def Activated(self):
        if self.IsActive():
            dialog = PreferencesDialog(Gui.getMainWindow())
            dialog.exec_()


def register():
    Gui.addCommand("UniStation_Preferences", PreferencesCommand())
