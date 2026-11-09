"""FreeCAD/Qt boundary. The AxisFlow API is checked before taking input."""

from unistation.i18n import (QT_TRANSLATE_NOOP, bind, tr, translated_button)
import FreeCAD as App
import math
from pathlib import Path
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets
from unistation.line import LineSession
from unistation.wire import WireSession
from unistation.circle import CircleSession
from unistation.arc import ArcSession
from unistation.transform import TransformSession
from unistation.input_events import InputEvent, InputType

_session = None
_ICON_DIR = Path(__file__).resolve().parent / "icons"
_LINE_PATTERNS = {"Solid": 0xffff, "Dashed": 0xf00f,
                  "Dotted": 0x0f0f, "Dashdot": 0xff88}


def active_input():
    """Return the live UniStation point/transform or element-locate session."""
    if _session is not None and not _session.closed:
        return _session
    from unistation.locate import active_session
    return active_session()


def drawing_session():
    """Live creating command that may change active attributes in-place."""
    session = _session
    if (type(session) in (LineSession, WireSession, CircleSession, ArcSession)
            and not session.closed and session.backend.alive()):
        return session
    return None


def reset(expected=None, source="command"):
    """Deliver a logical Reset event; its meaning belongs to the active command."""
    command = active_input()
    if command is None or (expected is not None and command is not expected):
        return
    try:
        return command.handle_input(InputEvent(InputType.RESET, source))
    except Exception as exc:
        App.Console.PrintError(tr('UniStation Reset failed: {0}').format(str(exc)) + "\n")
        cancel()


def cancel():
    """Unconditional teardown for Close, explicit Cancel and lifecycle guards."""
    from unistation.locate import cancel as cancel_locate
    cancel_locate()
    if _session is not None:
        _session.cancel()


