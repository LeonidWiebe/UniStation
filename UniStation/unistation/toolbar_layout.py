"""Validated per-toolbar preferences in the current FreeCAD user profile."""

from unistation.i18n import tr

import json

import FreeCAD as App


PATH = "User parameter:BaseApp/Preferences/Mod/UniStation/Toolbars"
# Keep the existing UniStation -> Drawing preference key for saved profiles.
# The new drawing toolbar has its own key and must not reuse that old geometry.
KEYS = {"UniStation": "Drawing", "Рисование": "DrawingTools",
        "Манипуляции": "Manipulations", "Палитра": "Palette", "Атрибуты": "Attributes",
        "Привязки": "Snapping"}


def validate(data):
    expected = {"version", "floating", "rect", "screen", "orientation"}
    if (not isinstance(data, dict) or set(data) != expected
            or type(data["version"]) is not int or data["version"] != 1
            or type(data["floating"]) is not bool
            or not isinstance(data["screen"], str) or len(data["screen"]) > 256
            or data["orientation"] not in ("horizontal", "vertical")):
        raise ValueError(tr('Invalid saved UniStation toolbar layout format.'))
    rect = data["rect"]
    if rect is not None:
        if (not isinstance(rect, list) or len(rect) != 4
                or any(type(value) is not int for value in rect)
                or any(abs(value) > 1000000 for value in rect[:2])
                or any(not 1 <= value <= 16384 for value in rect[2:])):
            raise ValueError(tr('Invalid UniStation toolbar coordinates or size.'))
    elif data["floating"]:
        raise ValueError(tr('No geometry is saved for the floating UniStation toolbar.'))
    return dict(data, rect=list(rect) if rect is not None else None)


class LayoutStore:
    def __init__(self):
        self.params = App.ParamGet(PATH)
        self.dirty = False

    def load(self, name):
        text = self.params.GetString(KEYS[name], "")
        if not text:
            return None
        if len(text) > 4096:
            raise ValueError(tr('The UniStation toolbar layout record is too large.'))
        return validate(json.loads(text))

    def save(self, name, data):
        value = validate(data)
        text = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        if self.params.GetString(KEYS[name], "") != text:
            self.params.SetString(KEYS[name], text)
            self.dirty = True

    def flush(self):
        if self.dirty:
            # The same current user parameter set selected by the launcher -u option.
            App.saveParameter()
            self.dirty = False
