"""Unit tests for GUI failure diagnostics. FreeCAD and Qt are not imported."""

import ast
import json
import os
import sys
import tempfile
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gui_diagnostics


class Widget:
    def __init__(self, class_name="QWidget", object_name="view", title="View",
                 visible=True, width=640, height=480, ratio=1.0, opengl=False,
                 broken=None):
        self.class_name = class_name
        self.object_name = object_name
        self.title = title
        self.visible = visible
        self.pixel_width = width
        self.pixel_height = height
        self.ratio = ratio
        self.opengl = opengl
        self.broken = set(broken or ())

    def _value(self, field, value):
        if field in self.broken:
            raise RuntimeError("destroyed " + field)
        return value

    def metaObject(self):
        return self

    def className(self):
        return self._value("class_name", self.class_name)

    def objectName(self):
        return self._value("object_name", self.object_name)

    def windowTitle(self):
        return self._value("window_title", self.title)

    def isVisible(self):
        return self._value("is_visible", self.visible)

    def width(self):
        return self._value("width", self.pixel_width)

    def height(self):
        return self._value("height", self.pixel_height)

    def devicePixelRatioF(self):
        return self._value("device_pixel_ratio", self.ratio)

    def inherits(self, name):
        return self._value("inherits", name == "QOpenGLWidget" and self.opengl)


class ActiveWindow(Widget):
    def __init__(self, children, **kwargs):
        super().__init__(**kwargs)
        self.children = list(children)

    def findChildren(self, child_class):
        if "find" in self.broken:
            raise RuntimeError("destroyed find")
        return list(self.children)


class Mdi:
    def __init__(self, active, windows):
        self.active = active
        self.windows = list(windows)

    def activeSubWindow(self):
        return self.active

    def subWindowList(self):
        return list(self.windows)


class Area:
    def __init__(self, active):
        self.active = active

    def activeSubWindow(self):
        return self.active


class SubWindow:
    def __init__(self, widgets):
        self.widgets = list(widgets)

    def findChildren(self, child_class):
        return list(self.widgets)


class View:
    pass


class Backend:
    def __init__(self, closed=False, name="axis"):
        self.closed = closed
        self.name = name


class BrokenClosed:
    name = "axis"

    @property
    def closed(self):
        raise RuntimeError("destroyed closed")


class Session:
    def __init__(self, backend):
        self.backend = backend


def readers(**overrides):
    base = {
        "document_names": lambda: ["QtInputTest"],
        "active_document_name": lambda: "QtInputTest",
        "gui_active_document": lambda: object(),
        "active_view": lambda: View(),
        "session": lambda: None,
        "axisflow_active": lambda: False,
        "focus_widget": lambda: None,
        "active_window": lambda: None,
        "mdi_area": lambda: None,
        "widget_class": lambda: object,
    }
    base.update(overrides)
    return base


