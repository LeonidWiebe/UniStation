"""Scrollable weight-index picker; document writes belong to its controller."""

from unistation.i18n import (bind, tr, translated_dialog_button, translated_label)

from PySide import QtCore, QtGui, QtWidgets

from unistation.line_weights import COUNT


class LineWeightPanel(QtWidgets.QWidget):
    def __init__(self, accept, cancel, parent):
        super().__init__(parent)
        self.accept = accept
        self.cancel = cancel
        self.widths = None
        self.previous = None
        self.setMinimumWidth(320)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(translated_label('Line weight of new elements'))
        row = QtWidgets.QHBoxLayout()
        row.addWidget(translated_label('Index:'))
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(0, COUNT - 1)
        bind(self.spin, 'setAccessibleName', 'Active line weight index')
        row.addWidget(self.spin)
        row.addStretch()
        layout.addLayout(row)
        self.detail = QtWidgets.QLabel()
        layout.addWidget(self.detail)
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setFixedHeight(320)
        content = QtWidgets.QWidget()
        choices = QtWidgets.QVBoxLayout(content)
        choices.setContentsMargins(0, 0, 0, 0)
        choices.setSpacing(2)
        self.buttons = []
        for index in range(COUNT):
            button = QtWidgets.QToolButton()
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
            button.setIconSize(QtCore.QSize(64, 40))
            button.setMinimumHeight(44)
            button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            button.setCheckable(True)
            bind(button, 'setAccessibleName', 'Line weight index {0}', index)
            button.clicked.connect(lambda checked=False, chosen=index: self.accept(chosen))
            choices.addWidget(button)
            self.buttons.append(button)
        self.scroll.setWidget(content)
        layout.addWidget(self.scroll)
        self.error = QtWidgets.QLabel()
        self.error.setWordWrap(True)
        self.error.setMaximumWidth(360)
        layout.addWidget(self.error)
        buttons = QtWidgets.QDialogButtonBox()
        self.ok = translated_dialog_button(buttons, 'OK', QtWidgets.QDialogButtonBox.AcceptRole)
        translated_dialog_button(buttons, 'Cancel', QtWidgets.QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.confirm)
        buttons.rejected.connect(self.cancel)
        layout.addWidget(buttons)
        self.spin.valueChanged.connect(self.show_index)
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
                    else:
                        self.confirm()
                return True
        return super().eventFilter(watched, event)

    def load(self, index, widths):
        self.widths = widths
        self.previous = None
        self.error.hide()
        self.ok.setEnabled(True)
        self.spin.setEnabled(True)
        for value, button in enumerate(self.buttons):
            button.setEnabled(True)
            button.setChecked(False)
            button.setText("{0}   —   {1:g} px".format(value, widths[value]))
            button.setIcon(weight_icon(widths[value], self.palette(), height=40))
        self.spin.setValue(index)
        self.show_index(index)

    def show_index(self, index):
        if self.widths is None:
            return
        if self.previous is not None:
            self.buttons[self.previous].setChecked(False)
        self.buttons[index].setChecked(True)
        bind(self.detail, 'setText', 'Index {0}: screen width {1:g} px', index, self.widths[index])
        self.scroll.ensureWidgetVisible(self.buttons[index])
        self.previous = index

    def focus_index(self):
        self.spin.setFocus()
        self.spin.selectAll()
        self.scroll.ensureWidgetVisible(self.buttons[self.spin.value()])

    def confirm(self):
        if self.widths is not None and self.ok.isEnabled():
            self.spin.interpretText()
            self.accept(self.spin.value())

    def show_error(self, message):
        self.widths = None
        self.spin.setEnabled(False)
        self.ok.setEnabled(False)
        for button in self.buttons:
            button.setEnabled(False)
            button.setChecked(False)
        bind(self.detail, 'setText', '')
        self.error.setText(message)
        self.error.show()


def weight_icon(width, palette, height=24, sample_width=64):
    """Toolbar samples fit their icon box; model LineWidth is not clamped here."""
    pixmap = QtGui.QPixmap(sample_width, height)
    pixmap.fill(QtCore.Qt.transparent)
    if width is not None:
        painter = QtGui.QPainter(pixmap)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(QtGui.QPen(palette.color(QtGui.QPalette.ButtonText),
                                     min(width, height - 6), QtCore.Qt.SolidLine,
                                     QtCore.Qt.FlatCap))
            painter.drawLine(3, height // 2, sample_width - 3, height // 2)
        finally:
            painter.end()
    return QtGui.QIcon(pixmap)
