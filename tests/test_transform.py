import unittest
from types import SimpleNamespace
from test_line import Backend, Vector
from unistation.transform import TransformSession


class TransformBackend(Backend):
    def __init__(self):
        super().__init__()
        self.queue = []

    def defer(self, callback):
        self.queue.append(callback)

    def transform(self, delta, copy):
        if self.fail:
            raise RuntimeError("injected failure")
        self.created.append((delta, copy))

    def preview_transform(self, delta):
        self.delta = delta

    def hide_ghost(self):
        self.delta = None


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.backend = TransformBackend()
        self.ends = 0
        self.api = SimpleNamespace(getPoint=lambda **kw: None, endSession=self.end)
        self.session = TransformSession(self.backend, self.api)
        self.session.start()

    def end(self):
        self.ends += 1

    def seed(self):
        self.session.point(Vector(1, 2, 3), True)
        self.session.point(Vector(4, 6, 3), True)

    def test_deferred_move_exactly_once(self):
        self.seed()
        self.session.point(Vector(100), True)
        self.assertEqual(self.backend.created, [])
        self.assertEqual(len(self.backend.queue), 1)
        self.backend.queue[0]()
        self.backend.queue[0]()
        self.assertEqual(len(self.backend.created), 1)
        delta, copy = self.backend.created[0]
        self.assertEqual(delta.Length, 5)
        self.assertFalse(copy)
        self.assertEqual(self.ends, 1)

    def test_copy_mode(self):
        self.session.copy = True
        self.seed()
        self.backend.queue[0]()
        self.assertTrue(self.backend.created[0][1])

    def test_cancel_pending_commit(self):
        self.seed()
        self.session.cancel()
        self.backend.queue[0]()
        self.assertEqual(self.backend.created, [])

    def test_document_change_pending_commit(self):
        self.seed()
        self.backend.live = False
        self.backend.queue[0]()
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_zero_and_invalid_retry(self):
        self.session.point(Vector(float('nan')), True)
        self.assertIsNone(self.session.first)
        self.session.point(Vector(0), True)
        self.session.point(Vector(0), True)
        self.assertFalse(self.session.pending)
        self.session.point(Vector(5), True)
        self.assertTrue(self.session.pending)

    def test_base_copied_preview_invalid_cleared(self):
        point = Vector(1)
        self.session.point(point, True)
        point.x = 99
        self.session.move(Vector(5))
        self.assertEqual(self.backend.delta.x, 4)
        self.session.move(Vector(float('inf')))
        self.assertIsNone(self.backend.delta)

    def test_finish_discards(self):
        self.session.point(Vector(0), True)
        self.session.finish()
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.queue, [])

    def test_failure_releases(self):
        self.seed()
        self.backend.fail = True
        self.backend.queue[0]()
        self.assertEqual(self.ends, 1)
        self.assertTrue(self.backend.errors)
