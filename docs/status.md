# Prototype status / Состояние прототипа

Product baseline: 2026-11-06. Publication preparation: 2026-11-09.
This snapshot does not claim a complete regression or a clean-machine install.

## Reported user acceptance

The user reported successful checks of English/Russian translation after the
startup correction, active attributes, the snapping toolbar, preview styling,
operation settings and the separate coordinate window, changing attributes
while drawing, and Circle/Arc after compass rotation. Each acceptance covers
the scope reported at that time, without an exhaustive scenario list.
Move with preselection and AxisFlow's themed appearance/normal operation were
also reported working. Those results do not prove every command combination,
Undo/Redo path, file round trip, monitor/DPI configuration or ABI combination.

## Awaiting separate confirmation

- RESET-001: corrected right-click delivery, in-task menu availability and
  command-owned rewind behavior. The first implementation had a failed user
  check; the correction is reviewed in code, not yet separately accepted.
- TOOLBARS-006: disabled Rectangle / Freeform Shape buttons.
- ATTRIBUTES-006: the user confirmed the Layer button exists. This is not
  acceptance of layer functionality or all display states.
- Earlier toolbar regrouping/drawing icons and attribute compactness
  (TOOLBARS-003/004, ATTRIBUTES-004) have no separate complete acceptance record.

## Known limitations

| Area | Current limitation |
| --- | --- |
| Circle lifecycle (AF-002) | A historical native access violation occurred during document/workbench lifecycle testing. Later isolated success did not establish a fix or prove AxisFlow ownership. Finish/cancel Circle before switching as a practical precaution, not a proven workaround. |
| Coordinate entry (AF-001) | Earlier external key-in focus problems and full acceptance remain open; the separately accepted window relocation does not close all earlier key-in scenarios. |
| Palette (PAL-001..003, LOC-001) | Editor read-only state after Undo/failure, unexpected dialog errors/target selection changes and strict JSON version handling remain recorded limitations. |
| Locate (LOC-003) | A compound mouse gesture may retain an armed click; this was a static observation. LOC-002 command availability was corrected in code, without separate GUI confirmation. |
| Layers | Layer selector is disabled; creation, assignment, visibility and ByLayer inheritance are absent. |
| Drawing | Rectangle/Freeform are disabled; Wire arc segments are deferred. |
| Transform | Only conservative preselected whole-object Move/Copy; Scale/Rotate/Mirror/Array are disabled. |
| Weights | No table editor, existing-object assignment workflow, direct-width return or print-millimeter model. |
| Tests (TEST-003/004) | Old GUI assertions refer to removed instruction widgets; Circle/Arc doubles lack the live-plane API contract. No new failed run is implied. |
| Installation | No bundled runtime, Addon Manager promise or clean-machine acceptance; the active AxisFlow binary is not reproducibly tied to source. |

Recorded issues are not silently marked fixed by publication. Further diagnostic
work, binary packaging and CI are separate decisions. No test or GUI run was
performed as part of preparing this snapshot. [Testing details](testing.md).

## По-русски

Пользовательские приёмки относятся к сообщённому объёму соответствующих
редакций. Приняты перевод после исправления запуска, активные атрибуты,
привязки, динамика, настройки операций/окно координат, смена атрибутов во время
рисования и поворот компаса Circle/Arc. Общая полная регрессия не заявляется.

Отдельного подтверждения исправленного Reset пока нет. У «Слоя» подтверждено
наличие кнопки, функционал не реализован. Две заготовки рисования и прежние
изменения группировки/компактности отдельно полностью не приняты.

AF-002, прежние ограничения фокуса key-in, PAL/LOC, старые assertions/doubles
тестов и отложенный функционал остаются открытыми в указанном выше объёме.
Публикация исходников их не закрывает. Ручная установка на чистом компьютере
и готовый бинарный комплект ещё не подтверждены.
