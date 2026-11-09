"""Active color/style/weight toolbar with a disabled future layer selector."""

from unistation.i18n import (QT_TRANSLATE_NOOP, bind, tr, translated_button, translated_dialog_button, translated_label)

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

from unistation import attributes
from unistation import line_weights
from unistation.line_weight_widgets import LineWeightPanel, weight_icon
from unistation.palette import PaletteError, same_document
from unistation.palette_gui import _require_idle, _swatch_style


COMMAND = "UniStation_ActiveColor"
STYLE_COMMAND = "UniStation_ActiveLineStyle"
WEIGHT_COMMAND = "UniStation_ActiveLineWeight"
LAYER_COMMAND = "UniStation_ActiveLayer"
STYLE_LABELS = {
    "Solid": QT_TRANSLATE_NOOP('UniStation', 'Solid'),
    "Dashed": QT_TRANSLATE_NOOP('UniStation', 'Dashed'),
    "Dotted": QT_TRANSLATE_NOOP('UniStation', 'Dotted'),
    "Dashdot": QT_TRANSLATE_NOOP('UniStation', 'Dash-dot'),
}
_controller = None


def register():
    Gui.addCommand(LAYER_COMMAND, PendingLayerCommand())
    Gui.addCommand(COMMAND, ActiveColorCommand())
    Gui.addCommand(STYLE_COMMAND, ActiveLineStyleCommand())
    Gui.addCommand(WEIGHT_COMMAND, ActiveLineWeightCommand())


def activate():
    global _controller
    deactivate()
    _controller = AttributesController()
    # Workbench activation must finish building the native toolbar first.
    _controller.schedule_refresh()


def deactivate():
    global _controller
    if _controller is not None:
        _controller.stop()
        _controller = None


def _can_choose():
    if _controller is None or App.ActiveDocument is None:
        return False
    try:
        _require_attribute_access()
        return True
    except Exception:
        return False


def _require_attribute_access():
    from unistation.gui import drawing_session
    session = drawing_session()
    if session is not None:
        if getattr(App, "activeDraftCommand", None) or not session.axisflow.isActive():
            raise PaletteError(tr('The current drawing command is no longer available.'))
        return session
    # Other commands/tasks retain the original idle requirement.
    _require_idle()
    return None


def _sync_drawing(document):
    from unistation.gui import drawing_session
    session = drawing_session()
    if session is not None and session.backend.doc is document:
        session.backend.refresh_active_attributes()


def _check_context(expected):
    if _require_attribute_access() is not expected:
        raise PaletteError(tr('The command changed. Reopen the attribute picker.'))


