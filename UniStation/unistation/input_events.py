"""Command-owned logical input events, independent of Qt and physical buttons."""

from dataclasses import dataclass
from enum import Enum


class InputType(Enum):
    RESET = "Reset"


@dataclass(frozen=True)
class InputEvent:
    kind: InputType
    source: str = "command"


class ResettableCommand:
    """Commands may override on_reset; the default rewinds, then exits."""

    def handle_input(self, event):
        if event.kind is InputType.RESET and not self.closed:
            return self.on_reset(event)
        return False

    def on_reset(self, event):
        if getattr(self, "_reset_pending_exit", False):
            self.cancel()
        else:
            self._reset_pending_exit = True
            self.reset_step()
        return True

    def accepted_input(self):
        # Hover, invalid input and typing alone do not interrupt consecutive Reset.
        self._reset_pending_exit = False

    def reset_step(self):
        raise NotImplementedError
