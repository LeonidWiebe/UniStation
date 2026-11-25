"""Collect a wire of straight and circular segments until explicit completion."""

from unistation.i18n import tr
import math
from unistation.line import PointResult
from unistation.session import InputSession
from unistation.wire_arc import ArcFrame, WireArc, offset, xyz


class WireSession(InputSession):
    def __init__(self, backend, axisflow, origin=None):
        super().__init__(backend, axisflow, origin)
        self.points = []
        self.arcs = {}
        self.arc_enabled = False
        self.arc_frame = None
        self._mode_before_arc = None
        self._sweep = 0.0
        self._cursor = None
        self.last_error = ""

    def rewind_input(self):
        if self.arc_frame is not None:
            self._leave_arc()
        elif self.points:
            self.points.pop()
            self.arcs.pop(len(self.points) - 1, None)
        self.first = self.points[0] if self.points else None

    def input_anchor(self):
        if self.arc_frame is not None:
            return self.backend.make_point(self.arc_frame.center)
        return self.points[-1] if self.points else self.origin

    def restore_preview(self):
        self.move(None)

    def set_arc_enabled(self, enabled):
        if not self.valid() or self.arc_enabled == enabled:
            return
        self.arc_enabled = enabled
        try:
            if self.arc_frame is not None:
                self._leave_arc()
                self._request_points()
            self.move(self._cursor)
        except Exception as exc:
            self._fail(tr('AxisFlow synchronization failed: '), exc)

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
        return self._accept_point(point, ok, explicit=False)

    def _accept_point(self, point, ok, *, explicit):
        if not self.valid():
            return PointResult.CLOSED
        self.last_error = ""
        if not ok or point is None:
            self.cancel()
            return PointResult.CLOSED
        if not all(math.isfinite(v) for v in xyz(point)):
            return self.reject_point(tr('Coordinates must be finite.'))
        if self.arc_enabled and self.points:
            try:
                return self._accept_arc_point(point, explicit)
            except Exception as exc:
                return self._fail(tr('Wire arc input failed: '), exc)
        if self.points:
            segment = self._length(self.points[-1], point)
            if not math.isfinite(segment):
                return self.reject_point(tr('Segment length must be finite.'))
            if segment <= self.backend.tolerance:
                return self.reject_point(tr('Choose a different next point.'))
            closing = self._length(self.points[0], point)
            if math.isfinite(closing) and closing <= self.backend.tolerance:
                return self.close_contour()
        return self._add_vertex(point, explicit)

    def _add_vertex(self, point, explicit, arc=None):
        if arc is not None:
            self.arcs[len(self.points) - 1] = arc
        self.points.append(self.backend.copy_point(point))
        self.first = self.points[0]
        self.accepted_input()
        self.move(None)
        if not self.valid():
            return PointResult.FAILED
        if explicit or arc is not None:
            return self._synchronize(point, explicit)
        return PointResult.ACCEPTED

    def _arc_circle(self, center, info):
        return ArcFrame.from_center(self.points[-1], center, info['planeN'], self.backend.tolerance)

    def _reject_arc_point(self, message, explicit):
        if not explicit and self._synchronize(self.input_anchor(), False) is PointResult.FAILED:
            return PointResult.FAILED
        return self.reject_point(message)

    def _accept_arc_point(self, point, explicit):
        if self.arc_frame is None:
            info = self.axisflow.getCompassInfo()
            frame = self._arc_circle(point, info)
            if frame is None:
                return self._reject_arc_point(
                    tr('Choose an arc center different from the start in the current compass plane.'), explicit)
            self.arc_frame = frame
            self._mode_before_arc = info['mode']
            self.axisflow.setMode('polar')
            self.accepted_input()
            self.move(None)
            if not self.valid():
                return PointResult.FAILED
            return self._synchronize(point, explicit)

        arc, end = self._arc_endpoint(point)
        if arc is None:
            return self._reject_arc_point(tr('Choose an arc end different from the start and center.'), explicit)
        if explicit and self._length(point, end) > self.backend.tolerance:
            return self.reject_point(tr('Choose a point on the arc circle.'))
        if self._length(self.points[0], end) <= self.backend.tolerance:
            if len(self.points) < 3:
                return self._reject_arc_point(tr('A closed contour needs at least three points.'), explicit)
            self.arcs[len(self.points) - 1] = arc
            return self.close_contour()
        self._leave_arc()
        return self._add_vertex(end, explicit, arc)

    def _arc_endpoint(self, point):
        frame = self.arc_frame
        sweep = frame.sweep_to(point, self._sweep, self.backend.tolerance)
        if sweep is None:
            return None, None
        coords = frame.point_at(sweep)
        if not all(math.isfinite(value) for value in coords):
            return None, None
        end = self.backend.make_point(coords)
        if math.hypot(*offset(coords, xyz(self.points[-1]))) <= self.backend.tolerance:
            return None, end
        return WireArc(frame, sweep), end

    def _leave_arc(self):
        mode, self._mode_before_arc = self._mode_before_arc, None
        self.arc_frame = None
        self._sweep = 0.0
        if mode is not None:
            self.axisflow.setMode(mode)

    def _fail(self, message, exc):
        self.last_error = message + str(exc)
        self.backend.report(self.last_error)
        self.cancel()
        return PointResult.FAILED

    def _synchronize(self, point, explicit):
        try:
            if explicit:
                self.axisflow.confirm(point)
            self.axisflow.setBasePoint(point)
        except Exception as exc:
            return self._fail(tr('AxisFlow synchronization failed: '), exc)
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
        return self._accept_point(point, True, explicit=True)

    def move(self, point):
        self._cursor = point
        if self.valid() and self.points:
            try:
                if self.arc_enabled:
                    self._preview_arc(point)
                else:
                    self._preview_segments(point)
            except Exception as exc:
                self._fail(tr('Preview failed: '), exc)

    def _preview_segments(self, point, arc=None):
        if self.arcs or arc is not None:
            self.backend.preview_mixed_wire(self.points, self.arcs, point, arc)
        else:
            self.backend.preview_wire(self.points, point)

    def _preview_arc(self, point):
        frame = self.arc_frame
        start = xyz(self.points[-1])
        if frame is None:
            circle = self._arc_circle(point, self.axisflow.getCompassInfo()) if point is not None else None
            self._preview_segments(None)
            self.backend.preview_wire_guides(circle.samples(math.tau) if circle else (),
                                             () if point is None else (start, xyz(point)))
            return
        arc, end = self._arc_endpoint(point) if point is not None else (None, None)
        radii = (start, frame.center)
        if arc is not None:
            self._sweep = arc.sweep
        if end is not None:
            radii += (xyz(end),)
        self._preview_segments(end if arc is not None else None, arc)
        self.backend.preview_wire_guides((), radii)

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
            if self.arcs:
                self.backend.create_mixed_wire(self.points, self.arcs, closed)
            else:
                self.backend.create_wire(self.points, closed)
        except Exception as exc:
            self.last_error = tr('Wire creation failed: ') + str(exc)
            self.backend.report(self.last_error)
            return PointResult.FAILED
        else:
            return PointResult.CREATED
        finally:
            self.cancel()

    def cancel(self, *args):
        if self.closed:
            return
        try:
            self._leave_arc()
        except Exception as exc:
            self.backend.report(tr('AxisFlow synchronization failed: ') + str(exc))
        finally:
            super().cancel(*args)
