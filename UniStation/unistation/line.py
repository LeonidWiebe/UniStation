"""Two-point command lifecycle, independent of Qt and input implementation."""

from unistation.i18n import tr
import math
from enum import Enum
from unistation.session import InputSession


class PointResult(Enum):
    ACCEPTED = "accepted"
    CREATED = "created"
    REJECTED = "rejected"
    CLOSED = "closed"
    FAILED = "failed"


class LineSession(InputSession):
    last_error = ""

    def reject_point(self, message):
        self.last_error = message
        self.backend.report(message)
        return PointResult.REJECTED

    def point(self, point, ok):
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        if not ok or point is None:
            self.cancel()
            return PointResult.CLOSED
        if not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
            return self.reject_point(tr('Coordinates must be finite.'))
        if self.first is None:
            self.first = self.backend.copy_point(point)
            self.accepted_input()
            return PointResult.ACCEPTED
        length = (point - self.first).Length
        if not math.isfinite(length) or length <= self.backend.tolerance:
            return self.reject_point(tr('Choose a finite, different end point.'))
        try:
            self.backend.create_line(self.first, point)
        except Exception as exc:
            self.last_error = tr('Line creation failed: ') + str(exc)
            self.backend.report(self.last_error)
            return PointResult.FAILED
        else:
            return PointResult.CREATED
        finally:
            self.cancel()

    def submit_point(self, point):
        """Accept explicit world coordinates and synchronize only a live session."""
        if not self.valid():
            return PointResult.CLOSED
        if not self.axisflow.isActive():
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
        if self.valid() and self.first is not None:
            try:
                self.backend.preview(self.first, point)
            except Exception as exc:
                self.backend.report(tr('Preview failed: ') + str(exc))
                self.cancel()

