import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "UniStation"))
from unistation.line import LineSession


class Vector:
    def __init__(self, x, y=0, z=0):
        self.x, self.y, self.z = x, y, z

    def __sub__(self, other):
        return Vector(self.x-other.x, self.y-other.y, self.z-other.z)

    @property
    def Length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)


class Backend:
    tolerance = 1e-7

    def __init__(self):
        self.live = True
        self.created = []
        self.errors = []
        self.closed = 0
        self.fail = False

    def alive(self):
        return self.live

    def copy_point(self, point):
        return Vector(point.x, point.y, point.z)

    def create_line(self, first, last):
        if self.fail:
            raise RuntimeError("injected failure")
        self.created.append((first, last))

    def preview(self, first, last):
        pass

    def report(self, error):
        self.errors.append(error)

    def close(self):
        self.closed += 1


class LineTests(unittest.TestCase):
    def setUp(self):
        self.backend = Backend()
        self.ends = 0
        self.api = SimpleNamespace(getPoint=self.capture, endSession=self.end)
        self.session = LineSession(self.backend, self.api)
        self.session.start()

    def capture(self, **kwargs):
        self.callbacks = kwargs

    def end(self):
        self.ends += 1

    def test_two_points_one_line_and_late_callback_ignored(self):
        self.session.point(Vector(1, 2, 3), True)
        self.session.point(Vector(4, 6, 3), True)
        self.session.point(Vector(9), True)
        self.assertEqual(len(self.backend.created), 1)
        self.assertEqual((self.backend.created[0][1] -
                          self.backend.created[0][0]).Length, 5)
        self.assertEqual(self.ends, 1)

    def test_cancel_never_creates_partial_line(self):
        self.session.point(Vector(1), True)
        self.callbacks["finishcallback"]()
        self.session.cancel()
        self.assertEqual(self.backend.created, [])
        self.assertEqual(self.backend.closed, 1)
        self.assertEqual(self.ends, 1)

    def test_axisflow_cancel(self):
        self.callbacks["callback"](None, False)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_document_switch(self):
        self.session.point(Vector(1), True)
        self.backend.live = False
        self.session.point(Vector(2), True)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_degenerate_point_can_be_retried(self):
        self.session.point(Vector(1), True)
        self.session.point(Vector(1 + 1e-9), True)
        self.assertFalse(self.session.closed)
        self.session.point(Vector(2), True)
        self.assertEqual(len(self.backend.created), 1)

    def test_nonfinite_rejected(self):
        self.session.point(Vector(float("nan")), True)
        self.assertIsNone(self.session.first)
        self.assertTrue(self.backend.errors)

    def test_geometry_failure_cleans_input(self):
        self.backend.fail = True
        self.session.point(Vector(1), True)
        self.session.point(Vector(2), True)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.ends, 1)
        self.assertTrue(self.backend.errors)

    def test_first_point_is_copied(self):
        first = Vector(1)
        self.session.point(first, True)
        first.x = 99
        self.session.point(Vector(2), True)
        self.assertEqual(self.backend.created[0][0].x, 1)

    def test_start_failure_releases_resources(self):
        def fail(**kwargs):
            raise RuntimeError("no view")
        backend = Backend()
        session = LineSession(backend, SimpleNamespace(
            getPoint=fail, endSession=self.end))
        with self.assertRaises(RuntimeError):
            session.start()
        self.assertTrue(session.closed)
        self.assertEqual(backend.closed, 1)

    def test_working_plane_origin_is_seed_not_first_vertex(self):
        origin = Vector(5, 10, 25)
        session = LineSession(self.backend, self.api, origin=origin)
        session.start()
        self.assertIs(self.callbacks["last"], origin)
        self.assertIsNone(session.first)
        self.assertEqual(self.backend.created, [])


if __name__ == "__main__":
    unittest.main()