class Backend:
    tolerance = 1e-7

    def __init__(self, axisflow, active_color_index=None, active_line_style=None,
                 active_line_weight=None):
        from pivy import coin
        self.axisflow = axisflow
        self.doc = App.ActiveDocument
        self.active_color_index = active_color_index
        self.active_line_style = active_line_style
        self.active_line_weight = active_line_weight
        preview_rgb = (1.0, 0.65, 0.1)
        preview_pattern = None
        preview_width = None
        # Resolve read-only display values before acquiring scenegraph resources.
        # Move/Copy do not supply active attributes and retain their ghost styling.
        if active_color_index is not None:
            from unistation.palette import colors_for_display
            _palette, colors = colors_for_display(self.doc)
            preview_rgb = tuple(channel / 255.0 for channel in colors[active_color_index])
        if active_line_style is not None:
            # Same masks as FreeCAD's ViewProviderPartExt::DrawStyle.
            preview_pattern = _LINE_PATTERNS[active_line_style]
        if active_line_weight is not None:
            from unistation.line_weights import widths_for_display
            _table, widths = widths_for_display(self.doc)
            preview_width = widths[active_line_weight]
        self.name = self.doc.Name
        self.view = Gui.activeDocument().activeView()
        self.graph = self.view.getSceneGraph()
        self.graph.ref()
        self.node = coin.SoSeparator()
        color = coin.SoBaseColor()
        color.rgb = preview_rgb
        self.preview_color = color
        self.preview_style = None
        self.coords = coin.SoCoordinate3()
        self.lines = coin.SoLineSet()
        self.lines.numVertices.setValue(0)
        self.node.addChild(color)
        if preview_pattern is not None or preview_width is not None:
            draw_style = coin.SoDrawStyle()
            draw_style.style = coin.SoDrawStyle.LINES
            if preview_pattern is not None:
                draw_style.linePattern = preview_pattern
            if preview_width is not None:
                draw_style.lineWidth = preview_width
            self.node.addChild(draw_style)
            self.preview_style = draw_style
        self.node.addChild(self.coords)
        self.node.addChild(self.lines)
        self.graph.addChild(self.node)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.guard)
        self.panel = None
        self.closed = False
        Gui.addDocumentObserver(self)

    def slotDeletedDocument(self, document):
        # Gui emits this before deleting the view and its Coin graph.
        # A timer is too late for native input resources owned by that view.
        if document.Document is self.doc:
            cancel()

    def alive(self):
        try:
            return (App.listDocuments().get(self.name) is self.doc
                    and App.ActiveDocument is self.doc
                    and Gui.activeDocument().activeView() == self.view)
        except (RuntimeError, AttributeError):
            return False

    def guard(self):
        if not self.alive() or not self.axisflow.isActive():
            cancel()

    def copy_point(self, point):
        return App.Vector(point)

    def report(self, message):
        App.Console.PrintWarning("UniStation: " + message + "\n")

    def preview(self, first, last):
        self.coords.point.setValues(0, 2, [
            (first.x, first.y, first.z), (last.x, last.y, last.z)])
        self.lines.numVertices.setValue(2)

    def refresh_active_attributes(self):
        """Update one complete display/settings snapshot without restarting input."""
        if self.active_color_index is None or not self.alive():
            return
        from unistation.attributes import drawing_snapshot
        from unistation.palette import colors_for_display
        from unistation.line_weights import widths_for_display
        index, style, weight = drawing_snapshot(self.doc)
        _palette, colors = colors_for_display(self.doc)
        _table, widths = widths_for_display(self.doc)
        rgb = tuple(channel / 255.0 for channel in colors[index])
        pattern, width = _LINE_PATTERNS[style], widths[weight]
        # All validation precedes state changes. The same Coin nodes style
        # every retained Wire segment as well as the current rubber band.
        self.preview_color.rgb = rgb
        self.preview_style.linePattern = pattern
        self.preview_style.lineWidth = width
        self.active_color_index = index
        self.active_line_style = style
        self.active_line_weight = weight

    def create_line(self, first, last):
        import Draft
        self.create_geometry(tr('UniStation Line'), lambda: Draft.make_line(first, last))

    def preview_wire(self, points, cursor):
        vertices = list(points) + ([cursor] if cursor is not None else [])
        self.coords.point.setValues(0, len(vertices), [(p.x, p.y, p.z) for p in vertices])
        self.lines.numVertices.setValue(len(vertices) if len(vertices) > 1 else 0)

    def create_wire(self, points, closed):
        import Draft
        self.create_geometry(tr('UniStation Wire'), lambda: Draft.make_wire(
            points, closed=closed, face=False))

    def create_geometry(self, title, factory):
        if not self.alive():
            raise RuntimeError(tr('The original document/view is no longer active'))
        # Read again before commit even if a queued toolbar refresh has not run.
        self.refresh_active_attributes()
        self.doc.openTransaction(title)
        try:
            obj = factory()
            if obj is None:
                raise RuntimeError(tr('Draft factory returned no object'))
            self.doc.recompute()
            if obj.Shape.isNull() or not obj.Shape.isValid():
                raise RuntimeError(tr('Draft produced invalid geometry'))
            if self.active_color_index is not None:
                from unistation.palette import apply_index_in_transaction
                apply_index_in_transaction(self.doc, [obj], self.active_color_index)
            if self.active_line_style is not None:
                from unistation.attributes import apply_line_style_in_transaction
                apply_line_style_in_transaction(self.doc, obj, self.active_line_style)
            if self.active_line_weight is not None:
                from unistation.line_weights import apply_in_transaction
                apply_in_transaction(self.doc, obj, self.active_line_weight)
            self.doc.commitTransaction()
        except Exception:
            self.doc.abortTransaction()
            raise
        from unistation.operation_selection import finish
        finish(self.doc, [obj])

    def clear_preview(self):
        self.lines.numVertices.setValue(0)

    def reset_input(self):
        self.clear_preview()
        if self.panel is not None:
            self.panel.reset_input()

    def set_circle_plane(self, u, v, normal):
        """Use the same live compass frame for validation, preview and creation."""
        self.circle_rotation = App.Rotation(App.Vector(*u), App.Vector(*v),
                                            App.Vector(*normal), "ZXY")

    def preview_circle(self, center, radius):
        # Polygon only for display; final geometry is an exact Draft/OCC circle.
        vertices = [center + self.circle_rotation.multVec(App.Vector(
            radius * math.cos(2 * math.pi * i / 128),
            radius * math.sin(2 * math.pi * i / 128), 0)) for i in range(129)]
        self.preview_wire(vertices, None)

    def create_circle(self, center, radius):
        import Draft
        placement = App.Placement(center, self.circle_rotation)
        self.create_geometry(tr('UniStation Circle'), lambda: Draft.make_circle(
            radius, placement=placement, face=False))

    def arc_edge(self, first, through, last):
        import Part
        return Part.Arc(first, through, last).toShape()

    def preview_arc(self, first, through, last):
        edge = self.arc_edge(first, through, last)
        self.preview_wire(edge.discretize(Number=129), None)

    def create_arc(self, first, through, last):
        import Draft
        edge = self.arc_edge(first, through, last)
        # Draft preserves the circular segment, including arcs greater than 180 degrees.
        self.create_geometry(tr('UniStation Arc'), lambda: Draft.make_circle(
            edge, placement=App.Placement(App.Vector(), self.circle_rotation), face=False))

    def close(self):
        global _session
        if self.closed:
            return
        self.closed = True
        self.timer.stop()
        Gui.removeDocumentObserver(self)
        try:
            self.graph.removeChild(self.node)
        finally:
            self.graph.unref()
            _session = None
            if self.panel is not None:
                Gui.Control.closeDialog()