class SnapshotTests(unittest.TestCase):
    def test_normal_observations_are_plain_data(self):
        gl = Widget(class_name="QOpenGLWidget", object_name="gl", opengl=True,
                    width=800, height=600, ratio=1.25)
        active = ActiveWindow([gl], class_name="QMdiSubWindow", object_name="child",
                              title="QtInputTest", width=900, height=700)
        focus = Widget(class_name="QLineEdit", object_name="distance", title="",
                       visible=True, width=40, height=18)
        snapshot = gui_diagnostics.collect_snapshot(readers(
            document_names=lambda: ["Alpha", "QtInputTest"],
            session=lambda: Session(Backend(False, "coin")),
            axisflow_active=lambda: True,
            focus_widget=lambda: focus,
            active_window=lambda: active,
            mdi_area=lambda: Mdi(active, [active]),
        ))
        self.assertEqual(snapshot["documents"], ["Alpha", "QtInputTest"])
        self.assertEqual(snapshot["active_document_name"], "QtInputTest")
        self.assertEqual(snapshot["gui_active_document"], {"present": True})
        self.assertEqual(snapshot["active_view_type"], "View")
        self.assertEqual(snapshot["session"]["present"], True)
        self.assertEqual(snapshot["session"]["type"], "Session")
        self.assertIs(snapshot["session"]["backend_closed"], False)
        self.assertEqual(snapshot["session"]["backend_name"], "coin")
        self.assertIs(snapshot["axisflow_active"], True)
        self.assertEqual(snapshot["focus_widget"]["class_name"], "QLineEdit")
        self.assertEqual(snapshot["focus_widget"]["object_name"], "distance")
        self.assertEqual(snapshot["mdi"]["opengl_candidate_count"], 1)
        self.assertEqual(snapshot["mdi"]["opengl_widgets"][0]["device_pixel_ratio"], 1.25)
        self.assertEqual(snapshot["mdi"]["subwindows"][0]["width"], 900)
        self.assertEqual(snapshot["errors"], [])
        json.dumps(snapshot)

    def test_missing_document_mdi_and_active_window_are_null(self):
        idle = Widget(class_name="QMdiSubWindow", object_name="idle")
        snapshot = gui_diagnostics.collect_snapshot(readers(
            document_names=lambda: [],
            active_document_name=lambda: None,
            gui_active_document=lambda: None,
            active_view=lambda: None,
            mdi_area=lambda: Mdi(None, [idle]),
        ))
        self.assertEqual(snapshot["documents"], [])
        self.assertIsNone(snapshot["active_document_name"])
        self.assertIsNone(snapshot["gui_active_document"])
        self.assertIsNone(snapshot["active_view_type"])
        self.assertIsNone(snapshot["session"])
        self.assertIsNone(snapshot["focus_widget"])
        self.assertIsNone(snapshot["active_window"])
        self.assertIsNone(snapshot["mdi"]["active_subwindow"])
        self.assertIsNone(snapshot["mdi"]["opengl_candidate_count"])
        self.assertIsNone(snapshot["mdi"]["opengl_widgets"])
        self.assertEqual(snapshot["mdi"]["subwindows"][0]["class_name"], "QMdiSubWindow")
        self.assertIsNone(gui_diagnostics.collect_snapshot(readers())["mdi"])

    def test_opengl_candidate_counts(self):
        plain = Widget(class_name="QLabel", opengl=False)
        none_active = ActiveWindow([plain], class_name="QMdiSubWindow")
        none_snapshot = gui_diagnostics.collect_snapshot(readers(
            mdi_area=lambda: Mdi(none_active, [none_active])))
        self.assertEqual(none_snapshot["mdi"]["opengl_candidate_count"], 0)
        self.assertEqual(none_snapshot["mdi"]["opengl_widgets"], [])
        first = Widget(class_name="QOpenGLWidget", object_name="a", opengl=True)
        second = Widget(class_name="QOpenGLWidget", object_name="b", opengl=True)
        many = ActiveWindow([first, second], class_name="QMdiSubWindow")
        many_snapshot = gui_diagnostics.collect_snapshot(readers(
            mdi_area=lambda: Mdi(many, [many])))
        self.assertEqual(many_snapshot["mdi"]["opengl_candidate_count"], 2)
        self.assertEqual(
            [item["object_name"] for item in many_snapshot["mdi"]["opengl_widgets"]],
            ["a", "b"])

    def test_one_destroyed_field_does_not_block_the_rest(self):
        focus = Widget(broken={"object_name"})

        def axisflow():
            raise RuntimeError("destroyed axisflow")

        snapshot = gui_diagnostics.collect_snapshot(readers(
            document_names=lambda: ["Kept"],
            focus_widget=lambda: focus,
            axisflow_active=axisflow,
            session=lambda: Session(BrokenClosed()),
        ))
        self.assertEqual(snapshot["documents"], ["Kept"])
        self.assertEqual(snapshot["focus_widget"]["class_name"], "QWidget")
        self.assertIsNone(snapshot["focus_widget"]["object_name"])
        self.assertIsNone(snapshot["axisflow_active"])
        self.assertEqual(snapshot["session"]["backend_name"], "axis")
        self.assertIsNone(snapshot["session"]["backend_closed"])
        fields = {item["field"]: item["error"] for item in snapshot["errors"]}
        self.assertIn("destroyed object_name", fields["focus_widget.object_name"])
        self.assertIn("destroyed axisflow", fields["axisflow_active"])
        self.assertIn("destroyed closed", fields["session.backend_closed"])
        json.dumps(snapshot)

    def test_non_plain_value_is_not_serialized_by_repr(self):
        focus = Widget()
        focus.pixel_width = object()
        snapshot = gui_diagnostics.collect_snapshot(readers(focus_widget=lambda: focus))
        self.assertIsNone(snapshot["focus_widget"]["width"])
        self.assertTrue(any(item["field"] == "focus_widget.width" for item in snapshot["errors"]))
        encoded = json.dumps(snapshot)
        self.assertNotIn("object at", encoded)

    def test_caller_retains_widgets_discovered_by_the_snapshot(self):
        gl = Widget(class_name="QOpenGLWidget", object_name="gl", opengl=True)
        active = ActiveWindow([gl], class_name="QMdiSubWindow")
        area = Mdi(active, [])
        retained = []
        found = []
        listed = []

        def retain(widget):
            retained.append(widget)
            return widget

        def find_children(parent, child_class):
            found.append((parent, child_class))
            return [gl]

        def list_subwindows(mdi):
            listed.append(mdi)
            return [active]

        snapshot = gui_diagnostics.collect_snapshot(readers(
            mdi_area=lambda: area,
            find_children=find_children,
            list_subwindows=list_subwindows,
            retain=retain,
        ))
        self.assertEqual(snapshot["mdi"]["opengl_candidate_count"], 1)
        self.assertEqual(snapshot["mdi"]["opengl_widgets"][0]["object_name"], "gl")
        self.assertEqual(snapshot["mdi"]["subwindows"][0]["class_name"], "QMdiSubWindow")
        self.assertEqual(found, [(active, object)])
        self.assertEqual(listed, [area])
        self.assertEqual(retained, [active])

    def test_missing_backend_is_null_without_an_error(self):
        class Bare:
            pass

        snapshot = gui_diagnostics.collect_snapshot(readers(session=lambda: Bare()))
        self.assertEqual(snapshot["session"]["type"], "Bare")
        self.assertIsNone(snapshot["session"]["backend_closed"])
        self.assertIsNone(snapshot["session"]["backend_name"])
        self.assertEqual(snapshot["errors"], [])


