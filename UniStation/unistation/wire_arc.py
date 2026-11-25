"""Circular Wire segment geometry in the compass plane."""

from dataclasses import dataclass
import math


def xyz(point):
    return point.x, point.y, point.z


def offset(point, origin):
    return tuple(value - base for value, base in zip(point, origin))


def dot(left, right):
    return sum(a * b for a, b in zip(left, right))


@dataclass(frozen=True)
class ArcFrame:
    center: tuple
    radius: float
    u: tuple
    v: tuple

    @classmethod
    def from_center(cls, start, center, normal, tolerance):
        radial = offset(xyz(start), xyz(center))
        radius = math.hypot(*radial)
        if not math.isfinite(radius) or radius <= tolerance:
            return None
        length = math.hypot(*normal)
        if not math.isfinite(length) or length <= 1e-12:
            raise ValueError('Invalid compass normal')
        normal = tuple(value / length for value in normal)
        if abs(dot(radial, normal)) > tolerance:
            return None

        u = tuple(value / radius for value in radial)
        x, y, z = normal
        a, b, c = u
        v = (y * c - z * b, z * a - x * c, x * b - y * a)
        length = math.hypot(*v)
        return cls(xyz(center), radius, u, tuple(value / length for value in v))

    def point_at(self, angle):
        cos, sin = math.cos(angle), math.sin(angle)
        return tuple(center + self.radius * (u * cos + v * sin)
                     for center, u, v in zip(self.center, self.u, self.v))

    def sweep_to(self, point, previous, tolerance):
        direction = offset(xyz(point), self.center)
        x, y = dot(direction, self.u), dot(direction, self.v)
        distance = math.hypot(x, y)
        if not math.isfinite(distance) or distance <= tolerance:
            return None
        # Unwrap around the previous preview so crossing 180 degrees does
        # not flip a long arc to its short complement.
        angle = math.atan2(y, x)
        return math.fmod(previous + math.remainder(angle - previous, math.tau), math.tau)

    def samples(self, sweep):
        steps = max(4, math.ceil(abs(sweep) / math.tau * 128))
        return [self.point_at(sweep * index / steps) for index in range(steps + 1)]


@dataclass(frozen=True)
class WireArc:
    frame: ArcFrame
    sweep: float
