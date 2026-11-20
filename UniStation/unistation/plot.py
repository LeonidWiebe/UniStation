"""Vector PDF output of planar geometry, independent of the 3D view."""

from dataclasses import dataclass
import math
import os
from pathlib import Path
from tempfile import mkstemp

from unistation import levels
from unistation.i18n import tr
from unistation.palette import displayed_rgb, same_document


PAPER_SIZES = ("A4", "A3", "A2", "A1", "A0")
STROKE_MM = 0.25
PDF_DPI = 720
PLANAR_TOLERANCE_MM = 1e-6


class PlotError(ValueError):
    pass


@dataclass(frozen=True)
class PlotSettings:
    paper: str = "A4"
    landscape: bool = True
    margin_mm: float = 10.0
    denominator: float | None = None


def _planar_shape(obj):
    from draftutils.utils import get_type

    if not obj.isDerivedFrom("Part::Feature"):
        return None
    if obj.TypeId != "Part::Feature" and get_type(obj) not in ("Wire", "Circle"):
        return None
    if obj.getParentGeoFeatureGroup() is not None or obj.OutList:
        return None
    shape = getattr(obj, "Shape", None)
    if shape is None or shape.isNull() or not shape.Edges:
        return None
    bounds = shape.BoundBox
    if not bounds.isValid() or bounds.ZLength > PLANAR_TOLERANCE_MM:
        return None
    return shape


def _plot_objects(document, objects):
    records = {level.identifier: level for level in levels.available_levels(document)}
    geometry = []
    seen = set()
    candidates = document.Objects if objects is None else objects
    for obj in candidates:
        if obj.Document is not document or document.getObject(obj.Name) is not obj:
            raise PlotError(tr('Select whole objects from the active document.'))
        if obj.Name in seen:
            continue
        seen.add(obj.Name)
        shape = _planar_shape(obj)
        if shape is None:
            if objects is not None:
                raise PlotError(tr('“{}” is not supported for plotting in the XY plane.').format(obj.Label))
            continue
        identifier = levels.element_level_id(obj) or levels.DEFAULT_ID
        level = records.get(identifier)
        if level is None:
            raise PlotError(tr('“{}” refers to a missing level. Assign an existing level first.').format(obj.Label))
        if level.plot and not level.global_freeze:
            if not shape.isValid():
                raise PlotError(tr('Invalid shape: ') + obj.Label)
            geometry.append((obj, shape.BoundBox))
    if not geometry:
        raise PlotError(tr('No printable XY geometry. Check the Plot and Global Freeze level flags.'))
    return geometry


def _layout(settings):
    from PySide import QtCore, QtGui

    if settings.paper not in PAPER_SIZES:
        raise PlotError(tr('Choose a supported paper size.'))
    paper = QtGui.QPageSize(getattr(QtGui.QPageSize.PageSizeId, settings.paper))
    orientation = (QtGui.QPageLayout.Landscape if settings.landscape
                   else QtGui.QPageLayout.Portrait)
    return QtGui.QPageLayout(paper, orientation, QtCore.QMarginsF(), QtGui.QPageLayout.Millimeter)


def _drawing_scale(settings, width, height, span_x, span_y):
    margin = settings.margin_mm
    available_x = width - 2 * margin - STROKE_MM
    available_y = height - 2 * margin - STROKE_MM
    if not math.isfinite(margin) or margin < 0 or min(available_x, available_y) <= 0:
        raise PlotError(tr('The margins leave no room on the page.'))
    limits = [available / span for available, span in (
        (available_x, span_x), (available_y, span_y)) if span > 0]
    if not limits:
        raise PlotError(tr('The drawing has no printable extent.'))
    fit_scale = min(limits)
    if settings.denominator is None:
        return fit_scale
    denominator = settings.denominator
    if not math.isfinite(denominator) or denominator <= 0:
        raise PlotError(tr('Enter a positive scale denominator.'))
    scale = 1.0 / denominator
    if scale > fit_scale and not math.isclose(scale, fit_scale, rel_tol=1e-9):
        raise PlotError(tr('The drawing does not fit at this scale. Choose a larger sheet or a smaller scale.'))
    return scale


def _sheet_svg(geometry, settings, width, height):
    import Draft

    xmin = min(box.XMin for _obj, box in geometry)
    xmax = max(box.XMax for _obj, box in geometry)
    ymin = min(box.YMin for _obj, box in geometry)
    ymax = max(box.YMax for _obj, box in geometry)
    scale = _drawing_scale(settings, width, height, xmax - xmin, ymax - ymin)
    x = width / 2 - (xmin + xmax) / 2 * scale
    y = height / 2 + (ymin + ymax) / 2 * scale
    fragments = []
    for obj, _box in geometry:
        rgb = displayed_rgb(obj)
        color = "#000000" if rgb == (255, 255, 255) else "#{:02x}{:02x}{:02x}".format(*rgb)
        fragment = Draft.get_svg(obj, scale=scale, linewidth=STROKE_MM, fillstyle="none",
                                 color=color, linestyle=getattr(obj.ViewObject, "DrawStyle", "Solid"))
        if not fragment.strip():
            raise PlotError(tr('Could not convert “{}” to vector geometry.').format(obj.Label))
        fragments.append(fragment)

    # Draft emits world XY coordinates. SVG/PDF page coordinates grow downwards.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm"'
        f' viewBox="0 0 {width} {height}">'
        f'<g transform="translate({x} {y}) scale({scale} {-scale})">'
        + "".join(fragments) + "</g></svg>"
    ).encode("utf-8")


def _render_pdf(path, layout, width, height, data):
    from PySide import QtCore, QtGui, QtSvg

    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(data))
    if not renderer.isValid():
        raise PlotError(tr('Could not load the vector drawing for PDF export.'))
    writer = QtGui.QPdfWriter(str(path))
    writer.setCreator("UniStation")
    writer.setResolution(PDF_DPI)
    if not writer.setPageLayout(layout):
        raise PlotError(tr('Could not set the PDF page layout.'))
    painter = QtGui.QPainter()
    if not painter.begin(writer):
        raise PlotError(tr('Could not open the PDF for writing.'))
    try:
        dots_per_mm = writer.resolution() / 25.4
        renderer.render(painter, QtCore.QRectF(0, 0, width * dots_per_mm, height * dots_per_mm))
    finally:
        finished = painter.end()
    if not finished:
        raise PlotError(tr('Could not finish writing the PDF.'))


def export_pdf(document, destination, settings=PlotSettings(), objects=None):
    """Plot the supplied whole objects, or all supported objects in the document."""
    from PySide import QtGui

    same_document(document)
    geometry = _plot_objects(document, objects)
    layout = _layout(settings)
    paper = layout.fullRect(QtGui.QPageLayout.Millimeter)
    width, height = paper.width(), paper.height()
    data = _sheet_svg(geometry, settings, width, height)
    destination = Path(destination)
    if destination.suffix.lower() != ".pdf":
        raise PlotError(tr('Choose a file with the .pdf extension.'))

    handle, temporary_path = mkstemp(dir=destination.parent, prefix=".ustn-plot-", suffix=".pdf")
    temporary = Path(temporary_path)
    try:
        # Qt opens the path itself. Release the Python handle first on Windows.
        os.close(handle)
        _render_pdf(temporary, layout, width, height, data)
        with temporary.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                raise PlotError(tr('The PDF writer did not produce a PDF file.'))
            stream.seek(max(0, temporary.stat().st_size - 1024))
            if not stream.read().rstrip().endswith(b"%%EOF"):
                raise PlotError(tr('The PDF writer did not finish the file.'))
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
    return len(geometry)
