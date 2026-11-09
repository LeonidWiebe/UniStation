import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "UniStation"))
from unistation.line import LineSession, PointResult
from test_line import Backend, Vector


class AxisFlow:
    def __init__(self):
        self.active = True
        self.events = []
        self.fail_confirm = False
        self.fail_base = False
        self.ends = 0

    def getPoint(self, **callbacks):
        self.callbacks = callbacks

    def isActive(self):
        return self.active

    def confirm(self, point):
        self.events.append(("confirm", (point.x, point.y, point.z)))
        if self.fail_confirm:
            raise RuntimeError("confirm failed")

    def setBasePoint(self, point):
        self.events.append(("setBasePoint", (point.x, point.y, point.z)))
        if self.fail_base:
            raise RuntimeError("base point failed")

    def endSession(self):
        self.ends += 1


class LineKeyinTests(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()
        self.axisflow = AxisFlow()
        self.session = LineSession(self.backend, self.axisflow)
        self.session.start()

    def test_first_keyin_point_syncs_in_confirm_then_base_order(self):
        point = Vector(1, 2, 3)

        result = self.session.submit_point(point)

        self.assertIs(result, PointResult.ACCEPTED)
        self.assertEqual(self.session.first.x, 1)
        self.assertEqual(self.axisflow.events, [
            ("confirm", (1, 2, 3)), ("setBasePoint", (1, 2, 3))])
        self.assertFalse(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_second_keyin_point_creates_once_without_axisflow_sync(self):
        self.assertIs(self.session.submit_point(Vector(1, 2, 3)),
                      PointResult.ACCEPTED)
        events_after_first = list(self.axisflow.events)

        result = self.session.submit_point(Vector(4, 6, 3))

        self.assertIs(result, PointResult.CREATED)
        self.assertEqual(self.axisflow.events, events_after_first)
        self.assertEqual(len(self.backend.created), 1)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.axisflow.ends, 1)

    def test_rejected_point_does_not_sync_or_replace_first_point(self):
        self.assertIs(self.session.submit_point(Vector(1, 2, 3)),
                      PointResult.ACCEPTED)
        first = self.session.first
        events_after_first = list(self.axisflow.events)

        result = self.session.submit_point(Vector(1, 2, 3))

        self.assertIs(result, PointResult.REJECTED)
        self.assertIs(self.session.first, first)
        self.assertEqual(self.axisflow.events, events_after_first)
        self.assertFalse(self.session.closed)
        self.assertEqual(self.backend.created, [])

        self.assertIs(self.session.submit_point(Vector(2, 2, 3)),
                      PointResult.CREATED)
        self.assertEqual(len(self.backend.created), 1)

    def test_axisflow_sync_failure_cancels_after_accepted_point(self):
        self.axisflow.fail_base = True

        result = self.session.submit_point(Vector(1, 2, 3))

        self.assertIs(result, PointResult.FAILED)
        self.assertEqual([name for name, _ in self.axisflow.events],
                         ["confirm", "setBasePoint"])
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])
        self.assertEqual(self.backend.closed, 1)
        self.assertEqual(self.axisflow.ends, 1)

    def test_backend_failure_returns_failed_and_closes_session(self):
        self.assertIs(self.session.submit_point(Vector(1, 2, 3)),
                      PointResult.ACCEPTED)
        self.backend.fail = True

        result = self.session.submit_point(Vector(2, 2, 3))

        self.assertIs(result, PointResult.FAILED)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_inactive_document_returns_closed_without_mutation(self):
        self.backend.live = False

        result = self.session.submit_point(Vector(1, 2, 3))

        self.assertIs(result, PointResult.CLOSED)
        self.assertIsNone(self.session.first)
        self.assertEqual(self.axisflow.events, [])
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)

    def test_inactive_axisflow_returns_closed_without_mutation(self):
        self.axisflow.active = False

        result = self.session.submit_point(Vector(1, 2, 3))

        self.assertIs(result, PointResult.CLOSED)
        self.assertIsNone(self.session.first)
        self.assertEqual(self.axisflow.events, [])
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)

    def test_callback_point_returns_explicit_result(self):
        result = self.axisflow.callbacks["callback"](Vector(1, 2, 3), True)
        self.assertIs(result, PointResult.ACCEPTED)

        result = self.axisflow.callbacks["callback"](Vector(1, 2, 3), True)
        self.assertIs(result, PointResult.REJECTED)

        result = self.axisflow.callbacks["callback"](Vector(2, 2, 3), True)
        self.assertIs(result, PointResult.CREATED)

        result = self.axisflow.callbacks["callback"](Vector(3, 2, 3), True)
        self.assertIs(result, PointResult.CLOSED)

    def test_confirm_failure_does_not_call_set_base_point(self):
        self.axisflow.fail_confirm = True

        result = self.session.submit_point(Vector(1, 2, 3))

        self.assertIs(result, PointResult.FAILED)
        self.assertEqual([name for name, _ in self.axisflow.events], ["confirm"])
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])


if __name__ == "__main__":
    unittest.main()
