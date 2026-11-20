# Using UniStation / Работа с UniStation

Open/create a document and activate UniStation. AxisFlow provides precision
point input similar to AccuDraw. Use its current bindings; they are configurable.
Line takes two points, Wire collects vertices, Circle uses center/radius and
the live compass orientation, Arc uses three world points. Move/Copy require
preselected supported whole objects, then base/target points.

| Toolbar | Contents |
| --- | --- |
| UniStation | Key-in, Level Manager, Print to PDF, Edit Palette |
| Drawing | Line, Wire, Circle, Arc; Rectangle/Freeform placeholders |
| Manipulations | Copy, Move; Scale/Rotate/Mirror/Array placeholders |
| Attributes | Active layer, color, style, weight, Change Attributes |
| Snapping | Master control and 14 Draft snapping modes |

## Layers and attributes

Open Level Manager. Add/edit layers and click Apply; the modeless manager stays
open and remains bound to its document. Choose the active layer on Attributes.
Layers are stored in FCStd. Global Display/Freeze affect model display and
selection; Lock blocks supported UniStation edits; Plot controls direct PDF.
These controls do not protect documents opened outside UniStation.

Color, four line styles and 32 screen-weight indices can be explicit or ByLayer.
Inherited attributes update after layer edits/reassignment. Live attribute
changes during drawing update the preview without discarding accepted points.
Weight indices are screen widths, not a print-millimeter model.

To edit existing elements, preselect them and open Change Attributes at the
right of Attributes. Check only properties to change and Apply in Tasks.
With no selection, configure the same task, then use Locate to pick an element.

## Palette and PDF

Edit Palette at the right of UniStation edits 256 indexed document colors.
Load replaces the document palette after confirmation. Save exports the document
palette to JSON; Apply to document commits manual edits. The separate Palette
toolbar is removed.

Print to PDF exports supported planar XY geometry, either the drawing or whole
selected objects. Choose A4–A0, orientation, margins and scale. Plot and Global
Freeze are respected. TechDraw/general page layouts are not included.

## Coordinates and completion

Key-in is a separate window for Line/Wire/Circle, using world abs/rel XYZ and
mm/cm/m. Closing it leaves drawing active. AxisFlow remains the primary input.
Reset rewinds a step, then exits on a repeated Reset without another accepted
point; its corrected mouse delivery has no separate complete acceptance.
Finish/cancel Circle before changing documents/workbenches as a precaution.
Save drawings with Ctrl+S outside installer state directories.
[Known limitations](status.md).

## По-русски

Создайте документ и включите UniStation. На панели UniStation находятся
менеджер слоёв, прямой PDF и Edit Palette. Менеджер остаётся открытым после
«Применить». Активный слой и атрибуты выбираются на панели Attributes;
Change Attributes справа меняет отмеченные свойства выделения или указанного
элемента. Load/Save в Edit Palette работают с JSON-палитрой; ручные правки
применяются отдельно. PDF предназначен для планарной геометрии XY и учитывает
Plot/Global Freeze. Сохраняйте документ в FCStd. Ограничения приведены выше.