class PendingLayerCommand:
    def GetResources(self):
        return {
            "MenuText": QT_TRANSLATE_NOOP('UniStation_ActiveLayer', 'Layer'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_ActiveLayer', 'Layer selection — not available yet'),
        }

    def IsActive(self):
        return False

    def Activated(self):
        pass


class ActiveColorCommand:
    def GetResources(self):
        return {
            "CmdType": "ForEdit NoTransaction",
            "MenuText": QT_TRANSLATE_NOOP('UniStation_ActiveColor', 'Active indexed color'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_ActiveColor', 'Color of new UniStation elements: choose a document palette index'),
        }

    def IsActive(self):
        return _can_choose()

    def Activated(self):
        if _controller is not None:
            _controller.open_popup()


class ActiveLineStyleCommand:
    def GetResources(self):
        return {
            "CmdType": "ForEdit NoTransaction",
            "MenuText": QT_TRANSLATE_NOOP('UniStation_ActiveLineStyle', 'Active line style'),
            "ToolTip": QT_TRANSLATE_NOOP('UniStation_ActiveLineStyle', 'Line style of new UniStation elements'),
        }

    def IsActive(self):
        return _can_choose()

    def Activated(self):
        if _controller is not None:
            _controller.open_style_popup()


class ActiveLineWeightCommand:
    def GetResources(self):
        return {"CmdType": "ForEdit NoTransaction",
                "MenuText": QT_TRANSLATE_NOOP('UniStation_ActiveLineWeight', 'Active line weight'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_ActiveLineWeight', 'Choose the line weight index for new UniStation elements: 0..31')}

    def IsActive(self):
        return _can_choose()

    def Activated(self):
        if _controller is not None:
            _controller.open_weight_popup()


class ColorPanel(QtWidgets.QWidget):
    """Selection is provisional until OK; this widget never edits geometry."""

    def __init__(self, accept, cancel, parent):
        super().__init__(parent)
        self.accept = accept
        self.cancel = cancel
        self.colors = None
        self.previous = None
        layout = QtWidgets.QVBoxLayout(self)
        self.heading = translated_label('Color of new elements')
        layout.addWidget(self.heading)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(translated_label('Index:'))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(0, 255)
        bind(self.spin, 'setAccessibleName', 'Active color index')
        row.addWidget(self.spin)
        self.sample = QtWidgets.QLabel()
        self.sample.setFixedSize(36, 22)
        row.addWidget(self.sample)
        row.addStretch()
        layout.addLayout(row)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(1)
        self.buttons = []
        for index in range(256):
            button = QtWidgets.QToolButton()
            button.setFixedSize(20, 20)
            button.setAutoRaise(False)
            bind(button, 'setAccessibleName', 'Index {0}', index)
            button.clicked.connect(lambda checked=False, chosen=index: self.spin.setValue(chosen))
            grid.addWidget(button, index // 16, index % 16)
            self.buttons.append(button)
        layout.addLayout(grid)
        self.detail = QtWidgets.QLabel()
        layout.addWidget(self.detail)
        self.error = QtWidgets.QLabel()
        self.error.setWordWrap(True)
        self.error.setMaximumWidth(340)
        layout.addWidget(self.error)
        buttons = QtWidgets.QDialogButtonBox()
        self.ok = translated_dialog_button(buttons, 'OK', QtWidgets.QDialogButtonBox.AcceptRole)
        translated_dialog_button(buttons, 'Cancel', QtWidgets.QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.cancel)
        layout.addWidget(buttons)
        self.spin.valueChanged.connect(self.show_index)
        # Keep confirmation/cancellation in the popup instead of application shortcuts.
        self.installEventFilter(self)
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.ShortcutOverride, QtCore.QEvent.KeyPress):
            key = event.key()
            if key in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                event.accept()
                if event.type() == QtCore.QEvent.KeyPress:
                    if key == QtCore.Qt.Key_Escape:
                        self.cancel()
                    elif isinstance(watched, QtWidgets.QAbstractButton):
                        watched.click()
                    else:
                        self.accept()
                return True
        return super().eventFilter(watched, event)

    def load(self, colors, index):
        self.colors = colors
        self.previous = None
        self.error.hide()
        self.ok.setEnabled(True)
        self.spin.setEnabled(True)
        for value, button in enumerate(self.buttons):
            rgb = colors[value]
            button.setEnabled(True)
            bind(button, 'setToolTip', 'Index %d — RGB %d, %d, %d', percent=(value, *rgb))
            button.setStyleSheet(_swatch_style(rgb, False))
            button.setText("")
        self.spin.setValue(index)
        self.show_index(index)

    def show_error(self, message):
        self.colors = None
        self.spin.setEnabled(False)
        self.ok.setEnabled(False)
        for button in self.buttons:
            button.setEnabled(False)
            button.setStyleSheet("")
            button.setText("")
            bind(button, 'setToolTip', '')
        self.sample.clear()
        self.sample.setStyleSheet("")
        bind(self.detail, 'setText', '')
        self.error.setText(message)
        self.error.show()

    def show_index(self, index):
        if self.colors is None:
            return
        if self.previous is not None:
            previous = self.buttons[self.previous]
            previous.setText("")
            previous.setStyleSheet(_swatch_style(self.colors[self.previous], False))
        rgb = self.colors[index]
        self.buttons[index].setStyleSheet(_swatch_style(rgb, True))
        self.buttons[index].setText("•")
        self.sample.setStyleSheet("background-color: rgb(%d,%d,%d); border: 1px solid #808080;" % rgb)
        bind(self.detail, 'setText', 'Index %d   RGB %d, %d, %d', percent=(index, *rgb))
        self.previous = index


class LineStylePanel(QtWidgets.QWidget):
    """Four discrete choices; a click confirms, dismissal leaves settings intact."""

    def __init__(self, accept, cancel, parent):
        super().__init__(parent)
        self.accept = accept
        self.cancel = cancel
        self.current = None
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(translated_label('Style of new elements'))
        self.buttons = {}
        for style in attributes.LINE_STYLES:
            button = QtWidgets.QToolButton()
            bind(button, "setText", STYLE_LABELS[style])
            bind(button, "setAccessibleName", STYLE_LABELS[style])
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            button.setIconSize(QtCore.QSize(64, 24))
            button.setMinimumWidth(280)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, chosen=style: self.accept(chosen))
            layout.addWidget(button)
            self.buttons[style] = button
        self.error = QtWidgets.QLabel()
        self.error.setWordWrap(True)
        self.error.setMaximumWidth(360)
        layout.addWidget(self.error)
        cancel_button = translated_button('Cancel')
        cancel_button.clicked.connect(self.cancel)
        layout.addWidget(cancel_button)
        self.installEventFilter(self)
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QtCore.QEvent.ShortcutOverride, QtCore.QEvent.KeyPress):
            if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                event.accept()
                if event.type() == QtCore.QEvent.KeyPress:
                    if event.key() == QtCore.Qt.Key_Escape:
                        self.cancel()
                    elif isinstance(watched, QtWidgets.QAbstractButton):
                        watched.click()
                return True
        return super().eventFilter(watched, event)

    def load(self, style):
        self.current = style
        self.error.hide()
        for value, button in self.buttons.items():
            button.setEnabled(True)
            button.setChecked(value == style)
            button.setIcon(_line_style_icon(value, self.palette()))

    def show_error(self, message):
        self.current = None
        for button in self.buttons.values():
            button.setEnabled(False)
            button.setChecked(False)
        self.error.setText(message)
        self.error.show()


class AttributesController(QtCore.QObject):
    def __init__(self):
        super().__init__(Gui.getMainWindow())
        self.running = True
        self.document = None
        self.context = None
        self.initial_index = None
        self.initial_colors = None
        self.buttons = []
        self.style_buttons = []
        self.style_document = None
        self.style_context = None
        self.initial_style = None
        self.weight_buttons = []
        self.weight_document = None
        self.weight_context = None
        self.initial_weight = None
        self.layer_buttons = []
        # Empty, unreachable menu provides the native dropdown arrow only.
        self.layer_menu = QtWidgets.QMenu(Gui.getMainWindow())
        self.layer_menu.setObjectName("UstnActiveLayerPlaceholder")
        self.menu = QtWidgets.QMenu(Gui.getMainWindow())
        self.menu.setObjectName("UstnActiveColorPopup")
        self.menu.setToolTipsVisible(True)
        self.panel = ColorPanel(self.apply, self.menu.close, self.menu)
        widget_action = QtWidgets.QWidgetAction(self.menu)
        widget_action.setDefaultWidget(self.panel)
        self.menu.addAction(widget_action)
        self.menu.aboutToShow.connect(self.prepare)
        self.menu.aboutToHide.connect(self.forget_document)
        self.style_menu = QtWidgets.QMenu(Gui.getMainWindow())
        self.style_menu.setObjectName("UstnActiveLineStylePopup")
        self.style_panel = LineStylePanel(self.apply_style, self.style_menu.close, self.style_menu)
        style_widget_action = QtWidgets.QWidgetAction(self.style_menu)
        style_widget_action.setDefaultWidget(self.style_panel)
        self.style_menu.addAction(style_widget_action)
        self.style_menu.aboutToShow.connect(self.prepare_style)
        self.style_menu.aboutToHide.connect(self.forget_style_document)
        self.weight_menu = QtWidgets.QMenu(Gui.getMainWindow())
        self.weight_menu.setObjectName("UstnActiveLineWeightPopup")
        self.weight_panel = LineWeightPanel(self.apply_weight, self.weight_menu.close, self.weight_menu)
        weight_action = QtWidgets.QWidgetAction(self.weight_menu)
        weight_action.setDefaultWidget(self.weight_panel)
        self.weight_menu.addAction(weight_action)
        self.weight_menu.aboutToShow.connect(self.prepare_weight)
        self.weight_menu.aboutToHide.connect(self.forget_weight_document)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh)
        App.addDocumentObserver(self)

    def schedule_refresh(self):
        if self.running:
            self.timer.start(0)

    def stop(self):
        self.running = False
        App.removeDocumentObserver(self)
        self.timer.stop()
        self.menu.close()
        self.style_menu.close()
        self.weight_menu.close()
        self.layer_menu.close()
        for button in self.buttons + self.style_buttons + self.weight_buttons + self.layer_buttons:
            try:
                if button.menu() in (self.menu, self.style_menu, self.weight_menu, self.layer_menu):
                    button.setMenu(None)
                    button.setPopupMode(QtWidgets.QToolButton.DelayedPopup)
            except RuntimeError:
                pass  # FreeCAD may already have rebuilt a customized toolbar.
        self.menu.deleteLater()
        self.style_menu.deleteLater()
        self.weight_menu.deleteLater()
        self.layer_menu.deleteLater()
        self.deleteLater()

    def actions(self, command=COMMAND):
        return Gui.Command.get(command).getAction()

    def attach_buttons(self, actions, style_actions, weight_actions):
        self.buttons = []
        self.style_buttons = []
        self.weight_buttons = []
        for toolbar in Gui.getMainWindow().findChildren(QtWidgets.QToolBar):
            for action in toolbar.actions():
                if action not in actions and action not in style_actions and action not in weight_actions:
                    continue
                button = toolbar.widgetForAction(action)
                if isinstance(button, QtWidgets.QToolButton):
                    is_style = action in style_actions
                    is_weight = action in weight_actions
                    button.setMenu(self.weight_menu if is_weight else self.style_menu if is_style else self.menu)
                    button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
                    button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
                    # Use the native size hint for the current label, without the
                    # former wide minimums. Popup choices retain their larger samples.
                    button.setMinimumWidth(0)
                    button.setIconSize(QtCore.QSize(32 if is_style or is_weight else 24,
                                                   toolbar.iconSize().height()))
                    if is_weight:
                        self.weight_buttons.append(button)
                    elif is_style:
                        self.style_buttons.append(button)
                    else:
                        self.buttons.append(button)

    def attach_layer_buttons(self):
        actions = self.actions(LAYER_COMMAND)
        self.layer_buttons = []
        for action in actions:
            action.setEnabled(False)
        for toolbar in Gui.getMainWindow().findChildren(QtWidgets.QToolBar):
            for action in toolbar.actions():
                if action not in actions:
                    continue
                button = toolbar.widgetForAction(action)
                if isinstance(button, QtWidgets.QToolButton):
                    button.setMenu(self.layer_menu)
                    button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
                    button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
                    button.setMinimumWidth(0)
                    button.setEnabled(False)
                    self.layer_buttons.append(button)

    def refresh(self):
        if not self.running:
            return
        try:
            self.attach_layer_buttons()
            actions = self.actions()
            style_actions = self.actions(STYLE_COMMAND)
            weight_actions = self.actions(WEIGHT_COMMAND)
            self.attach_buttons(actions, style_actions, weight_actions)
            document = App.ActiveDocument
            if document is None:
                text, rgb = "—", None
                tip = tr('Open a document to choose the active color.')
            else:
                try:
                    index, colors = attributes.color_snapshot(document)
                    text, rgb = str(index), colors[index]
                    tip = (tr('Active color of new elements: index %d, RGB %d, %d, %d.\nAvailable before or during drawing commands.') % (index, *rgb))
                except Exception as exc:
                    text, rgb = "?", None
                    tip = tr('Active color is unavailable: ') + str(exc)
            icon = _color_icon(rgb)
            for action in actions:
                action.setIcon(icon)
                action.setIconText(text)
                action.setToolTip(tip)
            for button in self.buttons:
                # Font-relative gap after the swatch; stored values and action
                # labels remain unpadded.
                button.setText("\u2002" + text)
            if document is None:
                style, style_text = None, "—"
                style_tip = tr('Open a document to choose the active line style.')
            else:
                try:
                    style = attributes.active_line_style(document)
                    style_text = tr(STYLE_LABELS[style])
                    style_tip = (tr('Active style of new elements: ') + style_text
                                 + tr('.\nAvailable before or during drawing commands.'))
                except Exception as exc:
                    style, style_text = None, "?"
                    style_tip = tr('Active line style is unavailable: ') + str(exc)
            style_icon = _line_style_icon(style, Gui.getMainWindow().palette(), sample_width=32)
            for action in style_actions:
                action.setIcon(style_icon)
                action.setIconText(style_text)
                action.setToolTip(style_tip)
            for button in self.style_buttons:
                button.setText("\u2002" + style_text)
            if document is None:
                weight_text, width = "—", None
                weight_tip = tr('Open a document to choose the active line weight.')
            else:
                try:
                    index, widths = attributes.weight_snapshot(document)
                    weight_text, width = str(index), widths[index]
                    weight_tip = (tr('Active line weight: index {0}, screen width {1:g} px.\nAvailable before or during drawing commands.').format(index, width))
                except Exception as exc:
                    weight_text, width = "?", None
                    weight_tip = tr('Active line weight is unavailable: ') + str(exc)
            icon = weight_icon(width, Gui.getMainWindow().palette(), sample_width=32)
            for action in weight_actions:
                action.setIcon(icon)
                action.setIconText(weight_text)
                action.setToolTip(weight_tip)
            for button in self.weight_buttons:
                button.setText("\u2002" + weight_text)
            if document is not None:
                _sync_drawing(document)
        except Exception as exc:
            App.Console.PrintError(tr('UniStation: Attributes toolbar: ') + str(exc) + "\n")

    def open_popup(self):
        try:
            _require_attribute_access()
            if App.ActiveDocument is None:
                raise PaletteError(tr('No active document.'))
            button = next((item for item in self.buttons if item.isVisible()), None)
            point = button.mapToGlobal(QtCore.QPoint(0, button.height())) if button else QtGui.QCursor.pos()
            self.menu.popup(point)
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")

    def prepare(self):
        self.forget_document()
        try:
            context = _require_attribute_access()
            document = App.ActiveDocument
            if document is None:
                raise PaletteError(tr('No active document.'))
            index, colors = attributes.color_snapshot(document)
            self.document = document
            self.context = context
            self.initial_index = index
            self.initial_colors = colors
            self.panel.load(colors, index)
            QtCore.QTimer.singleShot(0, self.focus_index)
        except Exception as exc:
            self.panel.show_error(str(exc))

    def open_style_popup(self):
        try:
            _require_attribute_access()
            if App.ActiveDocument is None:
                raise PaletteError(tr('No active document.'))
            button = next((item for item in self.style_buttons if item.isVisible()), None)
            point = button.mapToGlobal(QtCore.QPoint(0, button.height())) if button else QtGui.QCursor.pos()
            self.style_menu.popup(point)
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")

    def prepare_style(self):
        self.forget_style_document()
        try:
            context = _require_attribute_access()
            document = App.ActiveDocument
            if document is None:
                raise PaletteError(tr('No active document.'))
            style = attributes.active_line_style(document)
            self.style_document = document
            self.style_context = context
            self.initial_style = style
            self.style_panel.load(style)
            QtCore.QTimer.singleShot(0, self.focus_style)
        except Exception as exc:
            self.style_panel.show_error(str(exc))

    def focus_style(self):
        if self.running and self.style_menu.isVisible() and self.style_document is not None:
            self.style_panel.buttons[self.initial_style].setFocus()

    def forget_style_document(self):
        self.style_document = None
        self.style_context = None
        self.initial_style = None

    def apply_style(self, style):
        if self.style_document is None:
            return
        try:
            _check_context(self.style_context)
            document = self.style_document
            same_document(document)
            if attributes.active_line_style(document) != self.initial_style:
                raise PaletteError(tr('The active style changed. Reopen the list.'))
            attributes.set_active_line_style(document, style)
            _sync_drawing(document)
            self.style_menu.close()
            self.schedule_refresh()
        except Exception as exc:
            self.forget_style_document()
            self.style_panel.show_error(str(exc))
            App.Console.PrintError(tr('UniStation: active line style: ') + str(exc) + "\n")

    def open_weight_popup(self):
        try:
            _require_attribute_access()
            if App.ActiveDocument is None:
                raise PaletteError(tr('No active document.'))
            button = next((item for item in self.weight_buttons if item.isVisible()), None)
            point = button.mapToGlobal(QtCore.QPoint(0, button.height())) if button else QtGui.QCursor.pos()
            self.weight_menu.popup(point)
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")

    def prepare_weight(self):
        self.forget_weight_document()
        try:
            context = _require_attribute_access()
            document = App.ActiveDocument
            if document is None:
                raise PaletteError(tr('No active document.'))
            snapshot = attributes.weight_snapshot(document)
            self.weight_document = document
            self.weight_context = context
            self.initial_weight = snapshot
            self.weight_panel.load(*snapshot)
            QtCore.QTimer.singleShot(0, self.focus_weight)
        except Exception as exc:
            self.weight_panel.show_error(str(exc))

    def focus_weight(self):
        if self.running and self.weight_menu.isVisible() and self.weight_document is not None:
            self.weight_panel.focus_index()

    def forget_weight_document(self):
        self.weight_document = None
        self.weight_context = None
        self.initial_weight = None

    def apply_weight(self, index):
        if self.weight_document is None:
            return
        try:
            _check_context(self.weight_context)
            document = self.weight_document
            same_document(document)
            if attributes.weight_snapshot(document) != self.initial_weight:
                raise PaletteError(tr('The active line weight or table changed. Reopen the picker.'))
            attributes.set_active_line_weight(document, index)
            _sync_drawing(document)
            self.weight_menu.close()
            self.schedule_refresh()
        except Exception as exc:
            self.forget_weight_document()
            self.weight_panel.show_error(str(exc))
            App.Console.PrintError(tr('UniStation: active line weight: ') + str(exc) + "\n")

    def focus_index(self):
        if self.running and self.menu.isVisible() and self.document is not None:
            self.panel.spin.setFocus()
            self.panel.spin.selectAll()

    def forget_document(self):
        self.document = None
        self.context = None
        self.initial_index = None
        self.initial_colors = None

    def apply(self):
        if self.document is None or not self.panel.ok.isEnabled():
            return
        try:
            _check_context(self.context)
            document = self.document
            same_document(document)
            index, colors = attributes.color_snapshot(document)
            if index != self.initial_index or colors != self.initial_colors:
                raise PaletteError(tr('The active settings or palette changed. Reopen the color picker.'))
            self.panel.spin.interpretText()
            chosen = self.panel.spin.value()
            attributes.set_active_color(document, chosen)
            _sync_drawing(document)
            self.menu.close()
            self.schedule_refresh()
        except Exception as exc:
            self.forget_document()
            self.panel.show_error(str(exc))
            App.Console.PrintError(tr('UniStation: active color: ') + str(exc) + "\n")

    def changed(self, document=None):
        if self.document is not None and (document is None or document is self.document):
            self.menu.close()
        if self.style_document is not None and (document is None or document is self.style_document):
            self.style_menu.close()
        if self.weight_document is not None and (document is None or document is self.weight_document):
            self.weight_menu.close()
        if document is None or document is App.ActiveDocument:
            self.schedule_refresh()

    def slotActivateDocument(self, document):
        self.changed()

    def slotCreatedDocument(self, document):
        self.changed()

    def slotDeletedDocument(self, document):
        self.changed()

    def slotUndoDocument(self, document):
        self.changed(document)

    def slotRedoDocument(self, document):
        self.changed(document)

    def slotCreatedObject(self, obj):
        self.changed(obj.Document)

    def slotDeletedObject(self, obj):
        self.changed(obj.Document)

    def slotChangedObject(self, obj, prop):
        if prop in (attributes.SCHEMA, attributes.COLOR_INDEX, attributes.LINE_STYLE, attributes.LINE_WEIGHT,
                    line_weights.SCHEMA, line_weights.WIDTHS, line_weights.INDEX,
                    "UstnPaletteSchema", "UstnPaletteData", "UstnColorMode"):
            self.changed(obj.Document)


def _line_style_icon(style, palette, sample_width=64):
    """A readable UI sample, not a promise of dash lengths in model units."""
    pixmap = QtGui.QPixmap(sample_width, 24)
    pixmap.fill(QtCore.Qt.transparent)
    if style is not None:
        pen_styles = {"Solid": QtCore.Qt.SolidLine, "Dashed": QtCore.Qt.DashLine,
                      "Dotted": QtCore.Qt.DotLine, "Dashdot": QtCore.Qt.DashDotLine}
        painter = QtGui.QPainter(pixmap)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(QtGui.QPen(palette.color(QtGui.QPalette.ButtonText), 1.5,
                                     pen_styles[style], QtCore.Qt.FlatCap))
            painter.drawLine(3, 12, sample_width - 3, 12)
        finally:
            painter.end()
    return QtGui.QIcon(pixmap)


def _color_icon(rgb):
    pixmap = QtGui.QPixmap(24, 24)
    pixmap.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pixmap)
    try:
        painter.fillRect(2, 2, 20, 20, QtGui.QColor(*(rgb or (160, 160, 160))))
        painter.setPen(QtGui.QColor("#404040"))
        painter.drawRect(1, 1, 21, 21)
        painter.setPen(QtGui.QColor("#ffffff"))
        painter.drawRect(2, 2, 19, 19)
    finally:
        painter.end()
    return QtGui.QIcon(pixmap)
