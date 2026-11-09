# Prototype status / Состояние прототипа

Product baseline: 2026-11-06. Publication preparation: 2026-11-09.
This snapshot does not claim a complete regression or a clean-machine install.

## Completed checks

Tested with FreeCAD **1.1.1**; the earlier reference environment is 1.1.4.
English/Russian translation after the startup fix, snapping, styled preview,
operation settings and the separate coordinate window, live drawing attributes,
and Circle/Arc compass behavior have completed manual checks. Move with
preselection and the accepted AxisFlow theme/normal operation were checked earlier.
This does not establish a complete regression, every command combination,
Undo/Redo/lifecycle/DPI scenario or arbitrary ABI. No repeat of completed checks
is required just because documentation changed.

The published alpha.3 installer was compiled and inspected, but its runtime
setup/uninstall/restore flow is **not yet validated**. It is unsigned.
[Current release](release-v0.1.0-alpha.3.md).

## Awaiting separate confirmation

- RESET-001: corrected right-click delivery, in-task menu availability and
  command-owned rewind behavior. The first implementation had a failed user
  check; the correction is reviewed in code, not yet separately accepted.
- TOOLBARS-006: disabled Rectangle / Freeform Shape buttons.
- ATTRIBUTES-006: the Layer button presence was confirmed. This is not
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
| Installation | Alpha.3 setup is published and statically inspected; setup/uninstall/rollback execution remains unvalidated. FreeCAD is external; Addon Manager is not provided. AxisFlow source equivalence is documented, without an independent rebuild. |

Recorded issues are not silently marked fixed by publication. Further diagnostic
work and CI are separate decisions; the Windows installer is already published. No test or GUI run was
performed as part of preparing this snapshot. [Testing details](testing.md).

## По-русски

Ручные проверки подтверждают только проверенные сценарии соответствующих
редакций. Приняты перевод после исправления запуска, активные атрибуты,
привязки, динамика, настройки операций/окно координат, смена атрибутов во время
рисования и поворот компаса Circle/Arc. Общая полная регрессия не заявляется.

Отдельного подтверждения исправленного Reset пока нет. У «Слоя» подтверждено
наличие кнопки, функционал не реализован. Две заготовки рисования и прежние
изменения группировки/компактности отдельно полностью не приняты.

AF-002, прежние ограничения фокуса key-in, PAL/LOC, старые assertions/doubles
тестов и отложенный функционал остаются открытыми в указанном выше объёме.
Публикация исходников их не закрывает. Инсталлятор alpha.3 уже опубликован; исполнение
его установки, удаления и аварийного восстановления ещё не проверено.
