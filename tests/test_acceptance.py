import json
import math
import os
import sys
import tempfile
import threading
import unittest
import subprocess
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools"))
import acceptance


def snap(seq=1, objects=None, **extra):
    d = dict(schema_version=1, run_id="r", scenario_id="s", pid=1, sequence=seq,
             observed_at=datetime.now(timezone.utc).isoformat(), monotonic_ns=100+seq,
             driver="unverified", document_open=True, session=True, axisflow_active=True,
             objects=[] if objects is None else objects)
    d.update(extra)
    return d


def obj(name="Line", verts=None, length=5):
    return dict(name=name, vertices=verts or [[0,0,0],[3,4,0]], length=length,
                placement_base=[0,0,0], edges=1, valid=True)


def expect(op="line_created", **kw):
    d = dict(operation=op, document_open=True, session=True, axisflow_active=True)
    if op == "line_created": d.update(start=[0,0,0], end=[3,4,0])
    d.update(kw)
    return d


class AcceptanceTests(unittest.TestCase):
    def test_writer_atomic_metadata_and_payload_validation(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,"snap.json")
            w=acceptance.SnapshotWriter(p,"r","s")
            first=w.write(dict(document_open=True,session=True,axisflow_active=True,objects=[]))
            with open(p) as f: self.assertEqual(json.load(f),first)
            self.assertEqual(first["sequence"],1)
            with open(p,"rb") as f: before=f.read()
            with self.assertRaises(ValueError):
                w.write(dict(document_open=True,session=True,axisflow_active=True,objects=[],pid=2))
            with open(p,"rb") as f: self.assertEqual(f.read(),before)
            with self.assertRaises(acceptance.ObservationError):
                w.write(dict(document_open=True,session=True,axisflow_active=True,objects=[obj(verts=[[math.nan,0,0]])]))
            with open(p,"rb") as f: self.assertEqual(f.read(),before)
            self.assertEqual(w.sequence,1)
            self.assertEqual(os.listdir(d),["snap.json"])

    def test_concurrent_reader_sees_only_complete_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,"snap.json")
            w=acceptance.SnapshotWriter(p,"r","s")
            payload=dict(document_open=True,session=True,axisflow_active=True,objects=[])
            w.write(payload); errors=[]; stop=threading.Event()
            def read_loop():
                while not stop.is_set():
                    try:
                        with open(p,encoding="utf-8") as f: acceptance._validate_snapshot(json.load(f))
                    except PermissionError:
                        continue
                    except Exception as e: errors.append(e); stop.set()
            t=threading.Thread(target=read_loop); t.start()
            try:
                for _ in range(150): w.write(payload)
            finally:
                stop.set(); t.join(timeout=3)
            self.assertFalse(t.is_alive())
            self.assertEqual(errors,[])

    def test_writer_replace_and_serialization_failures_preserve_old_file(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,"s.json"); w=acceptance.SnapshotWriter(p,"r","s")
            payload=dict(document_open=True,session=True,axisflow_active=True,objects=[])
            w.write(payload)
            with open(p,"rb") as f: old=f.read()
            with patch.object(acceptance.os,"replace",side_effect=OSError("replace failed")):
                with self.assertRaises(OSError): w.write(payload)
            with open(p,"rb") as f: self.assertEqual(f.read(),old)
            self.assertEqual(w.sequence,1); self.assertEqual(os.listdir(d),["s.json"])
            with patch.object(acceptance.json,"dump",side_effect=OSError("dump failed")):
                with self.assertRaises(OSError): w.write(payload)
            with open(p,"rb") as f: self.assertEqual(f.read(),old)
            self.assertEqual(w.sequence,1); self.assertEqual(os.listdir(d),["s.json"])

    def test_validator_rejects_bad_schema_ids_stale_future_nonfinite_duplicates_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            p=os.path.join(d,"s.json")
            def check(s, **kwargs):
                with open(p,"w") as f: json.dump(s,f,allow_nan=True)
                with self.assertRaises(acceptance.ObservationError): acceptance.read_snapshot(p,"r","s",**kwargs)
            for change in (dict(schema_version=2),dict(run_id="wrong"),dict(sequence=True),
                           dict(observed_at=(datetime.now(timezone.utc)-timedelta(seconds=60)).isoformat()),
                           dict(observed_at=(datetime.now(timezone.utc)+timedelta(seconds=5)).isoformat()),
                           dict(objects=[obj(),obj()])):
                s=snap(); s.update(change); check(s)
            s=snap(objects=[obj(verts=[[float("nan"),0,0]])]); check(s)
            with open(p,"w") as f: f.write('{"document_open":true}')
            with self.assertRaises(acceptance.ObservationError): acceptance.read_snapshot(p,"r","s")

    def test_line_pass_and_failure_modes(self):
        b=snap(); a=snap(2,[obj()])
        self.assertEqual(acceptance.evaluate_transition(b,a,expect())["status"],"passed")
        bad=snap(2,[obj(verts=[[0,0,0],[3,4,1]],length=math.sqrt(26))])
        self.assertEqual(acceptance.evaluate_transition(b,bad,expect())["status"],"failed")
        self.assertEqual(acceptance.evaluate_transition(b,snap(2,[obj(),obj("Other")]),expect())["status"],"failed")
        old=obj("Old"); changed=obj("Old",[[0,0,0],[3,4,1]],math.sqrt(26))
        self.assertEqual(acceptance.evaluate_transition(snap(objects=[old]),snap(2,[changed,obj()]),expect())["status"],"failed")

    def test_unchanged_and_stale_order_and_expectation(self):
        before = snap(1, observed_at="2026-10-28T09:00:00+00:00")
        after = snap(2, observed_at="2026-10-28T09:00:01+00:00")
        self.assertLess(before["sequence"], after["sequence"])
        self.assertLess(before["monotonic_ns"], after["monotonic_ns"])
        self.assertLess(before["observed_at"], after["observed_at"])
        passed = acceptance.evaluate_transition(before, after, expect("unchanged"))
        self.assertEqual(passed["status"], "passed")
        self.assertEqual(passed["reasons"], [])
        with self.assertRaises(ValueError):
            acceptance.evaluate_transition(before, after, {"operation": "line_created"})
        stale_sequence = snap(1, observed_at="2026-10-28T09:00:01+00:00",
                               monotonic_ns=before["monotonic_ns"] + 1)
        self.assertFalse(stale_sequence["sequence"] > before["sequence"])
        self.assertGreater(stale_sequence["monotonic_ns"], before["monotonic_ns"])
        self.assertGreater(stale_sequence["observed_at"], before["observed_at"])
        report = acceptance.evaluate_transition(before, stale_sequence, expect("unchanged"))
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["reasons"], ["snapshot order is invalid"])
        stale_monotonic = snap(2, observed_at="2026-10-28T09:00:01+00:00",
                                monotonic_ns=before["monotonic_ns"])
        self.assertGreater(stale_monotonic["sequence"], before["sequence"])
        self.assertFalse(stale_monotonic["monotonic_ns"] > before["monotonic_ns"])
        self.assertGreater(stale_monotonic["observed_at"], before["observed_at"])
        report = acceptance.evaluate_transition(before, stale_monotonic, expect("unchanged"))
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["reasons"], ["snapshot order is invalid"])
        earlier = snap(2, observed_at="2026-10-28T08:59:59+00:00")
        self.assertGreater(earlier["sequence"], before["sequence"])
        self.assertGreater(earlier["monotonic_ns"], before["monotonic_ns"])
        self.assertLess(earlier["observed_at"], before["observed_at"])
        report = acceptance.evaluate_transition(before, earlier, expect("unchanged"))
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["reasons"], ["timestamp order is invalid"])

    def test_strict_metadata_geometry_and_evaluator_identity(self):
        for run_id, scenario_id in ((None, "s"), ("", "s"), ("r", None), ("r", "")):
            with self.assertRaises(ValueError): acceptance.read_snapshot("absent", run_id, scenario_id)
        for changes in (dict(schema_version=1.0), dict(driver=[]), dict(first=[1,2]),
                        dict(objects=[dict(obj(), radius=None)])):
            s=snap(); s.update(changes)
            with self.assertRaises(acceptance.ObservationError): acceptance._validate_snapshot(s)
        with self.assertRaises(acceptance.ObservationError): acceptance._validate_snapshot(snap(objects=[obj(length=10**10000)]))
        with self.assertRaises(ValueError): acceptance.read_snapshot("absent", "r", "s", max_age_seconds=float("nan"))
        a=snap(2); a["pid"]=2
        self.assertEqual(acceptance.evaluate_transition(snap(),a,expect("unchanged"))["status"],"blocked")
        with self.assertRaises(ValueError): acceptance.evaluate_transition(snap(),snap(2),expect("unchanged", typo=True))
        with self.assertRaises(ValueError): acceptance.evaluate_transition(snap(),snap(2),expect(start=[0,0,0],end=[0,0,0]))

    def test_cli_exit_codes_reports_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            before=os.path.join(d,"before.json"); after=os.path.join(d,"after.json")
            exp=os.path.join(d,"expect.json"); out=os.path.join(d,"report.json")
            def dump(path,data):
                with open(path,"w",encoding="utf-8") as f: json.dump(data,f)
            dump(before,snap()); dump(after,snap(2,[obj()])); dump(exp,expect())
            script=os.path.join(os.path.dirname(os.path.dirname(__file__)),"tools","acceptance.py")
            cmd=[sys.executable,"-B",script,"--before",before,"--after",after,"--expectation",exp,"--output",out]
            def run(): return subprocess.run(cmd,capture_output=True,text=True).returncode
            def report():
                with open(out,encoding="utf-8") as f: return json.load(f)
            self.assertEqual(run(),0); self.assertEqual(report()["status"],"passed")
            dump(after,snap(2)); self.assertEqual(run(),1)
            dump(before,{"legacy":True}); self.assertEqual(run(),2)
            with open(before,"w",encoding="utf-8") as f: f.write("{")
            self.assertEqual(run(),2); self.assertIn("source",report())
            dump(before,snap()); dump(exp,dict(expect(),start=[1,2]))
            self.assertEqual(run(),3); self.assertIn("source",report())
            os.unlink(exp); self.assertEqual(run(),3); self.assertIn("source",report())
            self.assertEqual(subprocess.run([sys.executable,"-B",script],capture_output=True).returncode,3)


if __name__ == "__main__": unittest.main()
