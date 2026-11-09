"""Strict, dependency-free acceptance snapshots and offline transition checks."""
import argparse
import json
import math
import os
import tempfile
import time
from datetime import datetime, timezone


class ObservationError(Exception):
    """An observation is absent, malformed, stale, or otherwise unusable."""


_META = {"schema_version", "run_id", "scenario_id", "pid", "sequence",
         "observed_at", "monotonic_ns", "driver"}
_DRIVERS = {"unverified", "qt", "os"}


def _finite_num(v, label, minimum=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ObservationError(f"{label} must be a finite number")
    try: finite = math.isfinite(v)
    except (OverflowError, TypeError): finite = False
    if not finite: raise ObservationError(f"{label} must be a finite number")
    if minimum is not None and v < minimum:
        raise ObservationError(f"{label} must be >= {minimum}")
    return v


def _integer(v, label, minimum=None):
    if isinstance(v, bool) or not isinstance(v, int) or (minimum is not None and v < minimum):
        raise ObservationError(f"{label} must be an integer >= {minimum}")
    return v


def _triple(v, label):
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ObservationError(f"{label} must be a triple")
    return tuple(_finite_num(x, label) for x in v)


def _validate_geometry(s):
    for k in ("document_open", "session", "axisflow_active"):
        if not isinstance(s.get(k), bool):
            raise ObservationError(f"{k} must be bool")
    objects = s.get("objects")
    if not isinstance(objects, list):
        raise ObservationError("objects must be a list")
    names = set()
    for i, obj in enumerate(objects):
        p = f"objects[{i}]"
        if not isinstance(obj, dict):
            raise ObservationError(f"{p} must be an object")
        name = obj.get("name")
        if not isinstance(name, str) or not name:
            raise ObservationError(f"{p}.name must be nonempty")
        if name in names:
            raise ObservationError("duplicate object name")
        names.add(name)
        vertices = obj.get("vertices")
        if not isinstance(vertices, list) or any(not isinstance(v, (list, tuple)) or len(v) != 3 for v in vertices):
            raise ObservationError(p + ".vertices must be a list of triples")
        for v in vertices: _triple(v, p + ".vertices")
        _finite_num(obj.get("length"), p + ".length", 0)
        _triple(obj.get("placement_base"), p + ".placement_base")
        _integer(obj.get("edges"), p + ".edges", 0)
        if not isinstance(obj.get("valid"), bool):
            raise ObservationError(p + ".valid must be bool")
        if "radius" in obj:
            _finite_num(obj["radius"], p + ".radius", 0)
    if "first" in s: _triple(s["first"], "first")


def _parse_time(value):
    if not isinstance(value, str):
        raise ObservationError("observed_at must be an ISO timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise ObservationError("invalid observed_at") from e
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ObservationError("observed_at must include UTC offset")
    return dt.astimezone(timezone.utc)


def _validate_snapshot(s, run_id=None, scenario_id=None):
    if not isinstance(s, dict):
        raise ObservationError("snapshot must be an object")
    if type(s.get("schema_version")) is not int or s.get("schema_version") != 1:
        raise ObservationError("unsupported schema_version")
    for key, wanted in (("run_id", run_id), ("scenario_id", scenario_id)):
        val = s.get(key)
        if not isinstance(val, str) or not val or (wanted is not None and val != wanted):
            raise ObservationError(f"invalid {key}")
    _integer(s.get("pid"), "pid", 1)
    _integer(s.get("sequence"), "sequence", 1)
    _integer(s.get("monotonic_ns"), "monotonic_ns", 1)
    if not isinstance(s.get("driver"), str) or s.get("driver") not in _DRIVERS:
        raise ObservationError("invalid driver")
    _parse_time(s.get("observed_at"))
    _validate_geometry(s)
    if s.get("observation_error") not in (None, ""):
        raise ObservationError("observation_error is nonempty")
    return s


class SnapshotWriter:
    def __init__(self, output_path, run_id, scenario_id, driver="unverified"):
        if not isinstance(run_id, str) or not run_id or not isinstance(scenario_id, str) or not scenario_id:
            raise ValueError("run_id and scenario_id must be nonempty strings")
        if driver not in _DRIVERS:
            raise ValueError("driver must be unverified, qt, or os")
        self.output_path = os.fspath(output_path)
        self.run_id, self.scenario_id, self.driver = run_id, scenario_id, driver
        self.sequence = 0

    def write(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")
        overlap = _META.intersection(payload)
        if overlap:
            raise ValueError("payload contains reserved metadata: " + ", ".join(sorted(overlap)))
        seq = self.sequence + 1
        snap = dict(payload)
        snap.update(schema_version=1, run_id=self.run_id, scenario_id=self.scenario_id,
                    pid=os.getpid(), sequence=seq,
                    observed_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    monotonic_ns=__import__("time").monotonic_ns(), driver=self.driver)
        _validate_snapshot(snap, self.run_id, self.scenario_id)
        directory = os.path.dirname(os.path.abspath(self.output_path))
        fd, temp = tempfile.mkstemp(prefix=".acceptance-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            # Windows may briefly deny replacement while another reader holds
            # the destination open. Retry without ever truncating that file.
            for attempt in range(30):
                try:
                    os.replace(temp, self.output_path)
                    break
                except PermissionError:
                    if attempt == 29: raise
                    time.sleep(0.005)
        except BaseException:
            try:
                os.unlink(temp)
            except OSError:
                pass
            raise
        self.sequence = seq
        return snap


def read_snapshot(path, run_id, scenario_id, min_sequence=0, max_age_seconds=5, now=None):
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("run_id must be a nonempty string")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise ValueError("scenario_id must be a nonempty string")
    if isinstance(min_sequence, bool) or not isinstance(min_sequence, int) or min_sequence < 0:
        raise ValueError("min_sequence must be a nonnegative integer")
    if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, (int,float)) or not math.isfinite(max_age_seconds) or max_age_seconds < 0:
        raise ValueError("max_age_seconds must be finite and nonnegative")
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        _validate_snapshot(s, run_id, scenario_id)
        if s["sequence"] <= min_sequence:
            raise ObservationError("sequence is not newer than minimum")
        dt = _parse_time(s["observed_at"])
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        age = (current.astimezone(timezone.utc) - dt).total_seconds()
        if age < -1:
            raise ObservationError("observation is from the future")
        if age > max_age_seconds:
            raise ObservationError("observation is stale")
        return s
    except ObservationError:
        raise
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        raise ObservationError(str(e)) from e


def _close(a, b, tolerance):
    return math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance)


def _objmap(snapshot):
    return {o["name"]: o for o in snapshot["objects"]}


def _geometry_equal(a, b, tol):
    if set(a) != set(b):
        return False
    for n in a:
        x, y = a[n], b[n]
        if len(x["vertices"]) != len(y["vertices"]): return False
        for xv, yv in zip(x["vertices"], y["vertices"]):
            if any(not _close(u, v, tol) for u, v in zip(_triple(xv, "vertices"), _triple(yv, "vertices"))): return False
        if any(not _close(u, v, tol) for u, v in zip(_triple(x["placement_base"], "placement_base"), _triple(y["placement_base"], "placement_base"))): return False
        for field in ("length", "radius"):
            if (field in x) != (field in y): return False
            if field in x:
                if not _close(x[field], y[field], tol): return False
        for field in ("edges", "valid"):
            if x[field] != y[field]: return False
    return True


def _validate_expectation(expectation):
    if not isinstance(expectation, dict):
        raise ValueError("expectation must be an object")
    op = expectation.get("operation")
    if op not in ("line_created", "unchanged"):
        raise ValueError("invalid operation")
    allowed = {"operation", "document_open", "session", "axisflow_active"} | ({"start", "end"} if op == "line_created" else set())
    if set(expectation) != allowed:
        raise ValueError("expectation has missing or unknown keys")
    for key in ("document_open", "session", "axisflow_active"):
        if not isinstance(expectation.get(key), bool):
            raise ValueError(f"expectation.{key} must be bool")
    start = end = None
    if op == "line_created":
        try:
            start, end = _triple(expectation.get("start"), "start"), _triple(expectation.get("end"), "end")
            distance = math.dist(start, end)
        except (ObservationError, OverflowError, TypeError) as e:
            raise ValueError(str(e)) from e
        if not math.isfinite(distance) or distance == 0:
            raise ValueError("line endpoints must define a finite nonzero length")
    return op, start, end


def evaluate_transition(before, after, expectation, tolerance=1e-7):
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    op, start, end = _validate_expectation(expectation)
    distance = math.dist(start, end) if op == "line_created" else None
    checks, reasons = [], []
    try:
        _validate_snapshot(before); _validate_snapshot(after)
        if before["run_id"] != after["run_id"] or before["scenario_id"] != after["scenario_id"]:
            raise ObservationError("snapshot identity mismatch")
        if before["pid"] != after["pid"] or before["driver"] != after["driver"]:
            raise ObservationError("snapshot process or driver mismatch")
        if after["sequence"] <= before["sequence"] or after["monotonic_ns"] <= before["monotonic_ns"]:
            raise ObservationError("snapshot order is invalid")
        if _parse_time(after["observed_at"]) < _parse_time(before["observed_at"]):
            raise ObservationError("timestamp order is invalid")
    except ObservationError as e:
        return {"status":"blocked", "level":"state", "os_input_verified":False, "checks":checks, "reasons":[str(e)]}
    for k in ("document_open", "session", "axisflow_active"):
        ok = after[k] is expectation[k]
        checks.append({"name":k,"passed":ok})
        if not ok: reasons.append(f"{k} did not match expectation")
    a, b = _objmap(before), _objmap(after)
    if op == "unchanged":
        ok = _geometry_equal(a, b, tolerance)
        checks.append({"name":"geometry_unchanged","passed":ok})
        if not ok: reasons.append("geometry changed")
    else:
        old_same = _geometry_equal(a, {k:v for k,v in b.items() if k in a}, tolerance)
        new_names = set(b) - set(a)
        one = len(new_names) == 1
        checks.extend([{"name":"existing_geometry_unchanged","passed":old_same},{"name":"one_new_object","passed":one}])
        if not old_same: reasons.append("existing geometry changed")
        if not one: reasons.append("expected exactly one new object")
        if one:
            obj = b[next(iter(new_names))]
            verts = obj["vertices"]
            p1, p2 = (tuple(verts[0]), tuple(verts[1])) if len(verts)==2 else ((), ())
            valid = obj["valid"] is True and obj["edges"] == 1 and len(verts)==2
            order = valid and all(_close(x,y,tolerance) for x,y in zip(p1,start)) and all(_close(x,y,tolerance) for x,y in zip(p2,end))
            length = _close(obj["length"], distance, tolerance)
            for name, passed in (("new_line_valid",valid),("endpoints_match",order),("length_matches",length)):
                checks.append({"name":name,"passed":passed})
                if not passed: reasons.append(name.replace("_"," ")+" check failed")
    return {"status":"passed" if not reasons else "failed", "level":"state", "os_input_verified":False,"checks":checks,"reasons":reasons}


def _main(argv=None):
    class Parser(argparse.ArgumentParser):
        def error(self, message):
            raise ValueError(message)
    parser = Parser()
    parser.add_argument("--before", required=True); parser.add_argument("--after", required=True)
    parser.add_argument("--expectation", required=True); parser.add_argument("--output", required=True)
    try:
        args = parser.parse_args(argv)
    except ValueError:
        return 3
    expectation_error = None
    try:
        with open(args.expectation, encoding="utf-8") as f: expectation = json.load(f)
        _validate_expectation(expectation)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        expectation_error = str(e)
    if expectation_error is not None:
        report, code = {"status":"blocked","level":"state","os_input_verified":False,"checks":[],"reasons":[expectation_error]}, 3
    else:
      try:
        # IDs are anchored in the earlier snapshot, and checked against the after snapshot.
        with open(args.before, encoding="utf-8") as f: before = json.load(f)
        if not isinstance(before, dict): raise ObservationError("before snapshot must be an object")
        _validate_snapshot(before)
        with open(args.after, encoding="utf-8") as f: after = json.load(f)
        _validate_snapshot(after, before.get("run_id"), before.get("scenario_id"))
        report = evaluate_transition(before, after, expectation)
        report.update(source={"before":os.path.abspath(args.before),"after":os.path.abspath(args.after),"expectation":os.path.abspath(args.expectation)}, run_id=before["run_id"], scenario_id=before["scenario_id"])
        status = report["status"]
        code = {"passed":0,"failed":1,"blocked":2}[status]
      except (ObservationError, OSError, ValueError, json.JSONDecodeError) as e:
        report, code = {"status":"blocked","level":"state","os_input_verified":False,"checks":[],"reasons":[str(e)]}, 2
    report.setdefault("source", {"before":os.path.abspath(args.before),"after":os.path.abspath(args.after),"expectation":os.path.abspath(args.expectation)})
    folder = os.path.dirname(os.path.abspath(args.output)); fd, tmp = tempfile.mkstemp(prefix=".report-", dir=folder)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(report,f,allow_nan=False,ensure_ascii=False,indent=2); f.write("\n")
        os.replace(tmp,args.output)
    except BaseException:
        try: os.unlink(tmp)
        except OSError: pass
        raise
    return code


if __name__ == "__main__":
    raise SystemExit(_main())
