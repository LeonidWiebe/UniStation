"""Edit a document's level definitions while working in the drawing."""

from dataclasses import replace
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

from unistation import attributes, levels, line_weights
from unistation.attributes import LINE_STYLES
from unistation.attributes_gui import ColorPanel, LineStylePanel, _color_icon, _line_style_icon
from unistation.i18n import QT_TRANSLATE_NOOP, bind, tr, translated_button
from unistation.line_weight_widgets import LineWeightPanel, weight_icon
from unistation.palette import DATA_PROPERTY as PALETTE_DATA, PaletteError, colors_for_display
from unistation.palette_gui import _require_idle


COMMAND = "UniStation_LevelManager"
ASSIGN_COMMAND = "UniStation_AssignLevel"
NAME, DESCRIPTION, COLOR, STYLE, WEIGHT, DISPLAY, FREEZE, LOCK, PLOT = range(9)


def register():
    manager = LevelManagerCommand()
    Gui.addCommand(COMMAND, manager)
    App.addDocumentObserver(manager)
    Gui.addCommand(ASSIGN_COMMAND, AssignLevelCommand())


class LevelManagerCommand:
    def __init__(self):
        self.dialogs = {}

    def GetResources(self):
        return {
            "Pixmap": str(Path(__file__).resolve().parent / "icons" / "levels.svg"),
            "CmdType": "NoTransaction",
            "MenuText": QT_TRANSLATE_NOOP('UniStation_LevelManager', 'Level Manager'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_LevelManager', 'Manage the active document’s levels'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            document = App.ActiveDocument
            if document is None:
                return
            name = document.Name
            dialog = self.dialogs.get(name)
            if dialog is None:
                dialog = LevelDialog(document, Gui.getMainWindow())
                dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
                self.dialogs[name] = dialog
                dialog.finished.connect(lambda _result: self.dialogs.pop(name, None))
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
        except (levels.LevelError, PaletteError) as exc:
            QtWidgets.QMessageBox.warning(Gui.getMainWindow(), tr('Level Manager'), str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            QtWidgets.QMessageBox.critical(Gui.getMainWindow(), tr('Level Manager'),
                                           tr('Could not open the Level Manager.'))

    def slotActivateDocument(self, _document):
        for dialog in self.dialogs.values():
            dialog.schedule_refresh()

    # FreeCAD makes a new document active without emitting ActivateDocument.
    slotCreatedDocument = slotActivateDocument

    def slotDeletedDocument(self, document):
        dialog = self.dialogs.get(document.Name)
        if dialog is not None:
            dialog.reject()
        self.slotActivateDocument(document)

    def schedule_document_refresh(self, document):
        dialog = self.dialogs.get(document.Name)
        if dialog is not None:
            dialog.schedule_refresh()

    slotUndoDocument = schedule_document_refresh
    slotRedoDocument = schedule_document_refresh

    def slotChangedObject(self, obj, prop):
        if prop in (levels.DATA, PALETTE_DATA, line_weights.WIDTHS):
            self.schedule_document_refresh(obj.Document)


class AssignLevelCommand:
    def GetResources(self):
        return {
            "CmdType": "NoTransaction",
            "MenuText": QT_TRANSLATE_NOOP('UniStation_AssignLevel', 'Assign Level…'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_AssignLevel', 'Assign a level to selected elements'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None and bool(Gui.Selection.getSelectionEx())

    def Activated(self):
        from unistation.transform_gui import selected_objects, whole_object_error

        window = Gui.getMainWindow()
        title = tr('Assign Level')
        try:
            _require_idle()
            document = App.ActiveDocument
            if document is None:
                return
            objects = selected_objects(tr('Select one or more whole objects.'))
            baseline = levels.read_table(document)
            _table, records = baseline
            if records is None:
                raise levels.LevelError(tr('Create the level table in the Level Manager first.'))

            names = {level.name: level.identifier for level in records}
            identifiers = list(names.values())
            assigned = {levels.element_level_id(obj) or levels.DEFAULT_ID for obj in objects}
            label = tr('Layer')
            if not assigned.issubset(identifiers):
                label = tr('Select a replacement for the missing level.')
            _levels, active = attributes.level_choices(document)
            current = next(iter(assigned)) if len(assigned) == 1 else active.identifier
            index = identifiers.index(current if current in identifiers else active.identifier)
            name, accepted = QtWidgets.QInputDialog.getItem(window, title, label, list(names), index, False)
            if not accepted:
                return
            _require_idle()
            for obj in objects:
                error = whole_object_error(obj)
                if error:
                    raise levels.LevelError(error)
            levels.assign_elements(document, baseline, objects, names[name])
        except (levels.LevelError, PaletteError, RuntimeError) as exc:
            QtWidgets.QMessageBox.warning(window, title, str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            QtWidgets.QMessageBox.critical(window, title, tr('Could not assign the level.'))


class NameDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, report_error, parent):
        super().__init__(parent)
        self.report_error = report_error

    def setModelData(self, editor, model, index):
        used = {model.data(model.index(row, NAME), QtCore.Qt.DisplayRole).strip().casefold()
                for row in range(model.rowCount()) if row != index.row()}
        try:
            name = levels.validate_name(editor.text(), used)
        except levels.LevelError as exc:
            self.report_error(str(exc))
            return
        model.setData(index, name, QtCore.Qt.EditRole)
        self.report_error("")


class LevelDialog(QtWidgets.QDialog):
    def __init__(self, document, parent):
        super().__init__(parent)
        self.document = document
        self.baseline = levels.read_table(document)
        self.records = {}
        _palette, self.colors = colors_for_display(document)
        _weights, self.widths = line_weights.widths_for_display(document)

        self.setObjectName("UstnLevelManager")
        self.setModal(False)
        bind(self, 'setWindowTitle', 'Level Manager — {}', document.Label)
        self.refresh_timer = QtCore.QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.timeout.connect(self.refresh_from_document)
        self.finished.connect(self.refresh_timer.stop)
        self.resize(970, 430)
        layout = QtWidgets.QVBoxLayout(self)
        self.picker = QtWidgets.QMenu(self)
        self.name_error = QtWidgets.QLabel(self)
        self.name_error.setWordWrap(True)
        self.name_error.hide()

        self.table = QtWidgets.QTableWidget(0, PLOT + 1, self)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setIconSize(QtCore.QSize(46, 20))
        self.table.verticalHeader().hide()
        self.table.setHorizontalHeaderLabels([
            tr('Name'), tr('Description'), tr('Color'), tr('Line style'), tr('Line weight'),
            tr('Global Display'), tr('Global Freeze'), tr('Lock'), tr('Plot'),
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(NAME, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(DESCRIPTION, QtWidgets.QHeaderView.Stretch)
        self.table.setColumnWidth(NAME, 170)
        self.table.setItemDelegateForColumn(NAME, NameDelegate(self.show_name_error, self.table))
        self.table.itemChanged.connect(self.update_sample)
        self.table.itemSelectionChanged.connect(self.update_actions)
        self.table.itemClicked.connect(self.open_picker)
        self.table.itemActivated.connect(self.open_picker)
        layout.addWidget(self.table)
        layout.addWidget(self.name_error)

        actions = QtWidgets.QHBoxLayout()
        add_button = translated_button('Add level')
        add_button.setAutoDefault(False)
        add_button.clicked.connect(self.add_level)
        actions.addWidget(add_button)
        self.remove_button = translated_button('Remove level')
        self.remove_button.setAutoDefault(False)
        self.remove_button.clicked.connect(self.remove_level)
        actions.addWidget(self.remove_button)
        actions.addStretch()
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save
                                             | QtWidgets.QDialogButtonBox.Apply
                                             | QtWidgets.QDialogButtonBox.Cancel, parent=self)
        self.save_button = bind(buttons.button(QtWidgets.QDialogButtonBox.Save), 'setText', 'Save')
        self.apply_button = bind(buttons.button(QtWidgets.QDialogButtonBox.Apply), 'setText', 'Apply')
        bind(buttons.button(QtWidgets.QDialogButtonBox.Cancel), 'setText', 'Cancel')
        self.apply_button.clicked.connect(self.apply)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        actions.addWidget(buttons)
        layout.addLayout(actions)
        self.populate(self.baseline[1])
        self.update_actions()

    def populate(self, records):
        selected = self.selected_name()
        identifier = selected.data(QtCore.Qt.UserRole) if selected is not None else levels.DEFAULT_ID
        self.picker.close()
        self.records = {level.identifier: level for level in records or (levels.DEFAULT_LEVEL,)}
        row = 0
        with QtCore.QSignalBlocker(self.table):
            self.table.setRowCount(0)
            for level in self.records.values():
                item = self.append_level(level)
                if level.identifier == identifier:
                    row = item.row()
        self.table.selectRow(row)

    def schedule_refresh(self):
        self.refresh_timer.start(0)

    def refresh_from_document(self):
        active = App.ActiveDocument is self.document
        self.save_button.setEnabled(active)
        self.apply_button.setEnabled(active)
        if not active:
            return
        try:
            latest = levels.read_table(self.document)
            _palette, colors = colors_for_display(self.document)
            _weights, widths = line_weights.widths_for_display(self.document)
            samples_changed = (colors, widths) != (self.colors, self.widths)
            self.colors, self.widths = colors, widths
            if latest != self.baseline:
                previous = self.baseline[1] or (levels.DEFAULT_LEVEL,)
                if (self.table.state() == QtWidgets.QAbstractItemView.EditingState
                        or self.edited_levels() != previous):
                    self.show_name_error(tr('The level table changed. Reopen the Level Manager to continue.'))
                else:
                    self.baseline = latest
                    self.populate(latest[1])
                    self.show_name_error("")
                    samples_changed = False
            if samples_changed:
                self.picker.close()
                with QtCore.QSignalBlocker(self.table):
                    for row in range(self.table.rowCount()):
                        for column in (COLOR, STYLE, WEIGHT):
                            self.set_sample(self.table.item(row, column), column)
        except (levels.LevelError, PaletteError) as exc:
            self.show_name_error(str(exc))

    def append_level(self, level):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name = QtWidgets.QTableWidgetItem(level.name)
        name.setData(QtCore.Qt.UserRole, level.identifier)
        if level.identifier == levels.DEFAULT_ID:
            font = name.font()
            font.setBold(True)
            name.setFont(font)
            name.setToolTip(tr('Default level'))
        self.table.setItem(row, NAME, name)
        self.table.setItem(row, DESCRIPTION, QtWidgets.QTableWidgetItem(level.description))
        for column, value in ((COLOR, level.color_index), (STYLE, level.line_style),
                              (WEIGHT, level.weight_index)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, value)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            item.setToolTip(tr('Open the attribute picker'))
            self.set_sample(item, column)
            self.table.setItem(row, column, item)
        for column, flag in ((DISPLAY, level.global_display), (FREEZE, level.global_freeze),
                             (LOCK, level.locked), (PLOT, level.plot)):
            item = QtWidgets.QTableWidgetItem()
            item.setCheckState(QtCore.Qt.Checked if flag else QtCore.Qt.Unchecked)
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
                          | QtCore.Qt.ItemIsUserCheckable)
            self.table.setItem(row, column, item)
        return name

    def show_name_error(self, message):
        self.name_error.setText(message)
        self.name_error.setVisible(bool(message))

    def open_picker(self, item):
        column = item.column()
        if column not in (COLOR, STYLE, WEIGHT) or self.picker.isVisible():
            return
        self.picker.clear()
        index = item.data(QtCore.Qt.EditRole)

        def choose(value):
            item.setData(QtCore.Qt.EditRole, value)
            self.picker.close()

        if column == COLOR:
            panel = ColorPanel(choose, self.picker.close, self.picker, for_level=True)
            panel.load(self.colors, index)
            focus = panel.spin
        elif column == STYLE:
            def choose_style(style):
                choose(LINE_STYLES.index(style))

            panel = LineStylePanel(choose_style, self.picker.close, self.picker, for_level=True)
            panel.load(LINE_STYLES[index])
            focus = panel.buttons[LINE_STYLES[index]]
        else:
            panel = LineWeightPanel(choose, self.picker.close, self.picker, for_level=True)
            panel.load(index, self.widths)
            focus = panel.spin
        action = QtWidgets.QWidgetAction(self.picker)
        action.setDefaultWidget(panel)
        self.picker.addAction(action)
        position = self.table.visualItemRect(item).bottomLeft()
        self.picker.popup(self.table.viewport().mapToGlobal(position))
        if column == WEIGHT:
            panel.focus_index()
        else:
            focus.setFocus()

    def set_sample(self, item, column):
        index = item.data(QtCore.Qt.EditRole)
        if column == COLOR:
            icon = _color_icon(self.colors[index])
        elif column == STYLE:
            icon = _line_style_icon(LINE_STYLES[index], self.table.palette(), 46)
        else:
            icon = weight_icon(self.widths[index], self.table.palette(), 24, 46)
        item.setIcon(icon)

    def update_sample(self, item):
        if item.column() in (COLOR, STYLE, WEIGHT):
            blocker = QtCore.QSignalBlocker(self.table)
            try:
                self.set_sample(item, item.column())
            finally:
                blocker.unblock()

    def selected_name(self):
        rows = self.table.selectionModel().selectedRows(NAME)
        return self.table.item(rows[0].row(), NAME) if rows else None

    def update_actions(self):
        item = self.selected_name()
        self.remove_button.setEnabled(item is not None and item.data(QtCore.Qt.UserRole) != levels.DEFAULT_ID)

    def add_level(self):
        self.show_name_error("")
        names = (self.table.item(row, NAME).text() for row in range(self.table.rowCount()))
        level = levels.new_level(names)
        self.records[level.identifier] = level
        item = self.append_level(level)
        self.table.setCurrentItem(item)
        self.table.selectRow(item.row())
        self.table.editItem(item)

    def remove_level(self):
        item = self.selected_name()
        if item is not None and item.data(QtCore.Qt.UserRole) != levels.DEFAULT_ID:
            identifier = item.data(QtCore.Qt.UserRole)
            try:
                if identifier in levels.used_level_ids(self.document):
                    raise levels.LevelError(tr('Cannot remove a level assigned to elements: {}').format(item.text()))
            except levels.LevelError as exc:
                self.show_name_error(str(exc))
                return
            del self.records[identifier]
            self.table.removeRow(item.row())
            self.show_name_error("")
            self.update_actions()

    def edited_level(self, row):
        name = self.table.item(row, NAME)
        original = self.records[name.data(QtCore.Qt.UserRole)]
        return replace(original, name=name.text().strip(),
                       description=self.table.item(row, DESCRIPTION).text(),
                       color_index=self.table.item(row, COLOR).data(QtCore.Qt.EditRole),
                       line_style=self.table.item(row, STYLE).data(QtCore.Qt.EditRole),
                       weight_index=self.table.item(row, WEIGHT).data(QtCore.Qt.EditRole),
                       global_display=self.table.item(row, DISPLAY).checkState() == QtCore.Qt.Checked,
                       global_freeze=self.table.item(row, FREEZE).checkState() == QtCore.Qt.Checked,
                       locked=self.table.item(row, LOCK).checkState() == QtCore.Qt.Checked,
                       plot=self.table.item(row, PLOT).checkState() == QtCore.Qt.Checked)

    def edited_levels(self):
        return tuple(self.edited_level(row) for row in range(self.table.rowCount()))

    def apply(self):
        if self.table.state() == QtWidgets.QAbstractItemView.EditingState:
            self.table.setFocus()
        try:
            _require_idle()
            records = self.edited_levels()
            levels.save_table(self.document, self.baseline, records)
            self.baseline = levels.read_table(self.document)
            self.records = {level.identifier: level for level in records}
        except (levels.LevelError, PaletteError) as exc:
            self.show_name_error(str(exc))
            return False
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            self.show_name_error(tr('Could not save the level table.'))
            return False
        self.show_name_error("")
        return True

    def accept(self):
        if self.apply():
            super().accept()
