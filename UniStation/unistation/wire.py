"""Collect a polyline without document mutations until explicit completion."""

from unistation.i18n import tr
import math
from unistation.line import PointResult
from unistation.session import InputSession


class WireSession(InputSession):
    def __init__(self, backend, axisflow, origin=None):
        super().__init__(backend, axisflow, origin)
        self.points = []
        self.last_error = ""

    def rewind_input(self):
        if self.points:
            self.points.pop()
        self.first = self.points[0] if self.points else None

    def input_anchor(self):
        return self.points[-1] if self.points else self.origin

    def restore_preview(self):
        if self.points:
            self.backend.preview_wire(self.points, None)

    def reject_point(self, message):
        self.last_error = message
        self.backend.report(message)
        return PointResult.REJECTED

    def _length(self, start, end):
        try:
            return (end - start).Length
        except OverflowError:
            return float("inf")

    def point(self, point, ok):
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        if not ok or point is None:
            self.cancel()
            return PointResult.CLOSED
        if not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
            return self.reject_point(tr('Coordinates must be finite.'))
        if self.points:
            segment = self._length(self.points[-1], point)
            if not math.isfinite(segment):
                return self.reject_point(tr('Segment length must be finite.'))
            if segment <= self.backend.tolerance:
                return self.reject_point(tr('Choose a different next point.'))
            closing = self._length(self.points[0], point)
            if math.isfinite(closing) and closing <= self.backend.tolerance:
                return self.close_contour()
        self.points.append(self.backend.copy_point(point))
        self.first = self.points[0]
        self.accepted_input()
        self.move(None)
        if not self.valid():
            return PointResult.FAILED
        return PointResult.ACCEPTED

    def submit_point(self, point):
        """Accept an explicit world point and synchronize only a still-live session."""
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        try:
            active = self.axisflow.isActive()
        except Exception as exc:
            self.last_error = tr('AxisFlow activity check failed: ') + str(exc)
            self.backend.report(self.last_error)
            self.cancel()
            return PointResult.FAILED
        if not active:
            self.cancel()
            return PointResult.CLOSED
        result = self.point(point, True)
        if result is PointResult.ACCEPTED and not self.closed:
            try:
                self.axisflow.confirm(point)
                self.axisflow.setBasePoint(point)
            except Exception as exc:
                self.last_error = tr('AxisFlow synchronization failed: ') + str(exc)
                self.backend.report(self.last_error)
                self.cancel()
                return PointResult.FAILED
        return result

    def move(self, point):
        if self.valid() and self.points:
            try:
                self.backend.preview_wire(self.points, point)
            except Exception as exc:
                self.last_error = tr('Preview failed: ') + str(exc)
                self.backend.report(self.last_error)
                self.cancel()

    def finish(self):
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        if len(self.points) < 2:
            self.cancel()
            return PointResult.CLOSED
        return self._create(False)

    def close_contour(self):
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        if len(self.points) < 3:
            return self.reject_point(tr('A closed contour needs at least three points.'))
        return self._create(True)

    def _create(self, closed):
        try:
            self.backend.create_wire(self.points, closed)
        except Exception as exc:
            self.last_error = tr('Wire creation failed: ') + str(exc)
            self.backend.report(self.last_error)
            return PointResult.FAILED
        else:
            return PointResult.CREATED
        finally:
            self.cancel()
