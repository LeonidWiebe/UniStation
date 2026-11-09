"""Three world points form an arc; new points follow the live compass plane."""

from unistation.i18n import tr
import math
from unistation.planar import PlanarSession


class ArcSession(PlanarSession):
    def __init__(self, backend, axisflow, origin=None, normal=(0, 0, 1)):
        super().__init__(backend, axisflow, origin, normal)
        self.points = []

    def rewind_input(self):
        if self.points:
            self.points.pop()
        self.first = self.points[0] if self.points else None

    def point_error(self, point):
        error = self.acceptable(point)
        if error:
            return error
        if any((point - p).Length <= self.backend.tolerance for p in self.points):
            return tr('Choose a point different from the previous arc points.')
        if len(self.points) == 2:
            a = self.points[1] - self.points[0]
            b = point - self.points[0]
            # Normalize first to avoid squared coordinate overflow in the cross product.
            length = math.hypot(a.x, a.y, a.z)
            u = (a.x / length, a.y / length, a.z / length)
            height = math.hypot(u[1]*b.z-u[2]*b.y,
                                u[2]*b.x-u[0]*b.z, u[0]*b.y-u[1]*b.x)
            if not math.isfinite(height) or height <= self.backend.tolerance:
                return tr('Three arc points must not lie on one straight line.')
        return None

    def point(self, point, ok):
        if not self.valid():
            return
        if not ok or point is None:
            self.cancel()
            return
        error = self.point_error(point)
        if error:
            self.backend.report(error)
            return
        if len(self.points) < 2:
            self.points.append(self.backend.copy_point(point))
            self.first = self.points[0]
            self.accepted_input()
            self.backend.clear_preview()
            return
        try:
            self.backend.create_arc(self.points[0], self.points[1], point)
        except Exception as exc:
            self.backend.report(tr('Arc creation failed: ') + str(exc))
        finally:
            self.cancel()

    def move(self, point):
        if not self.valid() or not self.points:
            return
        try:
            if point is None or self.point_error(point):
                self.backend.clear_preview()
            elif len(self.points) == 1:
                self.backend.preview(self.points[0], point)
            else:
                self.backend.preview_arc(self.points[0], self.points[1], point)
        except Exception as exc:
            self.backend.report(tr('Preview failed: ') + str(exc))
            self.cancel()
