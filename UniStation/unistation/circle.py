"""Two-point circle following the live compass plane, independent of FreeCAD/Qt."""

from unistation.i18n import tr
import math
from unistation.line import PointResult
from unistation.planar import PlanarSession


class CircleSession(PlanarSession):
    def __init__(self, backend, axisflow, origin=None, normal=(0, 0, 1)):
        super().__init__(backend, axisflow, origin, normal)
        self.last_error = ""

    def reject_point(self, message):
        self.last_error = message
        self.backend.report(message)
        return PointResult.REJECTED

    def _radius(self, center, point):
        try:
            return (point - center).Length
        except OverflowError:
            return float("inf")

    def point(self, point, ok):
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        if not ok or point is None:
            self.cancel()
            return PointResult.CLOSED
        error = self.acceptable(point)
        if error:
            return self.reject_point(error)
        if self.first is None:
            self.first = self.backend.copy_point(point)
            self.accepted_input()
            return PointResult.ACCEPTED
        radius = self._radius(self.first, point)
        if not math.isfinite(radius) or radius <= self.backend.tolerance:
            return self.reject_point(tr('Choose a finite, non-zero radius.'))
        return self._create(radius)

    def _create(self, radius):
        try:
            self.backend.create_circle(self.first, radius)
        except Exception as exc:
            self.last_error = tr('Circle creation failed: ') + str(exc)
            self.backend.report(self.last_error)
            return PointResult.FAILED
        else:
            return PointResult.CREATED
        finally:
            self.cancel()

    def submit_point(self, point):
        """Accept an explicit world point and synchronize only a still-open center."""
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
        if not self.valid() or self.first is None:
            return
        try:
            radius = 0 if point is None else self._radius(self.first, point)
            rejection = point is not None and self.acceptable(point)
            if (point is None or rejection or not math.isfinite(radius)
                    or radius <= self.backend.tolerance):
                self.backend.clear_preview()
            else:
                self.backend.preview_circle(self.first, radius)
        except Exception as exc:
            self.last_error = tr('Preview failed: ') + str(exc)
            self.backend.report(self.last_error)
            self.cancel()
