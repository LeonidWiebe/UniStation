import unittest
from types import SimpleNamespace
from test_line import Backend, Vector
from unistation.line import PointResult
from unistation.wire import WireSession


class WireBackend(Backend):
    def preview_wire(self, points, cursor):
        self.preview_points = list(points)
        self.preview_cursor = cursor

    def create_wire(self, points, closed):
        if self.fail:
            raise RuntimeError("injected failure")
        self.created.append((list(points), closed))


class WireTests(unittest.TestCase):
    def setUp(self):
        self.backend = WireBackend()
        self.ends = 0
        self.api = SimpleNamespace(getPoint=self.capture, endSession=self.end)
        self.session = WireSession(self.backend, self.api)
        self.session.start()

    def capture(self, **kwargs):
        self.callbacks = kwargs

    def end(self):
        self.ends += 1

    def add(self, *points):
        for point in points:
            self.session.point(point, True)

    def test_finish_commits_all_points_once(self):
        self.add(Vector(0), Vector(10), Vector(10, 5))
        self.assertEqual(self.backend.created, [])
        self.callbacks['finishcallback']()
        self.session.finish()
        self.session.point(Vector(20), True)
        self.assertEqual(len(self.backend.created), 1)
        self.assertEqual(len(self.backend.created[0][0]), 3)
        self.assertFalse(self.backend.created[0][1])
        self.assertEqual(self.ends, 1)

    def test_close_by_first_point_does_not_duplicate_vertex(self):
        self.add(Vector(0), Vector(10), Vector(10, 5), Vector(0))
        self.assertEqual(len(self.backend.created[0][0]), 3)
        self.assertTrue(self.backend.created[0][1])

    def test_early_close_can_be_retried(self):
        self.add(Vector(0), Vector(10), Vector(0))
        self.assertFalse(self.session.closed)
        self.add(Vector(10, 5))
        self.session.close_contour()
        self.assertTrue(self.backend.created[0][1])

    def test_cancel_discards_multiple_points(self):
        self.add(Vector(0), Vector(10), Vector(10, 5))
        self.callbacks['callback'](None, False)
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)

    def test_finish_insufficient_points_discards(self):
        self.add(Vector(0))
        self.session.finish()
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)

    def test_invalid_and_duplicate_points_do_not_accumulate(self):
        point = Vector(0)
        self.add(point)
        point.x = 99
        self.add(Vector(0), Vector(float('nan')), Vector(10))
        self.assertEqual(len(self.session.points), 2)
        self.assertEqual(self.session.points[0].x, 0)

    def test_document_switch_does_not_commit(self):
        self.add(Vector(0), Vector(10))
        self.backend.live = False
        self.session.finish()
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_creation_failure_releases_session(self):
        self.add(Vector(0), Vector(10))
        self.backend.fail = True
        self.session.finish()
        self.assertEqual(self.backend.closed, 1)
        self.assertEqual(self.ends, 1)
        self.assertTrue(self.backend.errors)


class AxisFlow:
    def __init__(self):
        self.active = True
        self.events = []
        self.fail_active = False
        self.fail_confirm = False
        self.fail_base = False
        self.ends = 0

    def getPoint(self, **callbacks):
        self.callbacks = callbacks

    def isActive(self):
        if self.fail_active:
            raise RuntimeError("activity failed")
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


def coordinates(points):
    return [(point.x, point.y, point.z) for point in points]


