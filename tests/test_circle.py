import unittest
from types import SimpleNamespace
from test_line import Backend, Vector
from unistation.circle import CircleSession
from unistation.line import PointResult


class CircleBackend(Backend):
    def create_circle(self, center, radius):
        if self.fail:
            raise RuntimeError("injected failure")
        self.created.append((center, radius))

    def preview_circle(self, center, radius):
        self.preview_radius = radius

    def clear_preview(self):
        self.preview_radius = None


class CircleTests(unittest.TestCase):
    def setUp(self):
        self.backend = CircleBackend()
        self.ends = 0
        self.api = SimpleNamespace(getPoint=self.capture, endSession=self.end)
        self.session = CircleSession(self.backend, self.api)
        self.session.start()

    def capture(self, **kwargs):
        self.callbacks = kwargs

    def end(self):
        self.ends += 1

    def test_radius_copied_center_and_late_callback(self):
        center = Vector(1, 2)
        self.session.point(center, True)
        center.x = 99
        self.session.point(Vector(4, 6), True)
        self.session.point(Vector(10), True)
        self.assertEqual(len(self.backend.created), 1)
        self.assertEqual(self.backend.created[0][0].x, 1)
        self.assertEqual(self.backend.created[0][1], 5)
        self.assertEqual(self.ends, 1)

    def test_zero_radius_can_be_retried(self):
        self.session.point(Vector(0), True)
        self.session.point(Vector(0), True)
        self.assertFalse(self.session.closed)
        self.session.point(Vector(5), True)
        self.assertEqual(self.backend.created[0][1], 5)

    def test_invalid_points_and_plane(self):
        for point in (Vector(float('nan')), Vector(float('inf')), Vector(0, 0, 10)):
            self.session.point(point, True)
        self.assertIsNone(self.session.first)
        self.session.point(Vector(0), True)
        self.session.point(Vector(5, 0, 1), True)
        self.assertEqual(self.backend.created, [])

    def test_tilted_translated_plane(self):
        session = CircleSession(self.backend, self.api, origin=Vector(0, 4, 25),
                                normal=(0, 1, 0))
        session.start()
        session.point(Vector(0, 4, 25), True)
        session.point(Vector(3, 4, 29), True)
        self.assertEqual(self.backend.created[0][1], 5)

    def test_finish_and_cancel_discard(self):
        self.session.point(Vector(0), True)
        self.callbacks['finishcallback']()
        self.session.cancel()
        self.assertEqual(self.backend.created, [])
        self.assertEqual(self.ends, 1)

    def test_document_switch(self):
        self.session.point(Vector(0), True)
        self.backend.live = False
        self.session.point(Vector(5), True)
        self.assertTrue(self.session.closed)
        self.assertEqual(self.backend.created, [])

    def test_failure_cleans_session(self):
        self.backend.fail = True
        self.session.point(Vector(0), True)
        self.session.point(Vector(5), True)
        self.assertTrue(self.backend.errors)
        self.assertEqual(self.backend.closed, 1)

    def test_preview_invalid_point_clears_stale_circle(self):
        self.session.point(Vector(0), True)
        self.session.move(Vector(5))
        self.assertEqual(self.backend.preview_radius, 5)
        self.session.move(Vector(0, 0, 5))
        self.assertIsNone(self.backend.preview_radius)


class OverflowPoint(Vector):
    def __sub__(self, other):
        return self

    @property
    def Length(self):
        raise OverflowError("length overflow")


class NonFiniteRadiusPoint(Vector):
    def __sub__(self, other):
        return self

    @property
    def Length(self):
        return float("inf")


class CircleAxisFlow:
    def __init__(self):
        self.events = []
        self.ends = 0
        self.active = True
        self.fail_active = False
        self.fail_confirm = False
        self.fail_base = False
        self.callbacks = {}

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


