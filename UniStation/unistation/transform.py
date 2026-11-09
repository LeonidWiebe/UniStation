"""Two-point displacement, committed outside the native input callback."""

from unistation.i18n import tr
import math
from unistation.session import InputSession


class TransformSession(InputSession):
    def __init__(self, backend, axisflow, origin=None, copy=False):
        super().__init__(backend, axisflow, origin)
        self.copy = copy
        self.pending = False

    def rewind_input(self):
        super().rewind_input()
        self.pending = False

    def point(self, point, ok):
        if not self.valid() or self.pending:
            return
        if not ok or point is None:
            self.cancel()
            return
        if not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
            self.backend.report(tr('Coordinates must be finite.'))
            return
        if self.first is None:
            self.first = self.backend.copy_point(point)
            self.accepted_input()
            return
        delta = point - self.first
        if not math.isfinite(delta.Length) or delta.Length <= self.backend.tolerance:
            self.backend.report(tr('Choose a finite, non-zero displacement.'))
            return
        self.pending = True
        delta = self.backend.copy_point(delta)
        generation = self._input_generation

        def commit():
            if generation != self._input_generation or not self.pending:
                return
            if not self.valid():
                return
            try:
                self.backend.transform(delta, self.copy)
            except Exception as exc:
                self.backend.report(tr('Transform failed: ') + str(exc))
            finally:
                self.cancel()

        try:
            self.backend.defer(commit)
        except Exception:
            self.cancel()
            raise

    def move(self, point):
        if not self.valid() or self.pending or self.first is None:
            return
        try:
            if point is None or not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
                self.backend.hide_ghost()
                return
            delta = point - self.first
            if not math.isfinite(delta.Length):
                self.backend.hide_ghost()
                return
            self.backend.preview_transform(delta)
        except Exception as exc:
            self.backend.report(tr('Preview failed: ') + str(exc))
            self.cancel()