class ViewportTests(unittest.TestCase):
    def test_missing_mdi_and_active_window_are_distinct(self):
        with self.assertRaises(RuntimeError) as missing_area:
            gui_diagnostics.opengl_viewport_widgets(None, object)
        self.assertIn("QMdiArea is missing", str(missing_area.exception))
        with self.assertRaises(RuntimeError) as missing_window:
            gui_diagnostics.opengl_viewport_widgets(Area(None), object)
        self.assertIn("activeSubWindow is missing", str(missing_window.exception))

    def test_candidate_count_raises_after_widgets_are_available(self):
        plain = Widget(class_name="QLabel", opengl=False)
        widgets, candidates = gui_diagnostics.opengl_viewport_widgets(
            Area(SubWindow([plain])), object)
        self.assertEqual(widgets, [plain])
        self.assertEqual(candidates, [])
        with self.assertRaises(RuntimeError) as none:
            gui_diagnostics.require_single_opengl(widgets, candidates)
        self.assertIn("found 0", str(none.exception))
        self.assertIn("QLabel", str(none.exception))
        first = Widget(class_name="QOpenGLWidget", opengl=True)
        second = Widget(class_name="QOpenGLWidget", opengl=True)
        widgets, candidates = gui_diagnostics.opengl_viewport_widgets(
            Area(SubWindow([first, second])), object)
        self.assertEqual(candidates, [first, second])
        with self.assertRaises(RuntimeError) as several:
            gui_diagnostics.require_single_opengl(widgets, candidates)
        self.assertIn("found 2", str(several.exception))
        only = Widget(class_name="QOpenGLWidget", opengl=True)
        widgets, candidates = gui_diagnostics.opengl_viewport_widgets(
            Area(SubWindow([only])), object)
        self.assertIs(gui_diagnostics.require_single_opengl(widgets, candidates), only)