class CircleResultTests(unittest.TestCase):
    def setUp(self):
        self.session = self.make_session()

    def make_session(self, **kwargs):
        backend = CircleBackend()
        axisflow = CircleAxisFlow()
        session = CircleSession(backend, axisflow, **kwargs)
        session.start()
        return session

    def test_center_copy_and_single_creation(self):
        center = Vector(1, 2, 0)
        self.assertIs(self.session.submit_point(center), PointResult.ACCEPTED)
        center.x = 99
        self.assertEqual((self.session.first.x, self.session.first.y, self.session.first.z),
                         (1, 2, 0))
        self.assertEqual(self.session.backend.created, [])
        self.assertFalse(hasattr(self.session.backend, "preview_radius"))
        self.assertIs(self.session.origin, None)
        self.assertEqual(self.session.last_error, "")
        self.assertFalse(self.session.closed)

        created = self.session.submit_point(Vector(1, 6, 0))

        self.assertIs(created, PointResult.CREATED)
        self.assertEqual(len(self.session.backend.created), 1)
        stored, radius = self.session.backend.created[0]
        self.assertEqual((stored.x, stored.y, stored.z), (1, 2, 0))
        self.assertEqual(radius, 4)
        self.assertEqual(self.session.axisflow.ends, 1)
        self.assertEqual(self.session.backend.closed, 1)
        self.assertEqual(self.session.axisflow.events, [
            ("confirm", (1, 2, 0)),
            ("setBasePoint", (1, 2, 0)),
        ])
        self.assertIs(self.session.submit_point(Vector(9, 9, 0)), PointResult.CLOSED)
        self.assertIs(self.session.axisflow.callbacks["callback"](Vector(8, 8, 0), True),
                      PointResult.CLOSED)
        self.assertEqual(len(self.session.backend.created), 1)
        self.assertEqual(self.session.axisflow.ends, 1)
        self.assertEqual(self.session.backend.closed, 1)
        self.assertEqual(len(self.session.axisflow.events), 2)

    def test_rejections_keep_state_and_retry_clears_error(self):
        plane = "Choose a point in the working plane captured at command start."
        radius = "Choose a finite, non-zero radius."
        before_center = (
            (Vector(float("nan")), "Coordinates must be finite."),
            (Vector(float("inf")), "Coordinates must be finite."),
            (Vector(0, 0, 10), plane),
        )
        for point, message in before_center:
            result = self.session.submit_point(point)
            self.assertIs(result, PointResult.REJECTED)
            self.assertEqual(self.session.last_error, message)
            self.assertEqual(self.session.backend.errors[-1], message)
            self.assertIsNone(self.session.first)
            self.assertEqual(self.session.backend.created, [])
            self.assertEqual(self.session.axisflow.events, [])
            self.assertFalse(self.session.closed)

        center = Vector(2, 0, 0)
        self.assertIs(self.session.submit_point(center), PointResult.ACCEPTED)
        center.x = 50
        self.assertEqual(self.session.last_error, "")
        self.assertEqual((self.session.first.x, self.session.first.y, self.session.first.z),
                         (2, 0, 0))
        saved_events = list(self.session.axisflow.events)
        after_center = (
            (Vector(float("nan"), 0, 0), "Coordinates must be finite."),
            (Vector(float("-inf"), 0, 0), "Coordinates must be finite."),
            (Vector(2, 0, 4), plane),
            (Vector(2, 0, 0), radius),
            (Vector(2 + 1e-9, 0, 0), radius),
            (NonFiniteRadiusPoint(3, 0, 0), radius),
            (OverflowPoint(4, 0, 0), radius),
        )
        for point, message in after_center:
            result = self.session.submit_point(point)
            self.assertIs(result, PointResult.REJECTED)
            self.assertEqual(self.session.last_error, message)
            self.assertEqual(self.session.backend.errors[-1], message)
            self.assertEqual((self.session.first.x, self.session.first.y, self.session.first.z),
                             (2, 0, 0))
            self.assertEqual(self.session.axisflow.events, saved_events)
            self.assertEqual(self.session.backend.created, [])
            self.assertFalse(self.session.closed)

        created = self.session.submit_point(Vector(2, 5, 0))
        self.assertIs(created, PointResult.CREATED)
        self.assertEqual(self.session.last_error, "")
        self.assertEqual(self.session.backend.created[0][1], 5)
        self.assertEqual(self.session.axisflow.events, saved_events)
        self.assertEqual(len(self.session.backend.created), 1)
        self.assertEqual(self.session.axisflow.ends, 1)

    def test_tilted_plane_keeps_world_coordinates(self):
        origin = Vector(0, 4, 25)
        session = self.make_session(origin=origin, normal=(0, 1, 0))
        center = Vector(0, 4, 25)

        self.assertIs(session.submit_point(center), PointResult.ACCEPTED)
        center.y = 0

        self.assertIs(session.origin, origin)
        self.assertEqual((origin.x, origin.y, origin.z), (0, 4, 25))
        self.assertEqual((session.first.x, session.first.y, session.first.z), (0, 4, 25))
        self.assertEqual(session.axisflow.events, [
            ("confirm", (0, 4, 25)),
            ("setBasePoint", (0, 4, 25)),
        ])
        created = session.submit_point(Vector(3, 4, 29))
        self.assertIs(created, PointResult.CREATED)
        stored, radius = session.backend.created[0]
        self.assertEqual((stored.x, stored.y, stored.z), (0, 4, 25))
        self.assertEqual(radius, 5)
        self.assertEqual(len(session.axisflow.events), 2)
        self.assertEqual(session.axisflow.ends, 1)

    def test_submit_orders_sync_and_callback_does_not(self):
        callback = self.session.axisflow.callbacks["callback"]
        self.assertIs(callback(Vector(1, 2, 0), True), PointResult.ACCEPTED)
        self.assertEqual(self.session.axisflow.events, [])
        self.assertEqual((self.session.first.x, self.session.first.y, self.session.first.z),
                         (1, 2, 0))

        created = callback(Vector(1, 7, 0), True)
        self.assertIs(created, PointResult.CREATED)
        self.assertEqual(self.session.backend.created[0][1], 5)
        self.assertEqual(self.session.axisflow.events, [])
        self.assertEqual(self.session.axisflow.ends, 1)

        other = self.make_session()
        self.assertIs(other.submit_point(Vector(4, 0, 0)), PointResult.ACCEPTED)
        self.assertIs(other.submit_point(Vector(4, 3, 0)), PointResult.CREATED)
        self.assertEqual(other.axisflow.events, [
            ("confirm", (4, 0, 0)),
            ("setBasePoint", (4, 0, 0)),
        ])
        self.assertEqual(other.backend.created[0][1], 3)
        self.assertEqual(other.axisflow.ends, 1)

    def test_inactive_and_api_failures_close_once(self):
        self.session.axisflow.active = False
        self.assertIs(self.session.submit_point(Vector(1, 0, 0)), PointResult.CLOSED)
        self.assertIsNone(self.session.first)
        self.assertEqual(self.session.backend.created, [])
        self.assertEqual(self.session.axisflow.events, [])
        self.assertEqual(self.session.backend.errors, [])
        self.assertTrue(self.session.closed)
        self.assertEqual(self.session.axisflow.ends, 1)
        self.assertEqual(self.session.backend.closed, 1)
        self.assertIs(self.session.submit_point(Vector(2, 0, 0)), PointResult.CLOSED)
        self.assertEqual(self.session.axisflow.ends, 1)

        active = self.make_session()
        active.axisflow.fail_active = True
        result = active.submit_point(Vector(1, 0, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(active.last_error, "AxisFlow activity check failed: activity failed")
        self.assertEqual(active.backend.errors[-1], active.last_error)
        self.assertIsNone(active.first)
        self.assertEqual(active.axisflow.events, [])
        self.assertTrue(active.closed)
        self.assertEqual(active.axisflow.ends, 1)
        self.assertEqual(active.backend.closed, 1)
        self.assertIs(active.submit_point(Vector(2, 0, 0)), PointResult.CLOSED)
        self.assertEqual(active.axisflow.ends, 1)
        self.assertEqual(active.backend.created, [])

        confirm = self.make_session()
        confirm.axisflow.fail_confirm = True
        result = confirm.submit_point(Vector(5, 0, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(confirm.last_error, "AxisFlow synchronization failed: confirm failed")
        self.assertEqual(confirm.backend.errors[-1], confirm.last_error)
        self.assertEqual([name for name, _point in confirm.axisflow.events], ["confirm"])
        self.assertEqual((confirm.first.x, confirm.first.y, confirm.first.z), (5, 0, 0))
        self.assertEqual(confirm.backend.created, [])
        self.assertTrue(confirm.closed)
        self.assertEqual(confirm.axisflow.ends, 1)
        self.assertIs(confirm.submit_point(Vector(6, 0, 0)), PointResult.CLOSED)
        self.assertEqual(len(confirm.axisflow.events), 1)
        self.assertEqual(confirm.axisflow.ends, 1)

        base = self.make_session()
        base.axisflow.fail_base = True
        result = base.submit_point(Vector(7, 1, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(base.last_error, "AxisFlow synchronization failed: base point failed")
        self.assertEqual([name for name, _point in base.axisflow.events],
                         ["confirm", "setBasePoint"])
        self.assertEqual(base.axisflow.events[1][1], (7, 1, 0))
        self.assertEqual(base.backend.created, [])
        self.assertTrue(base.closed)
        self.assertEqual(base.axisflow.ends, 1)
        self.assertEqual(base.backend.closed, 1)
        self.assertIs(base.submit_point(Vector(8, 1, 0)), PointResult.CLOSED)
        self.assertEqual(len(base.axisflow.events), 2)

        creation = self.make_session()
        self.assertIs(creation.submit_point(Vector(0, 0, 0)), PointResult.ACCEPTED)
        events = list(creation.axisflow.events)
        creation.backend.fail = True
        result = creation.submit_point(Vector(0, 6, 0))
        self.assertIs(result, PointResult.FAILED)
        self.assertEqual(creation.last_error, "Circle creation failed: injected failure")
        self.assertEqual(creation.backend.errors[-1], creation.last_error)
        self.assertEqual(creation.backend.created, [])
        self.assertEqual(creation.axisflow.events, events)
        self.assertTrue(creation.closed)
        self.assertEqual(creation.axisflow.ends, 1)
        self.assertEqual(creation.backend.closed, 1)
        self.assertEqual(creation.last_error, "Circle creation failed: injected failure")
        self.assertIs(creation.submit_point(Vector(0, 7, 0)), PointResult.CLOSED)
        self.assertEqual(creation.axisflow.events, events)
        self.assertEqual(creation.axisflow.ends, 1)
        self.assertEqual(creation.backend.created, [])

    def test_closed_inputs_do_not_repeat_cleanup(self):
        self.assertIs(self.session.point(Vector(1, 0, 0), False), PointResult.CLOSED)
        self.assertIsNone(self.session.first)
        self.assertEqual(self.session.backend.created, [])
        self.assertEqual(self.session.axisflow.ends, 1)
        self.assertEqual(self.session.backend.closed, 1)
        self.assertIs(self.session.point(Vector(2, 0, 0), True), PointResult.CLOSED)
        self.assertIs(self.session.submit_point(Vector(3, 0, 0)), PointResult.CLOSED)
        self.assertEqual(self.session.axisflow.ends, 1)
        self.assertEqual(self.session.backend.closed, 1)

        missing = self.make_session()
        self.assertIs(missing.point(None, True), PointResult.CLOSED)
        self.assertEqual(missing.backend.created, [])
        self.assertEqual(missing.axisflow.ends, 1)
        self.assertIs(missing.point(None, True), PointResult.CLOSED)
        self.assertEqual(missing.axisflow.ends, 1)

        dead = self.make_session()
        self.assertIs(dead.point(Vector(0, 0, 0), True), PointResult.ACCEPTED)
        dead.backend.live = False
        calls = []
        dead.axisflow.isActive = lambda: calls.append("isActive") or True
        self.assertIs(dead.point(Vector(0, 4, 0), True), PointResult.CLOSED)
        self.assertEqual(dead.backend.created, [])
        self.assertEqual(calls, [])
        self.assertEqual(dead.axisflow.ends, 1)
        self.assertEqual(dead.backend.closed, 1)
        self.assertIs(dead.submit_point(Vector(0, 5, 0)), PointResult.CLOSED)
        self.assertEqual(calls, [])
        self.assertEqual(dead.axisflow.ends, 1)
        self.assertEqual(dead.backend.closed, 1)

        fresh = self.make_session()
        fresh.backend.live = False
        self.assertIs(fresh.submit_point(Vector(1, 0, 0)), PointResult.CLOSED)
        self.assertIsNone(fresh.first)
        self.assertEqual(fresh.axisflow.events, [])
        self.assertEqual(fresh.axisflow.ends, 1)
        self.assertIs(fresh.submit_point(Vector(2, 0, 0)), PointResult.CLOSED)
        self.assertEqual(fresh.axisflow.ends, 1)

        finished = self.make_session()
        self.assertIs(finished.point(Vector(0, 0, 0), True), PointResult.ACCEPTED)
        self.assertIsNone(finished.finish())
        self.assertEqual(finished.backend.created, [])
        self.assertTrue(finished.closed)
        self.assertEqual(finished.axisflow.ends, 1)
        self.assertIsNone(finished.finish())
        self.assertEqual(finished.axisflow.ends, 1)
        self.assertEqual(finished.backend.closed, 1)

    def test_preview_updates_and_failures_cancel(self):
        self.session.move(Vector(5, 0, 0))
        self.assertFalse(hasattr(self.session.backend, "preview_radius"))
        self.assertIs(self.session.point(Vector(0, 0, 0), True), PointResult.ACCEPTED)
        self.assertIs(self.session.point(Vector(0, 0, 0), True), PointResult.REJECTED)
        self.assertEqual(self.session.last_error, "Choose a finite, non-zero radius.")
        remembered = self.session.last_error
        self.session.move(Vector(0, 6, 0))
        self.assertEqual(self.session.backend.preview_radius, 6)
        self.assertEqual(self.session.last_error, remembered)
        self.assertFalse(self.session.closed)
        self.session.move(None)
        self.assertIsNone(self.session.backend.preview_radius)
        self.session.move(Vector(0, 0, 8))
        self.assertIsNone(self.session.backend.preview_radius)
        self.session.move(Vector(0, 3, 0))
        self.assertEqual(self.session.backend.preview_radius, 3)
        self.session.move(NonFiniteRadiusPoint(1, 0, 0))
        self.assertIsNone(self.session.backend.preview_radius)
        self.session.move(Vector(0, 2, 0))
        self.session.move(OverflowPoint(1, 0, 0))
        self.assertIsNone(self.session.backend.preview_radius)
        self.assertEqual(self.session.last_error, remembered)
        self.assertFalse(self.session.closed)
        self.assertEqual((self.session.first.x, self.session.first.y, self.session.first.z),
                         (0, 0, 0))

        preview = self.make_session()
        preview.point(Vector(0, 0, 0), True)

        def fail_preview(center, radius):
            raise RuntimeError("preview failed")

        preview.backend.preview_circle = fail_preview
        preview.move(Vector(4, 0, 0))
        self.assertEqual(preview.last_error, "Preview failed: preview failed")
        self.assertEqual(preview.backend.errors[-1], preview.last_error)
        self.assertTrue(preview.closed)
        self.assertEqual(preview.axisflow.ends, 1)
        self.assertEqual(preview.backend.created, [])
        self.assertIs(preview.submit_point(Vector(5, 0, 0)), PointResult.CLOSED)
        self.assertEqual(preview.axisflow.ends, 1)
        self.assertEqual(preview.axisflow.events, [])

        clearing = self.make_session()
        clearing.point(Vector(0, 0, 0), True)

        def fail_clear():
            raise RuntimeError("clear failed")

        clearing.backend.clear_preview = fail_clear
        clearing.move(None)
        self.assertEqual(clearing.last_error, "Preview failed: clear failed")
        self.assertEqual(clearing.backend.errors[-1], clearing.last_error)
        self.assertTrue(clearing.closed)
        self.assertEqual(clearing.axisflow.ends, 1)
        self.assertIs(clearing.submit_point(Vector(1, 0, 0)), PointResult.CLOSED)
        self.assertEqual(clearing.axisflow.ends, 1)
        self.assertEqual(clearing.backend.created, [])

    def test_last_error_instances_are_independent(self):
        other = self.make_session()
        self.assertIs(self.session.point(Vector(float("nan")), True), PointResult.REJECTED)
        self.assertEqual(self.session.last_error, "Coordinates must be finite.")
        self.assertEqual(other.last_error, "")
        self.assertIs(other.point(Vector(0, 0, 3), True), PointResult.REJECTED)
        self.assertEqual(other.last_error,
                         "Choose a point in the working plane captured at command start.")
        self.assertEqual(self.session.last_error, "Coordinates must be finite.")
        self.assertIsNot(self.session, other)
        self.assertFalse(self.session.closed)
        self.assertFalse(other.closed)

