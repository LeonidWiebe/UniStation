# Usage / Работа с UniStation

## English

Open or create a FreeCAD document, then activate UniStation. Use AxisFlow's
current bindings and settings to position and confirm points. In the recorded
local keymap, `P` confirms a point, Enter is Smart Lock and Escape is FinishLine;
bindings can be changed, so inspect AxisFlow rather than assuming Enter confirms.

| Command | Input and result |
| --- | --- |
| Line | Two distinct points create one Draft line |
| Wire | Collect vertices; Finish creates an open wire, Close contour requires at least three vertices; returning to the first point closes it |
| Circle | Center and radius point; orientation follows the live compass |
| Arc | Start, through-point, end; accepted world points remain fixed |
| Move / Copy | Preselect supported whole objects, then give base and target points |

Move/Copy accept independent Draft wires/circles/arcs and simple Part features.
Subelements, dependent/nested/attached objects and unsupported types are
rejected. There is no selection stage after starting these commands.

## Toolbars / Панели

| Toolbar / Панель | Contents / Состав |
| --- | --- |
| UniStation | Cancel UniStation, Coordinate Input |
| Drawing / Рисование | Line, Wire, Circle, Arc, Rectangle, Freeform Shape |
| Manipulations / Манипуляции | Copy, Move, Scale, Rotate, Mirror, Array |
| Palette / Палитра | Assign indexed color, edit palette, import, export |
| Attributes / Атрибуты | Layer, active color, line style, line weight |
| Snapping / Привязки | Master Draft/AxisFlow control and 14 Draft modes |

Layer and the last two Drawing / last four Manipulations commands are disabled
placeholders. Floating toolbars have a title and close control; show hidden
toolbars through FreeCAD's toolbar menu. Their layout is saved in the profile.

## Attributes, coordinates and Reset

Choose a color index 0–255, one of four native line styles and a weight index
0–31. During Line/Wire/Circle/Arc, confirmed changes update the preview and
the eventual object. An unfinished Wire changes styling as a whole. Existing
selected objects are not restyled by these active-attribute controls.
Initial screen widths are index + 1, not printed millimeters.

The Palette commands separately assign indexed color to existing supported
objects and edit/import/export the document palette. The JSON file extension
is `.ustnpalette.json`; reading the older `.uspalette.json` extension is retained.

Open **UniStation → Coordinate Input** for Line/Wire/Circle. Example inputs:

```text
abs 10; 20; 0
rel 5 cm; 0; 0
```

These are world XYZ coordinates, not compass-local coordinates. Relative input
uses the previous accepted point (Wire: last vertex). Escape/close hides only
this modeless window. Arc/Move/Copy are not connected to this syntax.

**Reset** rewinds one step; a consecutive Reset without a new accepted point
exits. Wire/Arc remove the last point; Move/Copy keep the selection and clear
the base point/ghost. Reset is not Undo. Cancel/Close discard unfinished input;
Wire's FinishLine instead creates the open wire when enough points exist.

In **UniStation → Preferences**, assign right-click to Native or Reset and
configure operation-result selection (off by default). Right-click Reset was
corrected in code; separate user confirmation of the corrected behavior is
still pending. Snapping controls share Draft/AxisFlow state and can change
during drawing. Language is selected in FreeCAD's application preferences.

## По-русски

Создайте/откройте документ. Точки вводите через AxisFlow с его текущими
клавишами: в зафиксированной раскладке `P` подтверждает точку, Enter — Smart Lock,
Escape — FinishLine. При изменённой раскладке смотрите настройки AxisFlow.

Line — две точки; Wire — цепочка с завершением/замыканием; Circle — центр и
радиальная точка; Arc — начало, промежуточная точка, конец. Для Move/Copy
сначала выделите целые независимые поддерживаемые объекты, затем задайте
базовую и целевую точки. Выбор после запуска пока отсутствует.

Активные цвет/стиль/толщина меняются до и во время рисования. Динамика и
новый объект получают последние значения; вся незавершённая Wire оформляется
единообразно. Толщина — экранная, не печатные мм. Назначение цвета старым
объектам выполняется отдельно через «Палитру».

Окно **UniStation → Ввод координат…** принимает приведённые выше мировые
`abs`/`rel` XYZ для Line/Wire/Circle. Относительная база — принятая точка,
у Wire последняя вершина. Закрытие окна не отменяет команду.

Первый Reset возвращает шаг, повторный без новой принятой точки выходит.
Wire/Arc убирают одну точку; Move/Copy сохраняют выбор. Cancel/Close отменяют
незавершённое построение; для создания Wire используйте завершение ломаной.
Назначение ПКМ и автовыделение результата находятся в настройках UniStation.
Автовыделение по умолчанию выключено. Привязки общие с Draft/AxisFlow.

[Ограничения и подтверждённые результаты](status.md).
