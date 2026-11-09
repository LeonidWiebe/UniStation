import unittest
from types import SimpleNamespace
from test_line import Backend, Vector
from unistation.arc import ArcSession


class ArcBackend(Backend):
    def clear_preview(self):
        self.preview_points = None

    def preview_arc(self, *points):
        self.preview_points = points

    def create_arc(self, *points):
        if self.fail:
            raise RuntimeError("injected failure")
        self.created.append(points)


class ArcTests(unittest.TestCase):
    def setUp(self):
        self.backend = ArcBackend()
        self.ends = 0
        self.api = SimpleNamespace(getPoint=self.capture, endSession=self.end)
        self.session = ArcSession(self.backend, self.api)
        self.session.start()

    def capture(self, **kwargs):
        self.callbacks = kwargs

    def end(self):
        self.ends += 1

    def seed(self):
        self.session.point(Vector(0), True)
        self.session.point(Vector(5, 5), True)

    def test_three_points_copied_once(self):
        first = Vector(0)
        self.session.point(first, True)
        first.x = 99
        self.session.point(Vector(5, 5), True)
        self.assertEqual(self.backend.created, [])
        self.session.point(Vector(10), True)
        self.session.point(Vector(20), True)
        self.assertEqual(len(self.backend.created), 1)
        self.assertEqual(self.backend.created[0][0].x, 0)
        self.assertEqual(self.ends, 1)

    def test_duplicates_and_collinear_retry(self):
        self.seed()
        for p in (Vector(0), Vector(5, 5), Vector(10, 10), Vector(10, 10+1e-9)):
            self.session.point(p, True)
        self.assertEqual(len(self.session.points), 2)
        self.assertFalse(self.session.closed)
        self.session.point(Vector(10), True)
        self.assertEqual(len(self.backend.created), 1)

    def test_invalid_plane_and_nonfinite(self):
        for p in (Vector(float('nan')), Vector(float('inf')), Vector(0, 0, 5)):
            self.session.point(p, True)
        self.assertEqual(self.session.points, [])

    def test_cancel_two_points_no_geometry(self):
        self.seed()
        self.callbacks['finishcallback']()
        self.session.cancel()
        self.assertEqual(self.backend.created, [])
        self.assertEqual(self.ends, 1)

    def test_false_callback_cancels(self):
        self.seed()
        self.callbacks['callback'](None, False)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_preview_cleared_when_collinear(self):
        self.seed()
        self.session.move(Vector(10))
        self.assertEqual(len(self.backend.preview_points), 3)
        self.session.move(Vector(10, 10))
        self.assertIsNone(self.backend.preview_points)

    def test_document_switch(self):
        self.seed()
        self.backend.live = False
        self.session.point(Vector(10), True)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_factory_failure(self):
        self.seed()
        self.backend.fail = True
        self.session.point(Vector(10), True)
        self.assertTrue(self.backend.errors)
        self.assertEqual(self.backend.closed, 1)
