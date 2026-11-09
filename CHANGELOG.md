# Changes

This log describes the prototype's source state; these dates are not release
tags or evidence of a new installation test.

## Initial publication preparation — 2026-11-09

- Prepared the source snapshot and public English/Russian documentation.
- Selected GNU GPL version 3 (`GPL-3.0-only`) for UniStation.
- Preserved product files and selected test/tool sources without behavior changes.
- No new FreeCAD, GUI, unit, smoke, Qt or simulated-input runs.

## Product state — 2026-11-06

- Shared Draft/AxisFlow snapping toolbar with a master control and 14 Draft modes.
- Preview color, line style and screen width follow active drawing attributes;
  attributes can change during Line/Wire/Circle/Arc without losing points.
- A separate modeless coordinate window for Line/Wire/Circle.
- Operation-result selection preference, disabled by default.
- Circle/Arc read the live AxisFlow compass plane. Arc keeps accepted world points.
- Command-owned Reset event with step rewind and exit on a consecutive Reset;
  right-click delivery was corrected in code and awaits separate user confirmation.
- Disabled Rectangle and Freeform Shape buttons and a future layer selector.

## Earlier prototype work

- Line/Wire/Circle/Arc and conservative whole-object Move/Copy.
- Indexed document palette, active color/style/weight and persistent toolbar layout.
- English/Russian translations and theme-aware AxisFlow integration.

## По-русски

9 ноября подготовлены исходный снимок и публичные документы, выбрана GPL-3.0-only.
Поведение продукта не менялось, новых тестовых прогонов не было.
Состояние на 6 ноября включает живые атрибуты, отдельное окно координат,
привязки и актуальную плоскость компаса. Подробные границы пользовательской
приёмки и ожидающие подтверждения изменения — в [статусе](docs/status.md).
