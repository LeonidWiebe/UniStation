"""Commands and the 16 by 16 palette dialog. Document edits stay in palette.py."""

from unistation.i18n import (QT_TRANSLATE_NOOP, bind, tr, translated_dialog_button, translated_label)

import sys

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from unistation.palette import (
    PaletteError,
    assign_index,
    color_drift,
    colors_for_display,
    classify_palettes,
    indexed_objects,
    load_palette_file,
    release_rgb,
    replace_palette,
    same_document,
    write_palette_file,
)


def register():
    Gui.addCommand("UniStation_IndexedColor", IndexedColorCommand())
    Gui.addCommand("UniStation_EditPalette", EditPaletteCommand())
    Gui.addCommand("UniStation_ImportPalette", ImportPaletteCommand())
    Gui.addCommand("UniStation_ExportPalette", ExportPaletteCommand())


class IndexedColorCommand:
    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP('UniStation_IndexedColor', 'Indexed color'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_IndexedColor', 'Assign a palette index to selected objects or locate one object with the cursor'),
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        _run(_indexed_color)


class EditPaletteCommand:
    def GetResources(self):
        return {
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


def _indexed_color(document):
    if Gui.Selection.getSelectionEx(document.Name):
        _open_indexed_color(document, _targets())
        return
    from unistation.locate import LocateError, begin
    from unistation.transform_gui import whole_object_error

    def accept(objects):
        try:
            _open_indexed_color(document, objects)
        except PaletteError as exc:
            _warn(str(exc))
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")
            _critical(tr('The palette command failed. The document should contain no partial changes.'))

    try:
        begin(document, whole_object_error, accept)
    except LocateError as exc:
        raise PaletteError(str(exc)) from exc
    except Exception as exc:
        raise PaletteError(tr('Element locate did not start. ') + str(exc)) from exc


def _open_indexed_color(document, objects):
    from unistation.transform_gui import whole_object_error

    same_document(document)
    live = []
    for obj in objects:
        if document.getObject(getattr(obj, "Name", "")) is not obj:
            raise PaletteError(tr('The object was deleted. Color was not assigned.'))
        reason = whole_object_error(obj)
        if reason:
            raise PaletteError(_selection_message(reason))
        live.append(obj)
    _palette, colors = colors_for_display(document)
    ColorDialog(document, live, colors, _window()).exec_()


def _edit_palette(document):
    _palette, colors = colors_for_display(document)
    dialog = PaletteEditor(document, colors, _palette is not None, _window())
    dialog.exec_()


def _import_palette(document):
    classify_palettes(document)
    path, _selected = QtWidgets.QFileDialog.getOpenFileName(
        _window(),
        tr('Load palette'),
        "",
        tr('UniStation palette (*.ustnpalette.json *.uspalette.json)'),
    )
    if not path:
        return
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
    if not _confirm(text):
        return
    same_document(document)
    replace_palette(document, colors)


def _export_palette(document):
    palette, colors = colors_for_display(document)
    if palette is None:
        _info(
            tr(('The document has no palette or indexed objects. The built-in UniStation snapshot will be saved. '
             'No document object is created.'))
        )
        name = "UniStation"
    else:
        name = None
    path = _save_path()
    if not path:
        return
    same_document(document)
    palette_now, colors_now = colors_for_display(document)
    if (palette is None) != (palette_now is None):
        raise PaletteError(tr('The palette state changed. The file was not written.'))
    write_palette_file(path, colors_now if palette_now is not None else colors, name)


def _targets():
    from unistation.transform_gui import selected_objects

    try:
        return selected_objects()
    except RuntimeError as exc:
        raise PaletteError(_selection_message(str(exc))) from exc


def _selection_message(text):
    known = {
        tr('Select whole objects before starting Move or Copy'):
            tr('Select one or more whole objects.'),
        tr('Select whole objects, not edges or vertices'):
            tr('Select whole objects, not edges or vertices.'),
        tr('Select objects from the active document only'):
            tr('Select objects from the active document only.'),
        tr('Supported: independent Draft wires/circles/arcs and simple Part features'):
            tr('Independent Draft wires, circles, arcs and simple Part features are supported.'),
    }
    if text in known:
        return known[text]
    if text.startswith(tr('Attached, nested or dependent objects are not supported yet:')):
        return tr('Nested, dependent or attached objects cannot be colored yet: ') + text.split(":", 1)[1].strip()
    if text.startswith(tr('Invalid shape:')):
        return tr('Invalid shape: ') + text.split(":", 1)[1].strip()
    return tr('The objects are unsuitable for indexed color. ') + text


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


def _confirm(text):
    answer = QtWidgets.QMessageBox.question(
        _window(),
        "UniStation",
        text,
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        QtWidgets.QMessageBox.No,
    )
    return answer == QtWidgets.QMessageBox.Yes


def _warn(text):
    QtWidgets.QMessageBox.warning(_window(), "UniStation", text)


def _info(text):
    QtWidgets.QMessageBox.information(_window(), "UniStation", text)


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
        save = translated_dialog_button(buttons, 'Save', QtWidgets.QDialogButtonBox.ActionRole)
        save_as = translated_dialog_button(buttons, 'Save as', QtWidgets.QDialogButtonBox.ActionRole)
        buttons.addButton(QtWidgets.QDialogButtonBox.Close)
        save.clicked.connect(self.save_document)
        save_as.clicked.connect(self.save_file_as)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._refresh()

    def _show_notice(self):
        if self.stored:
            bind(self.notice, 'setText', 'The document palette is shown. Color edits stay in this window until Save is pressed. Save '
                 'writes the palette to the open document and updates indexed objects. Save as writes a separate '
                 'file.')
        else:
            bind(self.notice, 'setText', 'The built-in snapshot is shown; it is not saved in the document yet. Save writes it to the open '
                 'document. Save as writes a separate file.')

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
        self._refresh()
        self._show_detail(index)

    def save_document(self):
        try:
            _require_idle()
            same_document(self.document)
            replace_palette(self.document, self.colors, tr('UniStation: save palette'))
        except PaletteError as exc:
            QtWidgets.QMessageBox.warning(self, "UniStation", str(exc))
            return
        self.stored = True
        self._show_notice()
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
        bind(self.detail, 'setText', 'The file was written. This button did not change the document.')


class ColorDialog(QtWidgets.QDialog):
    """Modal chooser. Opening it does not create a palette or touch the document."""

    def __init__(self, document, objects, colors, parent=None):
        super().__init__(parent)
        self.document = document
        self.colors = colors
        self.user_chose = False
        self._loading = True
        bind(self, 'setWindowTitle', 'Indexed color')
        self.setModal(True)
        indexes = []
        drifted = False
        for obj in objects:
            mode = _mode(obj)
            if mode == "PaletteIndex":
                indexes.append(_stored_index(obj))
                if color_drift(obj, colors):
                    drifted = True
        self.mixed = len(set(indexes)) > 1 or (indexes and len(indexes) != len(objects))
        initial = indexes[0] if indexes and not self.mixed else 7

        layout = QtWidgets.QVBoxLayout(self)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(2)
        self.buttons = []
        for index, rgb in enumerate(colors):
            button = QtWidgets.QToolButton()
            button.setFixedSize(30, 30)
            button.setAutoRaise(False)
            bind(button, 'setToolTip', 'Index {0} — RGB {1}, {2}, {3}', index, *rgb)
            button.clicked.connect(lambda checked=False, chosen=index: self.choose(chosen))
            grid.addWidget(button, index // 16, index % 16)
            self.buttons.append(button)
        layout.addLayout(grid)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(translated_label('Index'))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(0, 255)
        self.spin.setValue(initial)
        self.spin.valueChanged.connect(self._spin_changed)
        row.addWidget(self.spin)
        self.sample = QtWidgets.QLabel()
        self.sample.setFixedSize(48, 24)
        row.addWidget(self.sample)
        self.detail = QtWidgets.QLabel()
        row.addWidget(self.detail, 1)
        layout.addLayout(row)

        self.notice = QtWidgets.QLabel()
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        if self.mixed:
            bind(self.notice, 'setText', 'Mixed')
        if drifted:
            warning = translated_label('Color changed outside UniStation')
            warning.setWordWrap(True)
            layout.addWidget(warning)

        buttons = QtWidgets.QDialogButtonBox()
        apply_index = translated_dialog_button(buttons, 'Apply index', QtWidgets.QDialogButtonBox.AcceptRole)
        keep_rgb = translated_dialog_button(buttons, 'Keep RGB', QtWidgets.QDialogButtonBox.ActionRole)
        translated_dialog_button(buttons, 'Cancel', QtWidgets.QDialogButtonBox.RejectRole)
        apply_index.clicked.connect(self._apply)
        keep_rgb.clicked.connect(self._release)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._loading = False
        self._show_index(initial, announce=not self.mixed)

    def choose(self, index):
        self.user_chose = True
        self._loading = True
        self.spin.setValue(index)
        self._loading = False
        self._show_index(index, announce=True)

    def _spin_changed(self, index):
        if self._loading:
            return
        self.user_chose = True
        self._show_index(index, announce=True)

    def _show_index(self, index, announce):
        for position, button in enumerate(self.buttons):
            selected = announce and position == index
            button.setText(str(index) if selected else "")
            button.setStyleSheet(_swatch_style(self.colors[position], selected))
        red, green, blue = self.colors[index]
        self.sample.setStyleSheet(
            "background-color: #%02x%02x%02x; border: 1px solid palette(mid);" % (red, green, blue)
        )
        if announce:
            bind(self.detail, 'setText', 'Index {0} — RGB {1}, {2}, {3}', index, red, green, blue)
            if self.notice.text() == tr('Mixed'):
                bind(self.notice, 'setText', '')
        else:
            bind(self.detail, 'setText', 'An index is not inferred from a matching RGB color.')

    def _apply(self):
        if self.mixed and not self.user_chose:
            _warn(tr('Choose one index. The selected objects currently have different indices.'))
            return
        try:
            _require_idle()
            same_document(self.document)
            assign_index(self.document, _targets(), int(self.spin.value()))
        except PaletteError as exc:
            _warn(str(exc))
            return
        self.accept()

    def _release(self):
        try:
            _require_idle()
            same_document(self.document)
            release_rgb(self.document, _targets())
        except PaletteError as exc:
            _warn(str(exc))
            return
        self.accept()


def _mode(obj):
    if "UstnColorMode" not in getattr(obj, "PropertiesList", []):
        return None
    mode = obj.UstnColorMode
    return None if mode is None else str(mode)


def _stored_index(obj):
    value = obj.UstnColorIndex
    if isinstance(value, (list, tuple)):
        value = value[0]
    if isinstance(value, bool):
        raise PaletteError(tr('Index “') + obj.Label + tr('” is damaged.'))
    index = int(value)
    if index < 0 or index > 255:
        raise PaletteError(tr('Index “') + obj.Label + tr('” is outside the range 0..255.'))
    return index


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
