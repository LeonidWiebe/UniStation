"""Commands and the 16 by 16 palette dialog. Document edits stay in palette.py."""

from unistation.i18n import (QT_TRANSLATE_NOOP, bind, tr, translated_dialog_button, translated_label)

import sys
from pathlib import Path

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from unistation.palette import (
    PaletteError,
    colors_for_display,
    classify_palettes,
    indexed_objects,
    load_palette_file,
    replace_palette,
    same_document,
    write_palette_file,
)


def register():
    Gui.addCommand("UniStation_EditPalette", EditPaletteCommand())
    Gui.addCommand("UniStation_ImportPalette", ImportPaletteCommand())
    Gui.addCommand("UniStation_ExportPalette", ExportPaletteCommand())


class EditPaletteCommand:
    def GetResources(self):
        return {
            "Pixmap": str(Path(__file__).resolve().parent / "icons" / "edit-palette.svg"),
            "MenuText": QT_TRANSLATE_NOOP('UniStation_EditPalette', 'Edit palette'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_EditPalette', 'Open the document palette and double-click to edit a color'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        _run(_edit_palette)


class ImportPaletteCommand:
    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP('UniStation_ImportPalette', 'Load palette'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_ImportPalette', 'Replace the 256 document palette colors from a .ustnpalette.json file'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        _run(_import_palette)


class ExportPaletteCommand:
    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP('UniStation_ExportPalette', 'Save palette'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_ExportPalette', 'Write the current document palette to a .ustnpalette.json file'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        _run(_export_palette)


def _run(action):
    try:
        _require_idle()
        document = App.ActiveDocument
        if document is None:
            raise PaletteError(tr('No active document.'))
        same_document(document)
        action(document)
    except PaletteError as exc:
        _warn(str(exc))
    except Exception as exc:
        App.Console.PrintError("UniStation: " + str(exc) + "\n")
        _critical(tr('The palette command failed. The document should contain no partial changes.'))


def _edit_palette(document):
    _palette, colors = colors_for_display(document)
    dialog = PaletteEditor(document, colors, _palette is not None, _window())
    dialog.exec_()


def _import_palette(document, parent=None, *, discard_draft=False):
    classify_palettes(document)
    path, _selected = QtWidgets.QFileDialog.getOpenFileName(
        parent or _window(),
        tr('Load palette'),
        "",
        tr('UniStation palette (*.ustnpalette.json *.uspalette.json)'),
    )
    if not path:
        return None
    colors = load_palette_file(path)
    same_document(document)
    palette = classify_palettes(document)
    count = len(indexed_objects(document))
    if palette is None:
        text = (
            tr(('A palette will be created in the document from the file. Indices are preserved; colors will be '
             'recalculated for this many objects: '))
            + str(count)
            + tr('. Direct-RGB objects and other documents are unchanged.')
        )
    else:
        text = (
            tr(('All 256 palette colors will be replaced. Indices are preserved; colors will be recalculated for '
             'this many objects: '))
            + str(count)
            + tr('. Direct-RGB objects and other documents are unchanged.')
        )
    if discard_draft:
        text += "\n\n" + tr('The pending edits in this window will be discarded.')
    if not _confirm(text, parent):
        return None
    same_document(document)
    replace_palette(document, colors)
    return colors


def _export_palette(document, parent=None):
    palette, colors = colors_for_display(document)
    if palette is None:
        _info(
            tr(('The document has no palette or indexed objects. The built-in UniStation snapshot will be saved. '
             'No document object is created.')),
            parent,
        )
        name = "UniStation"
    else:
        name = None
    path = _save_path(parent)
    if not path:
        return False
    same_document(document)
    palette_now, colors_now = colors_for_display(document)
    if (palette is None) != (palette_now is None):
        raise PaletteError(tr('The palette state changed. The file was not written.'))
    write_palette_file(path, colors_now if palette_now is not None else colors, name)
    return True


def _require_idle():
    from unistation import gui
    from unistation.locate import is_active

    if gui._session is not None or is_active():
        raise PaletteError(tr('Finish the current UniStation command first.'))
    if getattr(App, "activeDraftCommand", None):
        raise PaletteError(tr('Finish the current Draft command first.'))
    if Gui.Control.activeDialog():
        raise PaletteError(tr('Finish the current task first.'))
    module = sys.modules.get("AxisFlow")
    if module is None:
        return
    probe = getattr(module, "isActive", None)
    if not callable(probe):
        return
    try:
        active = bool(probe())
    except Exception as exc:
        raise PaletteError(
            tr('Could not check the AxisFlow session. AxisFlow state was not changed.')
        ) from exc
    if active:
        raise PaletteError(tr('Finish the AxisFlow session first.'))


def _save_path(parent=None):
    dialog = QtWidgets.QFileDialog(parent or _window(), tr('Save palette'))
    dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
    dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
    dialog.setNameFilter(tr('UniStation palette (*.ustnpalette.json)'))
    dialog.setDefaultSuffix("ustnpalette.json")
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return None
    selected = dialog.selectedFiles()
    return selected[0] if selected else None


def _confirm(text, parent=None):
    answer = QtWidgets.QMessageBox.question(
        parent or _window(),
        "UniStation",
        text,
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        QtWidgets.QMessageBox.No,
    )
    return answer == QtWidgets.QMessageBox.Yes


def _warn(text):
    QtWidgets.QMessageBox.warning(_window(), "UniStation", text)


def _info(text, parent=None):
    QtWidgets.QMessageBox.information(parent or _window(), "UniStation", text)


def _critical(text):
    QtWidgets.QMessageBox.critical(_window(), "UniStation", text)


def _window():
    return Gui.getMainWindow()


class SwatchButton(QtWidgets.QToolButton):
    """Color cell. The index is shown on mouse press and follows a drag."""

    def __init__(self, index, editor):
        super().__init__()
        self.index = index
        self.editor = editor

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.editor.show_index(self.index)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            self.editor.show_index_at(_global_point(event))
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.editor.edit_color(self.index)
        event.accept()


def _global_point(event):
    getter = getattr(event, "globalPosition", None)
    if callable(getter):
        point = getter()
        to_point = getattr(point, "toPoint", None)
        return to_point() if callable(to_point) else point
    return event.globalPos()


class PaletteEditor(QtWidgets.QDialog):
    """Edit colors in memory. A cell change does not write the document or a file."""

    def __init__(self, document, colors, stored, parent=None):
        super().__init__(parent)
        self.document = document
        self.colors = [tuple(rgb) for rgb in colors]
        self.applied_colors = tuple(self.colors)
        self.stored = stored
        self.selected = None
        bind(self, 'setWindowTitle', 'Palette editor')
        self.setModal(True)
        layout = QtWidgets.QVBoxLayout(self)
        self.notice = QtWidgets.QLabel()
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self._show_notice()
        hint = translated_label('Press the mouse button to show an index; hold and drag across cells. Double-click changes the '
             'color in this window only.')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(2)
        self.buttons = []
        for index, rgb in enumerate(self.colors):
            button = SwatchButton(index, self)
            button.setFixedSize(40, 40)
            button.setAutoRaise(False)
            grid.addWidget(button, index // 16, index % 16)
            self.buttons.append(button)
        layout.addLayout(grid)
        self.detail = translated_label('Press a color to see its index.')
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        buttons = QtWidgets.QDialogButtonBox()
        load = translated_dialog_button(buttons, 'Load', QtWidgets.QDialogButtonBox.ActionRole)
        save = translated_dialog_button(buttons, 'Save', QtWidgets.QDialogButtonBox.ActionRole)
        self.save_draft_button = translated_dialog_button(buttons, 'Save draft…', QtWidgets.QDialogButtonBox.ActionRole)
        apply = translated_dialog_button(buttons, 'Apply to document', QtWidgets.QDialogButtonBox.ActionRole)
        load.setObjectName("UstnPaletteLoad")
        save.setObjectName("UstnPaletteSave")
        apply.setObjectName("UstnPaletteApply")
        self.save_draft_button.setEnabled(False)
        buttons.addButton(QtWidgets.QDialogButtonBox.Close)
        load.clicked.connect(self.load_file)
        save.clicked.connect(self.save_file)
        self.save_draft_button.clicked.connect(self.save_file_as)
        apply.clicked.connect(self.save_document)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._refresh()

    def _show_notice(self):
        if self.stored:
            bind(self.notice, 'setText', 'Apply to document updates the drawing. Save exports the document palette.')
        else:
            bind(self.notice, 'setText', 'The built-in palette is shown. Apply to document installs it in the drawing.')

    def _mark_applied(self):
        self.stored = True
        self.applied_colors = tuple(self.colors)
        self.save_draft_button.setEnabled(False)
        self._show_notice()

    def show_index(self, index):
        if self.selected == index:
            return
        self.selected = index
        self._refresh()
        self._show_detail(index)

    def show_index_at(self, global_pos):
        for button in self.buttons:
            if button.rect().contains(button.mapFromGlobal(global_pos)):
                self.show_index(button.index)
                return

    def _refresh(self):
        for index, button in enumerate(self.buttons):
            selected = self.selected == index
            button.setText(str(index) if selected else "")
            button.setStyleSheet(_swatch_style(self.colors[index], selected, 16))
            bind(button, 'setToolTip', 'Index {0} — RGB {1}. Double-click to edit.',
                 index, ", ".join(str(channel) for channel in self.colors[index]))

    def _show_detail(self, index):
        red, green, blue = self.colors[index]
        bind(self.detail, 'setText', 'Index {0} — RGB {1}, {2}, {3}', index, red, green, blue)

    def edit_color(self, index):
        self.selected = index
        current = self.colors[index]
        chosen = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(current[0], current[1], current[2]),
            self,
            tr('Index {0}').format(index),
        )
        if not chosen.isValid():
            self._refresh()
            self._show_detail(index)
            return
        self.colors[index] = (chosen.red(), chosen.green(), chosen.blue())
        self.save_draft_button.setEnabled(tuple(self.colors) != self.applied_colors)
        self._refresh()
        self._show_detail(index)

    def load_file(self):
        try:
            _require_idle()
            same_document(self.document)
            colors = _import_palette(self.document, self, discard_draft=tuple(self.colors) != self.applied_colors)
        except PaletteError as exc:
            QtWidgets.QMessageBox.warning(self, "UniStation", str(exc))
            return
        if colors is None:
            return
        self.colors[:] = colors
        self._mark_applied()
        self._refresh()
        bind(self.detail, 'setText', 'The palette was loaded into the document.')

    def save_file(self):
        try:
            _require_idle()
            same_document(self.document)
            written = _export_palette(self.document, self)
        except PaletteError as exc:
            QtWidgets.QMessageBox.warning(self, "UniStation", str(exc))
            return
        if written:
            bind(self.detail, 'setText', 'The palette was saved to a file.')

    def save_document(self):
        try:
            _require_idle()
            same_document(self.document)
            replace_palette(self.document, self.colors, tr('UniStation: save palette'))
        except PaletteError as exc:
            QtWidgets.QMessageBox.warning(self, "UniStation", str(exc))
            return
        self._mark_applied()
        bind(self.detail, 'setText', 'The palette was saved to the document. Indexed objects use the new colors.')

    def save_file_as(self):
        path = _save_path(self)
        if not path:
            return
        try:
            write_palette_file(path, self.colors)
        except PaletteError as exc:
            QtWidgets.QMessageBox.warning(self, "UniStation", str(exc))
            return
        bind(self.detail, 'setText', 'The draft was saved to a file.')


def _swatch_style(rgb, selected, font_size=8):
    red, green, blue = rgb
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255.0
    ink = "#000000" if luminance > 0.62 else "#ffffff"
    border = "2px solid " + ink if selected else "1px solid #5c5c5c"
    weight = "bold" if selected else "normal"
    return (
        "QToolButton { background-color: #%02x%02x%02x; color: %s; border: %s; "
        "font-weight: %s; font-size: %dpx; padding: 0px; }"
        % (red, green, blue, ink, border, weight, font_size)
    )