def key_hint(axisflow, action):
    """Display actual bindings, including two-key chords, without rebinding."""
    try:
        bindings = axisflow.getSettings()["hotkeys"][action]
        return " / ".join(
            " ".join(QtGui.QKeySequence(key).toString() for key in
                     (binding if isinstance(binding, (list, tuple)) else [binding]))
            for binding in bindings) or "unassigned"
    except (AttributeError, KeyError, TypeError):
        return tr('see AxisFlow settings')


class Panel:
    def __init__(self, axisflow, session):
        self.session = session
        self.form = QtWidgets.QWidget()
        wire = isinstance(session, WireSession)
        circle = isinstance(session, CircleSession)
        arc = isinstance(session, ArcSession)
        transform = isinstance(session, TransformSession)
        title = QT_TRANSLATE_NOOP('UniStation', 'UniStation Copy') if transform and session.copy else QT_TRANSLATE_NOOP('UniStation', 'UniStation Move')
        bind(self.form, 'setWindowTitle', title if transform else
             QT_TRANSLATE_NOOP('UniStation', 'UniStation Arc') if arc else
             QT_TRANSLATE_NOOP('UniStation', 'UniStation Circle') if circle else
             QT_TRANSLATE_NOOP('UniStation', 'UniStation Wire') if wire else
             QT_TRANSLATE_NOOP('UniStation', 'UniStation Line'))
        layout = QtWidgets.QVBoxLayout(self.form)
        if wire:
            for text, name, callback in (
                    (QT_TRANSLATE_NOOP('UniStation', 'Finish wire'), "unistation_finish_wire", session.finish),
                    (QT_TRANSLATE_NOOP('UniStation', 'Close contour'), "unistation_close_contour", session.close_contour)):
                button = translated_button(text)
                button.setObjectName(name)
                button.setAutoDefault(False)
                button.setDefault(False)
                button.clicked.connect(callback)
                layout.addWidget(button)
        reset_button = translated_button('Reset')
        reset_button.setObjectName("unistation_reset")
        reset_button.setAutoDefault(False)
        reset_button.clicked.connect(lambda: reset(expected=session, source="task"))
        layout.addWidget(reset_button)

    def reset_input(self):
        from unistation.coordinate_input import reset_for
        reset_for(self.session)

    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Close

    def reject(self):
        cancel()
        return True

    def isAllowedAlterDocument(self):
        return False

    def isAllowedAlterView(self):
        return True

    def isAllowedAlterSelection(self):
        return False


