# Using UniStation / Работа с UniStation

Open/create a document and activate UniStation. AxisFlow provides precision
point input similar to AccuDraw. Use its current bindings; they are configurable.
Line takes start and end points, Wire collects vertices, Circle uses center/radius and
the live compass orientation, Arc uses three world points. Move/Copy require
preselected supported whole objects, then base/target points.

| Toolbar | Contents |
| --- | --- |
| UniStation | Key-in, Level Manager, Print to PDF, Edit Palette |
| Drawing | Line, Wire, Circle, Arc; Rectangle/Freeform placeholders |
| Manipulations | Copy, Move; Scale/Rotate/Mirror/Array placeholders |
| Attributes | Active layer, color, style, weight, Change Attributes |
| Snapping | Master control and 14 Draft snapping modes |

## Drawing in alpha.12

These controls are included in the published alpha.12 build.

- **Line** opens with **Continue drawing** checked. Each confirmed endpoint
  creates a separate Draft object and becomes the compass origin and start of
  the next segment. Clear the checkbox before confirming the last segment to
  finish the command.
- **Wire** opens with **Line** selected under **Segment type**. After the first
  vertex, choose **Arc** to add a circular segment. The dashed circle and
  radius follow the cursor while you choose the center. After confirming the
  center, AxisFlow switches to polar mode and the preview shows the arc and
  two guide radii. Confirm the end to restore the previous compass mode.
  Switch back to **Line** before confirming the end to discard the center
  and resume from the last vertex. **Finish wire** and **Close contour** save
  the completed segments in one object.

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
mm/cm/m. During Wire Arc endpoint placement, `rel` uses the accepted center
and the entered endpoint must lie on the circle. Closing Key-in leaves drawing
active. AxisFlow remains the primary input.
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

В рабочих исходниках Line продолжает построение с конца последнего отрезка,
пока включён флажок **«Продолжать выполнение»**. В Wire тип сегмента задаётся
переключателями **Линия / Дуга**. Для дуги укажите центр и конец. После выбора
центра AxisFlow переходит в полярный режим. [Быстрый старт](installation.md).
