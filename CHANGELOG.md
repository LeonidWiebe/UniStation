# Changes

## Documentation refresh — 2026-11-09

- Refreshed current status, installer/source installation, dependencies and author voice.
- Publication confirmed; installer runtime validation remains pending.
- Versioned EXE/ZIP/tag snapshots, runtime code and licenses are unchanged.

## v0.1.0-alpha.3 Windows installer prerelease — 2026-11-09

- Added a per-user RU/EN wizard: UniStation/AxisFlow selection, documentation,
  Start menu links, custom parent Mod directory and uninstall component selection.
- Default Mod directory: `%APPDATA%\FreeCAD\v1-1\Mod`. FreeCAD stays external.
- Retained same-volume backups, ownership checks and restoration; no recursive
  deletion of the shared Mod tree or changes to FreeCAD configuration.
- Product runtime/AxisFlow unchanged; no GUI or automated behavioral runs.
- Setup published as the recommended download by explicit user instruction;
  installer/uninstaller GUI acceptance remains pending. Alpha.2 assets unchanged.

This log describes the prototype's source state; these dates are not release
tags or evidence of a new installation test.

## v0.1.0-alpha.2 prerelease — 2026-11-09

- Tested with FreeCAD 1.1.1; this does not establish a full regression or
  certify every Python/Qt/OS combination.
- Published packaging metadata, launcher and documentation, plus the original
  alpha.2 ZIP assets and SHA256SUMS. Archive bytes remain from build commit
  25fca51; embedded pending text is the pre-check build state.
- Updated public download/install guidance and release notes. Product runtime,
  AxisFlow, licenses and known limitations are unchanged. No automated runs.

## 0.1.0-alpha.2 minimum-version candidate — 2026-11-09

- Admitted FreeCAD 1.1.1 as an experimental test minimum; maximum remains 1.1.4.
- Compared pinned source tags: 23 reviewed API implementation files identical;
  checked custom profile/launcher support and Python 3.11 syntax.
- Added official 1.1.1 download identity and a separate-profile user check.
- Product runtime and AxisFlow unchanged; official 1.1.1 binary ABI/load and
  installation were pending at candidate build time. The subsequent product
  check succeeded; it does not validate the later installer. No automated runs.
- Alpha.1 archives retained unchanged; no GitHub Release published.

## 0.1.0-alpha.1 installation candidate — 2026-11-09

- Added workbench metadata, explicit target ABI and deterministic ZIP builder.
- Added separate-profile Windows launcher and manual installation check.
- Associated accepted AxisFlow theme_01 with public source snapshot
  7daa0ffd776eac559ed7468bec43911ec159adbb through build manifests.
- Prepared local candidate archives with LGPL text and complete AxisFlow sources.
- Runtime unchanged; no new binary build or GUI/automated behavioral runs.
- User installation acceptance and GitHub Release remain pending.

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
привязки и актуальную плоскость компаса. Подробные границы завершённых
проверок и ожидающие подтверждения изменения — в [статусе](docs/status.md).