def start(kind="line"):
    global _session
    if kind not in ("line", "wire", "circle", "arc", "move", "copy"):
        raise ValueError(tr('Unknown command: ') + kind)
    cancel()
    if not App.ActiveDocument or Gui.Control.activeDialog():
        raise RuntimeError(tr('Open a document and finish the current task first'))
    if getattr(App, "activeDraftCommand", None):
        raise RuntimeError(tr('Finish the current Draft command first'))
    active_index = None
    active_style = None
    active_weight = None
    if kind in ("line", "wire", "circle", "arc"):
        from unistation.attributes import drawing_snapshot
        active_index, active_style, active_weight = drawing_snapshot(App.ActiveDocument)
    import AxisFlow
    required = ("getPoint", "endSession", "setPlane", "isActive")
    if kind in ("line", "wire", "circle"):
        required += ("confirm", "setBasePoint")
    if kind in ("circle", "arc"):
        required += ("getCompassInfo",)
    for name in required:
        if not callable(getattr(AxisFlow, name, None)):
            raise RuntimeError(tr('Incompatible AxisFlow: missing ') + name)
    if AxisFlow.isActive():
        raise RuntimeError(tr('Finish the current AxisFlow session first'))
    import WorkingPlane
    wp = WorkingPlane.get_working_plane()
    AxisFlow.setPlane(wp.u, wp.v, wp.axis)
    if kind in ("move", "copy"):
        from unistation.transform_gui import selected_objects, TransformBackend
        backend = TransformBackend(AxisFlow, selected_objects())
    else:
        backend = Backend(AxisFlow, active_color_index=active_index,
                          active_line_style=active_style, active_line_weight=active_weight)
    session_type = {"line": LineSession, "wire": WireSession,
                    "circle": CircleSession, "arc": ArcSession,
                    "move": TransformSession, "copy": TransformSession}[kind]
    options = {}
    if kind in ("move", "copy"):
        options["copy"] = kind == "copy"
    if kind in ("circle", "arc"):
        backend.circle_rotation = App.Rotation(wp.u, wp.v, wp.axis, "ZXY")
        options["normal"] = tuple(wp.axis)
    _session = session_type(backend, AxisFlow, origin=App.Vector(wp.position), **options)
    try:
        backend.panel = Panel(AxisFlow, _session)
        Gui.Control.showDialog(backend.panel)
        backend.timer.start()
        _session.start()
    except Exception:
        cancel()
        raise