class WireResultTests(unittest.TestCase):
    def setUp(self):
        self.backend = WireBackend()
        self.axisflow = AxisFlow()
        self.session = WireSession(self.backend, self.axisflow)
        self.session.start()

    def test_accepted_points_are_copied_and_not_created_before_finish(self):
        first = Vector(1, 2, 3)
        second = Vector(4, 2, 3)

        self.assertIs(self.session.submit_point(first), PointResult.ACCEPTED)
        first.x = 99
        self.assertIs(self.session.submit_point(second), PointResult.ACCEPTED)

        self.assertEqual(coordinates(self.session.points), [(1, 2, 3), (4, 2, 3)])
        self.assertEqual(coordinates([self.session.first]), [(1, 2, 3)])
        self.assertIs(self.session.first, self.session.points[0])
        self.assertEqual(self.backend.created, [])
        self.assertEqual(self.backend.preview_cursor, None)
        self.assertEqual(coordinates(self.backend.preview_points), [(1, 2, 3), (4, 2, 3)])
        self.assertFalse(self.session.closed)
        self.assertEqual(self.session.last_error, "")

    def test_submit_syncs_each_accepted_point_but_callback_does_not(self):
        self.assertIs(self.axisflow.callbacks["callback"](Vector(1, 2, 3), True),
                      PointResult.ACCEPTED)
        self.assertEqual(self.axisflow.events, [])

        self.assertIs(self.session.submit_point(Vector(4, 0, 0)), PointResult.ACCEPTED)
        self.assertIs(self.session.submit_point(Vector(4, 5, 0)), PointResult.ACCEPTED)

        self.assertEqual(self.axisflow.events, [
            ("confirm", (4, 0, 0)),
            ("setBasePoint", (4, 0, 0)),
            ("confirm", (4, 5, 0)),
            ("setBasePoint", (4, 5, 0)),
        ])
        self.assertEqual(self.backend.created, [])
        self.assertEqual(len(self.session.points), 3)

    def test_rejected_points_do_not_change_geometry_or_sync(self):
        self.assertIs(self.session.submit_point(Vector(0, 0, 0)), PointResult.ACCEPTED)
        self.assertIs(self.session.submit_point(Vector(10, 0, 0)), PointResult.ACCEPTED)
        saved_points = coordinates(self.session.points)
        saved_first = coordinates([self.session.first])
        saved_events = list(self.axisflow.events)

        cases = (
            (Vector(float("nan"), 0, 0), "Coordinates must be finite."),
            (Vector(float("inf"), 0, 0), "Coordinates must be finite."),
            (Vector(1e308, 0, 0), "Segment length must be finite."),
            (Vector(10, 0, 0), "Choose a different next point."),
            (Vector(0, 0, 0), "A closed contour needs at least three points."),
        )
        for point, message in cases:
            result = self.session.submit_point(point)
            self.assertIs(result, PointResult.REJECTED)
            self.assertEqual(self.session.last_error, message)
            self.assertEqual(self.backend.errors[-1], message)
            self.assertEqual(coordinates(self.session.points), saved_points)
            self.assertEqual(coordinates([self.session.first]), saved_first)
            self.assertEqual(self.axisflow.events, saved_events)
            self.assertEqual(self.backend.created, [])
            self.assertFalse(self.session.closed)

    def test_correction_after_rejection_clears_last_error(self):
        self.assertIs(self.session.submit_point(Vector(0, 0, 0)), PointResult.ACCEPTED)
        self.assertIs(self.session.submit_point(Vector(0, 0, 0)), PointResult.REJECTED)
        self.assertNotEqual(self.session.last_error, "")

        result = self.session.submit_point(Vector(3, 0, 0))

        self.assertIs(result, PointResult.ACCEPTED)
        self.assertEqual(self.session.last_error, "")
        self.assertEqual(coordinates(self.session.points), [(0, 0, 0), (3, 0, 0)])
        self.assertEqual(self.axisflow.events[-2:], [
            ("confirm", (3, 0, 0)), ("setBasePoint", (3, 0, 0))])

    def test_completion_creates_once_and_repeat_is_closed(self):
        self.session.submit_point(Vector(0, 0, 0))
        self.session.submit_point(Vector(10, 0, 0))
        self.session.submit_point(Vector(10, 5, 0))
        events = list(self.axisflow.events)

        closed = self.session.submit_point(Vector(0, 0, 0))

        self.assertIs(closed, PointResult.CREATED)
        self.assertEqual(coordinates(self.backend.created[0][0]),
                         [(0, 0, 0), (10, 0, 0), (10, 5, 0)])
        self.assertTrue(self.backend.created[0][1])
        self.assertEqual(self.axisflow.events, events)
        self.assertEqual(self.axisflow.ends, 1)
        self.assertEqual(self.backend.closed, 1)
        self.assertIs(self.session.submit_point(Vector(1, 1, 0)), PointResult.CLOSED)
        self.assertIs(self.session.finish(), PointResult.CLOSED)
        self.assertIs(self.session.close_contour(), PointResult.CLOSED)
        self.assertEqual(len(self.backend.created), 1)
        self.assertEqual(self.axisflow.events, events)
        self.assertEqual(self.axisflow.ends, 1)

    def test_finish_and_close_button_create_once(self):
        self.session.submit_point(Vector(0, 0, 0))
        self.session.submit_point(Vector(8, 0, 0))
        events = list(self.axisflow.events)

        finished = self.session.finish()

        self.assertIs(finished, PointResult.CREATED)
        self.assertEqual(coordinates(self.backend.created[0][0]), [(0, 0, 0), (8, 0, 0)])
        self.assertFalse(self.backend.created[0][1])
        self.assertEqual(self.axisflow.events, events)
        self.assertEqual(self.axisflow.ends, 1)
        self.assertEqual(self.backend.closed, 1)
        self.assertIs(self.session.finish(), PointResult.CLOSED)
        self.assertEqual(len(self.backend.created), 1)

        other = WireSession(WireBackend(), AxisFlow())
        other.start()
        other.point(Vector(0, 0, 0), True)
        other.point(Vector(2, 0, 0), True)
        other.point(Vector(2, 2, 0), True)
        created = other.close_contour()
        self.assertIs(created, PointResult.CREATED)
        self.assertEqual(coordinates(other.backend.created[0][0]),
                         [(0, 0, 0), (2, 0, 0), (2, 2, 0)])
        self.assertTrue(other.backend.created[0][1])
        self.assertEqual(other.axisflow.events, [])
        self.assertEqual(other.axisflow.ends, 1)
        self.assertEqual(other.backend.closed, 1)
        self.assertIs(other.close_contour(), PointResult.CLOSED)
        self.assertEqual(len(other.backend.created), 1)
        self.assertEqual(other.axisflow.ends, 1)

    def test_terminal_failures_report_and_block_further_work(self):
        self.backend.fail = True
        self.session.point(Vector(0, 0, 0), True)
        self.session.point(Vector(1, 0, 0), True)
        created = self.session.finish()
        self.assertIs(created, PointResult.FAILED)
        self.assertEqual(self.session.last_error, "Wire creation failed: injected failure")
        self.assertEqual(self.backend.errors[-1], self.session.last_error)
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)
        self.assertEqual(self.axisflow.ends, 1)
        self.assertEqual(self.backend.closed, 1)
        self.assertEqual(self.axisflow.events, [])
        self.assertIs(self.session.finish(), PointResult.CLOSED)
        self.assertIs(self.session.submit_point(Vector(2, 0, 0)), PointResult.CLOSED)
        self.assertEqual(self.axisflow.ends, 1)
        self.assertEqual(self.backend.created, [])
        self.assertEqual(self.axisflow.events, [])

        preview = WireSession(WireBackend(), AxisFlow())
        preview.start()

        def fail_preview(points, cursor):
            raise RuntimeError("preview failed")

        preview.backend.preview_wire = fail_preview
        result = preview.submit_point(Vector(1, 2, 3))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(preview.last_error, "Preview failed: preview failed")
        self.assertEqual(preview.backend.errors[-1], preview.last_error)
        self.assertTrue(preview.closed)
        self.assertEqual(preview.axisflow.events, [])
        self.assertEqual(preview.axisflow.ends, 1)
        self.assertIs(preview.submit_point(Vector(4, 2, 3)), PointResult.CLOSED)
        self.assertEqual(preview.axisflow.events, [])
        self.assertEqual(preview.axisflow.ends, 1)

        inactive_check = WireSession(WireBackend(), AxisFlow())
        inactive_check.start()
        inactive_check.axisflow.fail_active = True
        result = inactive_check.submit_point(Vector(1, 0, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(inactive_check.last_error, "AxisFlow activity check failed: activity failed")
        self.assertEqual(inactive_check.backend.errors[-1], inactive_check.last_error)
        self.assertEqual(inactive_check.points, [])
        self.assertTrue(inactive_check.closed)
        self.assertEqual(inactive_check.axisflow.events, [])
        self.assertIs(inactive_check.submit_point(Vector(2, 0, 0)), PointResult.CLOSED)
        self.assertEqual(inactive_check.axisflow.ends, 1)

        confirm = WireSession(WireBackend(), AxisFlow())
        confirm.start()
        confirm.axisflow.fail_confirm = True
        result = confirm.submit_point(Vector(5, 0, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(confirm.last_error, "AxisFlow synchronization failed: confirm failed")
        self.assertEqual([name for name, _ in confirm.axisflow.events], ["confirm"])
        self.assertTrue(confirm.closed)
        self.assertEqual(confirm.backend.created, [])
        self.assertIs(confirm.submit_point(Vector(6, 0, 0)), PointResult.CLOSED)
        self.assertEqual([name for name, _ in confirm.axisflow.events], ["confirm"])
        self.assertEqual(confirm.axisflow.ends, 1)

        base = WireSession(WireBackend(), AxisFlow())
        base.start()
        base.axisflow.fail_base = True
        result = base.submit_point(Vector(7, 1, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(base.last_error, "AxisFlow synchronization failed: base point failed")
        self.assertEqual([name for name, _ in base.axisflow.events],
                         ["confirm", "setBasePoint"])
        self.assertTrue(base.closed)
        self.assertIs(base.submit_point(Vector(8, 1, 0)), PointResult.CLOSED)
        self.assertEqual(len(base.axisflow.events), 2)
        self.assertEqual(base.axisflow.ends, 1)
        self.assertEqual(base.backend.created, [])

    def test_inactive_axisflow_and_dead_backend_close_without_points(self):
        self.axisflow.active = False
        result = self.session.submit_point(Vector(1, 2, 3))
        self.assertIs(result, PointResult.CLOSED)
        self.assertEqual(self.session.points, [])
        self.assertIsNone(self.session.first)
        self.assertEqual(self.axisflow.events, [])
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)
        self.assertEqual(self.axisflow.ends, 1)

        dead = WireSession(WireBackend(), AxisFlow())
        dead.start()
        dead.backend.live = False
        result = dead.submit_point(Vector(1, 2, 3))
        self.assertIs(result, PointResult.CLOSED)
        self.assertEqual(dead.points, [])
        self.assertEqual(dead.axisflow.events, [])
        self.assertEqual(dead.backend.created, [])
        self.assertTrue(dead.closed)

        done = WireSession(WireBackend(), AxisFlow())
        done.start()
        done.point(Vector(0, 0, 0), True)
        done.point(Vector(2, 0, 0), True)
        self.assertIs(done.finish(), PointResult.CREATED)
        self.assertIs(done.submit_point(Vector(3, 0, 0)), PointResult.CLOSED)
        self.assertEqual(len(done.points), 2)
        self.assertEqual(done.axisflow.events, [])
        self.assertEqual(len(done.backend.created), 1)

    def test_cancel_and_closed_callback_do_not_sync(self):
        self.assertIs(self.session.submit_point(Vector(1, 0, 0)), PointResult.ACCEPTED)
        result = self.session.point(Vector(2, 0, 0), False)
        self.assertIs(result, PointResult.CLOSED)
        self.assertEqual(coordinates(self.session.points), [(1, 0, 0)])
        self.assertEqual(self.axisflow.events, [
            ("confirm", (1, 0, 0)), ("setBasePoint", (1, 0, 0))])
        self.assertEqual(self.backend.created, [])
        self.assertTrue(self.session.closed)
        self.assertEqual(self.axisflow.ends, 1)
        self.assertIs(self.session.point(None, True), PointResult.CLOSED)
        self.assertEqual(self.axisflow.ends, 1)
        self.assertEqual(len(self.session.points), 1)
