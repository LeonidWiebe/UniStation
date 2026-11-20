"""UniStation command and sheet settings for direct PDF output."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtWidgets

from unistation.i18n import QT_TRANSLATE_NOOP, bind, tr, translated_dialog_button, translated_label
from unistation.levels import LevelError
from unistation.palette import PaletteError, same_document
from unistation.palette_gui import _require_idle
from unistation.plot import PAPER_SIZES, PlotError, PlotSettings, export_pdf


COMMAND = "UniStation_PlotPdf"


def register():
    Gui.addCommand(COMMAND, PlotPdfCommand())


class PlotPdfCommand:
    def GetResources(self):
        return {
            "Pixmap": "Std_PrintPdf",
            "CmdType": "NoTransaction",
            "MenuText": QT_TRANSLATE_NOOP('UniStation_PlotPdf', 'Plot to PDF…'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_PlotPdf', 'Export a vector PDF using the level print flags'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        window = Gui.getMainWindow()
        title = tr('Plot to PDF')
        try:
            _require_idle()
            document = App.ActiveDocument
            if document is None:
                return
            selection = Gui.Selection.getSelectionEx()
            dialog = PlotDialog(bool(selection), window)
            if not dialog.exec_():
                return
            objects = None
            if dialog.scope.currentData() == "selection":
                if any(item.SubElementNames for item in selection):
                    raise PlotError(tr('Select whole objects from the active document.'))
                objects = tuple(item.Object for item in selection)
            same_document(document)
            target = QtWidgets.QFileDialog(window, title)
            target.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
            target.setFileMode(QtWidgets.QFileDialog.AnyFile)
            target.setNameFilter(tr('PDF files (*.pdf)'))
            target.setDefaultSuffix("pdf")
            if not target.exec_():
                return
            _require_idle()
            count = export_pdf(document, target.selectedFiles()[0], dialog.settings(), objects)
            window.statusBar().showMessage(tr('PDF saved. Objects plotted: {}').format(count), 8000)
        except (PlotError, LevelError, PaletteError, OSError) as exc:
            QtWidgets.QMessageBox.warning(window, title, str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            QtWidgets.QMessageBox.critical(window, title, tr('Could not export the plot to PDF.'))


class PlotDialog(QtWidgets.QDialog):
    def __init__(self, have_selection, parent):
        super().__init__(parent)
        bind(self, 'setWindowTitle', 'Plot to PDF')
        form = QtWidgets.QFormLayout(self)

        self.scope = QtWidgets.QComboBox(self)
        self.scope.addItem(tr('Entire drawing'), "drawing")
        if have_selection:
            self.scope.addItem(tr('Selected objects'), "selection")
            self.scope.setCurrentIndex(1)
        form.addRow(translated_label('Objects to plot'), self.scope)

        self.paper = QtWidgets.QComboBox(self)
        self.paper.addItems(PAPER_SIZES)
        form.addRow(translated_label('Paper size'), self.paper)

        self.orientation = QtWidgets.QComboBox(self)
        self.orientation.addItem(tr('Landscape'), True)
        self.orientation.addItem(tr('Portrait'), False)
        form.addRow(translated_label('Orientation'), self.orientation)

        self.fit = QtWidgets.QCheckBox(self)
        bind(self.fit, 'setText', 'Fit to page')
        self.fit.setChecked(True)
        form.addRow(self.fit)

        self.scale = QtWidgets.QDoubleSpinBox(self)
        self.scale.setRange(0.01, 100000.0)
        self.scale.setValue(1.0)
        self.scale.setPrefix("1 : ")
        self.scale.setEnabled(False)
        self.fit.toggled.connect(self.scale.setDisabled)
        form.addRow(translated_label('Scale'), self.scale)

        self.margin = QtWidgets.QDoubleSpinBox(self)
        self.margin.setRange(0.0, 999.0)
        self.margin.setValue(10.0)
        bind(self.margin, 'setSuffix', ' mm')
        form.addRow(translated_label('Margin'), self.margin)

        buttons = QtWidgets.QDialogButtonBox(self)
        translated_dialog_button(buttons, 'Export PDF…', QtWidgets.QDialogButtonBox.AcceptRole)
        translated_dialog_button(buttons, 'Cancel', QtWidgets.QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def settings(self):
        return PlotSettings(self.paper.currentText(), self.orientation.currentData(),
                            self.margin.value(), None if self.fit.isChecked() else self.scale.value())
