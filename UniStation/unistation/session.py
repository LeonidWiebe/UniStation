"""Shared AxisFlow ownership and teardown for point-based commands."""

from unistation.i18n import tr
from unistation.input_events import ResettableCommand


class InputSession(ResettableCommand):
    def __init__(self, backend, axisflow, origin=None):
        self.backend = backend
        self.axisflow = axisflow
        self.first = None
        self.closed = False
        self.started = False
        self.origin = origin
        self._input_generation = 0

    def start(self):
        if self.started or self.closed:
            raise RuntimeError(tr('An input session can only be started once'))
        self.started = True
        try:
            self._request_points()
        except Exception:
            self.cancel()
            raise

    def _request_points(self):
        self._input_generation += 1
        generation = self._input_generation

        def point(value, ok):
            if not self.closed and generation == self._input_generation:
                return self.point(value, ok)

        def move(value):
            if not self.closed and generation == self._input_generation:
                return self.move(value)

        def finish():
            if not self.closed and generation == self._input_generation:
                return self.finish()

        # getPoint re-arms the existing native tool, clearing its typed values,
        # locks and follow reference. It replaces the old callback bridge.
        self.axisflow.getPoint(callback=point, movecallback=move, continuous=True,
                               finishcallback=finish, last=self.input_anchor())

    def input_anchor(self):
        return self.first if self.first is not None else self.origin

    def rewind_input(self):
        self.first = None

    def restore_preview(self):
        pass

    def reset_step(self):
        if not self.valid():
            return
        # Invalidate deferred commits and callbacks before mutating command state.
        self._input_generation += 1
        self.rewind_input()
        if hasattr(self, "last_error"):
            self.last_error = ""
        self.backend.reset_input()
        self.restore_preview()
        self._request_points()

    def accepted_input(self):
        super().accepted_input()
        notify = getattr(self.backend, "input_accepted", None)
        if notify is not None:
            notify()

    def valid(self):
        if self.closed:
            return False
        if not self.backend.alive():
            self.cancel()
            return False
        return True

    def finish(self):
        self.cancel()

    def cancel(self, *args):
        if self.closed:
            return
        self.closed = True
        try:
            if self.started:
                self.axisflow.endSession()
        finally:
            self.backend.close()
