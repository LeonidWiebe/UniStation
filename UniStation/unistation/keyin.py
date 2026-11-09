"""Parse explicit world-coordinate key-in values without FreeCAD dependencies."""

from unistation.i18n import tr

import math
import re


_PREFIX = re.compile(r"\A(abs|rel)\s+(.+)\Z", re.IGNORECASE | re.DOTALL)
_COMPONENT = re.compile(r"\A([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(mm|cm|m)?\Z")
_SCALE = {None: 1.0, "mm": 1.0, "cm": 10.0, "m": 1000.0}
_MAX_TEXT_LENGTH = 4096


def _finite_base(base):
    if base is None:
        raise ValueError(tr('Enter an absolute point or pick a point with the mouse first'))
    try:
        values = tuple(float(value) for value in base)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(tr('The base point must contain three finite coordinates')) from None
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError(tr('The base point must contain three finite coordinates'))
    return values


def parse_point(text, base=None):
    """Return an absolute world point in millimetres from ``abs`` or ``rel`` input.

    ``base`` is required only for relative input and is copied before use.
    Malformed, non-finite, or out-of-range coordinates raise ``ValueError``.
    """
    if not isinstance(text, str):
        raise ValueError(tr('Enter coordinates as text'))
    if len(text) > _MAX_TEXT_LENGTH:
        raise ValueError(tr('Input is too long (maximum 4096 characters)'))

    match = _PREFIX.fullmatch(text.strip())
    if match is None:
        raise ValueError(tr('Enter abs or rel and three coordinates separated by semicolons'))
    mode, body = match.groups()
    parts = body.split(";")
    if len(parts) != 3:
        raise ValueError(tr('Enter exactly three coordinates separated by semicolons'))

    coordinates = []
    for part in parts:
        component = _COMPONENT.fullmatch(part.strip())
        if component is None:
            raise ValueError(tr('A coordinate must be a number with a decimal point and units mm, cm or m'))
        number, unit = component.groups()
        try:
            value = float(number) * _SCALE[unit]
        except (ValueError, OverflowError):
            raise ValueError(tr('A coordinate is outside the supported numeric range')) from None
        if not math.isfinite(value):
            raise ValueError(tr('A coordinate must be finite'))
        coordinates.append(value)

    if mode.lower() == "rel":
        origin = _finite_base(base)
        coordinates = [origin[index] + coordinates[index] for index in range(3)]
        if not all(math.isfinite(value) for value in coordinates):
            raise ValueError(tr('The relative coordinate result is outside the supported range'))

    return tuple(coordinates)