class LineCommand:
    def GetResources(self):
        return {"Pixmap": str(_ICON_DIR / "line.svg"),
                "MenuText": QT_TRANSLATE_NOOP('UniStation_Line', 'UniStation Line'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_Line', 'Create a two-point Draft line using AxisFlow')}

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        try:
            start()
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")


class WireCommand(LineCommand):
    def GetResources(self):
        return {"Pixmap": str(_ICON_DIR / "wire.svg"),
                "MenuText": QT_TRANSLATE_NOOP('UniStation_Wire', 'UniStation Wire'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_Wire', 'Create an open or closed Draft polyline using AxisFlow')}

    def Activated(self):
        try:
            start("wire")
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")


class CircleCommand(LineCommand):
    def GetResources(self):
        return {"Pixmap": str(_ICON_DIR / "circle.svg"),
                "MenuText": QT_TRANSLATE_NOOP('UniStation_Circle', 'UniStation Circle'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_Circle', 'Create a Draft circle from center and radius point using AxisFlow')}

    def Activated(self):
        try:
            start("circle")
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")


class ArcCommand(LineCommand):
    def GetResources(self):
        return {"Pixmap": str(_ICON_DIR / "arc.svg"),
                "MenuText": QT_TRANSLATE_NOOP('UniStation_Arc', 'UniStation Arc'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_Arc', 'Create a Draft arc through start, through-point and end using AxisFlow')}

    def Activated(self):
        try:
            start("arc")
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")


class TransformCommand(LineCommand):
    def __init__(self, copy=False):
        self.kind = "copy" if copy else "move"

    def GetResources(self):
        if self.kind == "copy":
            label = QT_TRANSLATE_NOOP("UniStation_Copy", "UniStation Copy")
            tip = QT_TRANSLATE_NOOP("UniStation_Copy", "Select independent whole objects, then pick base and target using AxisFlow")
        else:
            label = QT_TRANSLATE_NOOP("UniStation_Move", "UniStation Move")
            tip = QT_TRANSLATE_NOOP("UniStation_Move", "Select independent whole objects, then pick base and target using AxisFlow")
        return {"Pixmap": str(_ICON_DIR / (self.kind + ".svg")),
                "MenuText": label,
                "ToolTip": tip}

    def Activated(self):
        try:
            start(self.kind)
        except Exception as exc:
            App.Console.PrintError("UniStation: " + str(exc) + "\n")


class PendingCommand:
    """Visible placeholders; even a forced activation must leave the model alone."""

    def __init__(self, kind, label, tip):
        self.kind = kind
        self.label = label
        self.tip = tip

    def GetResources(self):
        return {"Pixmap": str(_ICON_DIR / (self.kind + ".svg")),
                "MenuText": self.label,
                "ToolTip": self.tip}

    def IsActive(self):
        return False

    def Activated(self):
        pass


class CancelCommand:
    def GetResources(self):
        return {"CmdType": "ForEdit NoTransaction",
                "MenuText": QT_TRANSLATE_NOOP('UniStation_Cancel', 'Cancel UniStation'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_Cancel', 'Cancel the current UniStation input')}

    def IsActive(self):
        return active_input() is not None

    def Activated(self):
        cancel()


class ResetCommand(CancelCommand):
    def GetResources(self):
        return {"CmdType": "ForEdit NoTransaction",
                "MenuText": QT_TRANSLATE_NOOP('UniStation_Reset', 'Reset'),
                "ToolTip": QT_TRANSLATE_NOOP('UniStation_Reset',
                    'Send Reset to the current command: step back, then exit on another Reset')}

    def Activated(self):
        reset(source="menu")


def register():
    Gui.addCommand("UniStation_Line", LineCommand())
    Gui.addCommand("UniStation_Wire", WireCommand())
    Gui.addCommand("UniStation_Circle", CircleCommand())
    Gui.addCommand("UniStation_Arc", ArcCommand())
    Gui.addCommand("UniStation_Rectangle", PendingCommand("rectangle",
        QT_TRANSLATE_NOOP("UniStation_Rectangle", "Rectangle"),
        QT_TRANSLATE_NOOP("UniStation_Rectangle", "Rectangle — not available yet")))
    Gui.addCommand("UniStation_Freeform", PendingCommand("freeform",
        QT_TRANSLATE_NOOP("UniStation_Freeform", "Freeform Shape"),
        QT_TRANSLATE_NOOP("UniStation_Freeform", "Freeform Shape — not available yet")))
    Gui.addCommand("UniStation_Move", TransformCommand())
    Gui.addCommand("UniStation_Copy", TransformCommand(copy=True))
    Gui.addCommand("UniStation_Scale", PendingCommand("scale",
        QT_TRANSLATE_NOOP("UniStation_Scale", "Scale"),
        QT_TRANSLATE_NOOP("UniStation_Scale", "Scale — not available yet")))
    Gui.addCommand("UniStation_Rotate", PendingCommand("rotate",
        QT_TRANSLATE_NOOP("UniStation_Rotate", "Rotate"),
        QT_TRANSLATE_NOOP("UniStation_Rotate", "Rotate — not available yet")))
    Gui.addCommand("UniStation_Mirror", PendingCommand("mirror",
        QT_TRANSLATE_NOOP("UniStation_Mirror", "Mirror"),
        QT_TRANSLATE_NOOP("UniStation_Mirror", "Mirror — not available yet")))
    Gui.addCommand("UniStation_Array", PendingCommand("array",
        QT_TRANSLATE_NOOP("UniStation_Array", "Array"),
        QT_TRANSLATE_NOOP("UniStation_Array", "Array — not available yet")))
    Gui.addCommand("UniStation_Cancel", CancelCommand())
    Gui.addCommand("UniStation_Reset", ResetCommand())
