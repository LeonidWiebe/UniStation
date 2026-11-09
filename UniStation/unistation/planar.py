"""Live compass-plane validation shared by Circle and Arc."""

from unistation.i18n import tr
import math
from unistation.session import InputSession


class PlanarSession(InputSession):
    def __init__(self, backend, axisflow, origin=None, normal=(0, 0, 1)):
        super().__init__(backend, axisflow, origin)
        length = math.sqrt(sum(v * v for v in normal))
        self.normal = tuple(v / length for v in normal)

    def acceptable(self, point):
        values = (point.x, point.y, point.z)
        if not all(math.isfinite(v) for v in values):
            return tr('Coordinates must be finite.')
        try:
            # AxisFlow owns the live frame. WorkingPlane is only the initial
            # frame; rotating the compass does not update that Draft snapshot.
            state = self.axisflow.getCompassInfo()
            base = tuple(state['origin'])
            u, v, normal = (tuple(state[key]) for key in ('planeU', 'planeV', 'planeN'))
            if any(len(vector) != 3 or not all(math.isfinite(x) for x in vector)
                   for vector in (base, u, v, normal)):
                raise ValueError('Invalid compass frame')
            length = math.hypot(*normal)
            if length <= 1e-12:
                raise ValueError('Invalid compass normal')
            self.backend.set_circle_plane(u, v, normal)
            self.normal = tuple(x / length for x in normal)
        except Exception as exc:
            return tr('Cannot read the current AxisFlow plane: ') + str(exc)
        distance = sum((v - o) * n for v, o, n in zip(values, base, self.normal))
        if abs(distance) > self.backend.tolerance:
            return tr('Choose a point in the current compass plane.')
        return None