class TraceTests(unittest.TestCase):
    def test_failure_payload_keeps_error_and_event_order(self):
        trace = gui_diagnostics.CaseTrace("run-1")
        trace.begin("transform_mouse_endpoint_snap", "QtInputTest")
        trace.add_event("before_view", (1, 2, 3), False, {"step": "before"})
        trace.add_event("after_move", (4.5, -6, 0), True, {"step": "move"})
        trace.add_event("after_click", (4.5, -6, 0), True, {"step": "click"})
        original = "Traceback (most recent call last):\nRuntimeError: viewport missing\n"
        payload = trace.failure_payload(original, {"final": True}, 4128)
        loaded = json.loads(json.dumps(payload))
        self.assertEqual(loaded["schema_version"], 1)
        self.assertEqual(loaded["run_id"], "run-1")
        self.assertEqual(loaded["case_name"], "transform_mouse_endpoint_snap")
        self.assertEqual(loaded["expected_document"], "QtInputTest")
        self.assertEqual(loaded["pid"], 4128)
        self.assertEqual(loaded["input_method"], "qt")
        self.assertIs(loaded["os_input_verified"], False)
        self.assertEqual(loaded["original_error"], original)
        self.assertEqual(
            [event["phase"] for event in loaded["mouse_events"]],
            ["before_view", "after_move", "after_click"])
        self.assertEqual([event["sequence"] for event in loaded["mouse_events"]], [1, 2, 3])
        self.assertEqual(loaded["mouse_events"][1]["target"], [4.5, -6, 0])
        self.assertIs(loaded["mouse_events"][0]["click"], False)
        self.assertEqual(loaded["failure_snapshot"], {"final": True})
        trace.begin("transform_lifecycle", "Next")
        self.assertEqual(trace.events, [])
        self.assertEqual(trace.failure_payload("later", {}, 1)["mouse_events"], [])


class WriteTests(unittest.TestCase):
    def test_write_publishes_one_file_and_removes_the_temporary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = gui_diagnostics.write_case_file(
                tmp, "transform_rollback", {"schema_version": 1, "ok": True})
            self.assertEqual(path.parent.name, "gui-diagnostics")
            self.assertEqual(path.name, "transform_rollback.json")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["ok"], True)
            self.assertEqual(list(path.parent.glob(".diag-*.tmp")), [])
            other = gui_diagnostics.write_case_file(
                tmp, "transform_lifecycle", {"schema_version": 1, "ok": False})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["ok"], True)
            self.assertEqual(json.loads(other.read_text(encoding="utf-8"))["ok"], False)

    def test_existing_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "gui-diagnostics"
            directory.mkdir()
            existing = directory / "alpha.json"
            existing.write_text("original\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                gui_diagnostics.write_case_file(tmp, "alpha", {"new": True})
            self.assertEqual(existing.read_text(encoding="utf-8"), "original\n")
            self.assertEqual(list(directory.glob(".diag-*.tmp")), [])

    def test_write_failure_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "gui-diagnostics"
            directory.mkdir()
            kept = directory / "kept.txt"
            kept.write_text("sentinel", encoding="utf-8")
            existing = directory / "alpha.json"
            existing.write_text("original\n", encoding="utf-8")
            with patch("gui_diagnostics.os.link", side_effect=PermissionError("denied")), \
                    patch("gui_diagnostics.os.rename", side_effect=PermissionError("denied")):
                with self.assertRaises(PermissionError):
                    gui_diagnostics.write_case_file(tmp, "beta", {"ok": True})
            self.assertEqual(kept.read_text(encoding="utf-8"), "sentinel")
            self.assertEqual(existing.read_text(encoding="utf-8"), "original\n")
            self.assertFalse((directory / "beta.json").exists())
            self.assertEqual(list(directory.glob(".diag-*.tmp")), [])

    def test_illegal_case_name_cannot_escape_the_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("../outside", "sub/case", "sub\\case", "..", "a:b", " case", ""):
                with self.assertRaises(ValueError):
                    gui_diagnostics.write_case_file(root, name, {"x": 1})
            self.assertFalse((root / "outside.json").exists())
            self.assertFalse((root / "sub").exists())
            self.assertFalse((root / "gui-diagnostics").exists())


def load_run_one_case():
    path = Path(__file__).with_name("qt_input.FCMacro")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_one_case"
    ]
    if len(found) != 1:
        raise AssertionError("run_one_case was not found once at module level")
    module = ast.Module(body=[found[0]], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"traceback": traceback}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["run_one_case"]


