"""Serializable observations for a failed Qt GUI case.

FreeCAD and Qt objects are supplied by the caller. This module does not import
them and does not process Qt events or change the objects it reads.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def validate_case_name(case_name):
    if not isinstance(case_name, str) or case_name == "" or case_name != case_name.strip():
        raise ValueError("invalid case name")
    if ".." in case_name or "/" in case_name or "\\" in case_name or ":" in case_name:
        raise ValueError("invalid case name")
    if Path(case_name).name != case_name or Path(case_name).is_absolute():
        raise ValueError("invalid case name")


def read_value(errors, field, getter):
    try:
        return getter()
    except RuntimeError as error:
        errors.append({"field": field, "error": str(error)})
        return None


def plain_value(errors, field, value):
    if isinstance(value, bool) or value is None or isinstance(value, (str, int, float)):
        if isinstance(value, float) and (value != value or value == float("inf") or value == float("-inf")):
            errors.append({"field": field, "error": "non-finite number"})
            return None
        return value
    errors.append({"field": field, "error": "non-serializable %s" % type(value).__name__})
    return None


def widget_brief(errors, prefix, widget, include_ratio=False):
    if widget is None:
        return None

    def take(suffix, getter):
        return plain_value(errors, prefix + "." + suffix, read_value(errors, prefix + "." + suffix, getter))

    brief = {
        "class_name": take("class_name", lambda: widget.metaObject().className()),
        "object_name": take("object_name", lambda: widget.objectName()),
        "window_title": take("window_title", lambda: widget.windowTitle()),
        "is_visible": take("is_visible", lambda: widget.isVisible()),
        "width": take("width", lambda: widget.width()),
        "height": take("height", lambda: widget.height()),
    }
    if include_ratio:
        brief["device_pixel_ratio"] = take("device_pixel_ratio", lambda: widget.devicePixelRatioF())
    return brief


def _optional_attr(errors, field, obj, attr):
    if obj is None:
        return None
    try:
        return getattr(obj, attr)
    except RuntimeError as error:
        errors.append({"field": field, "error": str(error)})
        return None
    except AttributeError:
        return None


def _opengl_children(errors, active, child_class, find_children):
    if active is None or child_class is None:
        return None
    try:
        if find_children is None:
            children = list(active.findChildren(child_class))
        else:
            children = list(find_children(active, child_class))
    except RuntimeError as error:
        errors.append({"field": "mdi.opengl_widgets", "error": str(error)})
        return None
    found = []
    for child in children:
        try:
            matches = bool(child.inherits("QOpenGLWidget"))
        except RuntimeError as error:
            errors.append({"field": "mdi.opengl_inherits", "error": str(error)})
            continue
        if matches:
            found.append(child)
    return found


def collect_snapshot(readers):
    """Read one consistent set of observations. readers values are callables."""
    errors = []

    def take(field, key):
        return read_value(errors, field, readers[key])

    document_names = take("documents", "document_names")
    if document_names is not None:
        document_names = [plain_value(errors, "documents", name) for name in list(document_names)]
    active_document_name = plain_value(errors, "active_document_name", take("active_document_name", "active_document_name"))
    gui_document = take("gui_active_document", "gui_active_document")
    active_view = take("active_view", "active_view")
    session = take("session", "session")
    axisflow_active = plain_value(errors, "axisflow_active", take("axisflow_active", "axisflow_active"))
    focus_widget = widget_brief(errors, "focus_widget", take("focus_widget", "focus_widget"))
    active_window = widget_brief(errors, "active_window", take("active_window", "active_window"))
    mdi = take("mdi", "mdi_area")
    mdi_info = None
    if mdi is not None:
        active = read_value(errors, "mdi.active_subwindow", lambda: mdi.activeSubWindow())
        if active is not None and "retain" in readers:
            read_value(errors, "mdi.active_subwindow.retain", lambda: readers["retain"](active))
        if "list_subwindows" in readers:
            listed = read_value(errors, "mdi.subwindows", lambda: list(readers["list_subwindows"](mdi)))
            windows = listed
        else:
            try:
                windows = list(mdi.subWindowList())
            except RuntimeError as error:
                errors.append({"field": "mdi.subwindows", "error": str(error)})
                windows = None
        child_class = read_value(errors, "widget_class", readers["widget_class"])
        finder = readers["find_children"] if "find_children" in readers else None
        opengl = _opengl_children(errors, active, child_class, finder)
        mdi_info = {
            "present": True,
            "active_subwindow": widget_brief(errors, "mdi.active_subwindow", active),
            "subwindows": None if windows is None else [
                widget_brief(errors, "mdi.subwindows", window) for window in windows
            ],
            "opengl_candidate_count": None if opengl is None else len(opengl),
            "opengl_widgets": None if opengl is None else [
                widget_brief(errors, "mdi.opengl_widgets", widget, include_ratio=True)
                for widget in opengl
            ],
        }
    session_info = None
    if session is not None:
        backend = _optional_attr(errors, "session.backend", session, "backend")
        session_info = {
            "present": True,
            "type": type(session).__name__,
            "backend_closed": plain_value(
                errors, "session.backend_closed",
                _optional_attr(errors, "session.backend_closed", backend, "closed")),
            "backend_name": plain_value(
                errors, "session.backend_name",
                _optional_attr(errors, "session.backend_name", backend, "name")),
        }
    return {
        "documents": document_names,
        "active_document_name": active_document_name,
        "gui_active_document": None if gui_document is None else {"present": True},
        "active_view_type": None if active_view is None else type(active_view).__name__,
        "session": session_info,
        "axisflow_active": axisflow_active,
        "focus_widget": focus_widget,
        "active_window": active_window,
        "mdi": mdi_info,
        "errors": errors,
    }


def opengl_viewport_widgets(mdi, child_class):
    """Return retained child widgets and OpenGL candidates, or explain why there is no viewport."""
    if mdi is None:
        raise RuntimeError("Qt viewport unavailable: QMdiArea is missing")
    active = mdi.activeSubWindow()
    if active is None:
        raise RuntimeError("Qt viewport unavailable: MDI activeSubWindow is missing")
    widgets = list(active.findChildren(child_class))
    candidates = [widget for widget in widgets if widget.inherits("QOpenGLWidget")]
    return widgets, candidates


def require_single_opengl(widgets, candidates):
    if len(candidates) != 1:
        names = []
        for widget in widgets:
            try:
                names.append(widget.metaObject().className())
            except RuntimeError:
                names.append("<destroyed>")
        raise RuntimeError(
            "Qt viewport unavailable: expected one QOpenGLWidget, found %d (%s)"
            % (len(candidates), names))
    return candidates[0]


class CaseTrace:
    def __init__(self, run_id):
        self.run_id = str(run_id)
        self.case_name = None
        self.expected_document = None
        self.events = []
        self._sequence = 0

    def begin(self, case_name, expected_document):
        validate_case_name(case_name)
        self.case_name = case_name
        self.expected_document = None if expected_document is None else str(expected_document)
        self.events = []
        self._sequence = 0

    def add_event(self, phase, target, click, snapshot):
        self._sequence += 1
        self.events.append({
            "sequence": self._sequence,
            "phase": str(phase),
            "target": [float(value) for value in target],
            "click": True if click else False,
            "timestamp": utc_timestamp(),
            "snapshot": snapshot,
        })

    def failure_payload(self, original_error, failure_snapshot, pid):
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "case_name": self.case_name,
            "expected_document": self.expected_document,
            "pid": int(pid),
            "timestamp": utc_timestamp(),
            "input_method": "qt",
            "os_input_verified": False,
            "original_error": original_error,
            "mouse_events": [dict(event) for event in self.events],
            "failure_snapshot": failure_snapshot,
        }


def write_case_file(output_dir, case_name, payload):
    validate_case_name(case_name)
    directory = Path(output_dir) / "gui-diagnostics"
    directory.mkdir(parents=True, exist_ok=True)
    root = directory.resolve()
    destination = (directory / (case_name + ".json")).resolve()
    if destination.parent != root:
        raise ValueError("case path escapes diagnostics directory")
    if destination.exists():
        raise FileExistsError(str(destination))
    temporary = directory / (".diag-" + uuid.uuid4().hex + ".tmp")
    published = False
    try:
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            os.link(str(temporary), str(destination))
        except FileExistsError:
            raise
        except OSError as error:
            if destination.exists():
                raise FileExistsError(str(destination)) from error
            os.rename(str(temporary), str(destination))
        published = destination.exists()
        if not published:
            raise OSError("diagnostics file was not published")
        return destination
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                if not published:
                    raise