class MacroBranchTests(unittest.TestCase):
    def test_diagnostics_run_before_cleanup(self):
        run_one_case = load_run_one_case()
        order = []

        def begin(name, doc):
            order.append("begin")
            self.assertEqual(name, "transform_mouse_endpoint_snap")
            self.assertEqual(doc, "doc")

        def test(doc):
            order.append("test")
            raise RuntimeError("viewport missing")

        def record(name, original):
            order.append("diagnostics")
            self.assertIn("viewport missing", original)
            self.assertIn("RuntimeError", original)
            return {"error": "replaced", "status": "passed", "name": "other",
                    "diagnostics_path": "gui-diagnostics/transform_mouse_endpoint_snap.json"}

        def cleanup():
            order.append("cleanup")

        entry = run_one_case(
            "transform_mouse_endpoint_snap", test, "doc", begin, record, cleanup)
        self.assertEqual(order, ["begin", "test", "diagnostics", "cleanup"])
        self.assertEqual(entry["status"], "failed")
        self.assertEqual(entry["name"], "transform_mouse_endpoint_snap")
        self.assertIn("viewport missing", entry["error"])
        self.assertNotIn("replaced", entry["error"])
        self.assertEqual(
            entry["diagnostics_path"],
            "gui-diagnostics/transform_mouse_endpoint_snap.json")

    def test_write_failure_keeps_the_original_traceback(self):
        run_one_case = load_run_one_case()
        order = []

        def begin(name, doc):
            order.append("begin")

        def test(doc):
            order.append("test")
            raise ValueError("original boom")

        def record(name, original):
            order.append("diagnostics")
            self.assertIn("original boom", original)
            raise OSError("disk full")

        def cleanup():
            order.append("cleanup")

        entry = run_one_case("transform_lifecycle", test, "doc", begin, record, cleanup)
        self.assertEqual(order, ["begin", "test", "diagnostics", "cleanup"])
        self.assertEqual(entry["status"], "failed")
        self.assertIn("original boom", entry["error"])
        self.assertIn("ValueError", entry["error"])
        self.assertNotIn("disk full", entry["error"])
        self.assertIn("OSError: disk full", entry["diagnostics_error"])
        self.assertNotIn("diagnostics_path", entry)

    def test_success_does_not_record_diagnostics(self):
        run_one_case = load_run_one_case()
        order = []

        def begin(name, doc):
            order.append("begin")

        def test(doc):
            order.append("test")
            return {"points": 2}

        def record(name, original):
            order.append("diagnostics")

        def cleanup():
            order.append("cleanup")

        entry = run_one_case("transform_rollback", test, "doc", begin, record, cleanup)
        self.assertEqual(order, ["begin", "test", "cleanup"])
        self.assertEqual(entry, {"name": "transform_rollback", "status": "passed",
                                 "detail": {"points": 2}})


if __name__ == "__main__":
    unittest.main()
