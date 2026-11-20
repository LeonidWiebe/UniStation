# UniStation v0.1.0-alpha.4 — layers, attributes and PDF

This Windows prerelease packages the UniStation source snapshot of 20 November
2026. It includes the additions developed after alpha.3.

- FCStd layers: modeless manager, active layer, assignment, Global Display,
  Global Freeze, Lock in supported operations, and Plot.
- Persistent ByLayer color, line style and weight; inherited attributes update
  when the layer changes. Change Attributes applies selected properties to
  selected objects or to an object located after starting the command.
- Edit Palette with JSON Load/Save and 256 indexed colors. The separate
  Palette toolbar has been removed; the workbench now has five toolbars.
- Direct vector PDF output for supported planar XY geometry: drawing or whole
  selected objects, A4–A0, orientation, margins and scale, respecting Plot and
  Global Freeze.
- Toolbar sizing, layer tooltips and the existing drawing/Move/Copy workflow.

## Installation

[Download the Windows setup](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.4/UniStation-0.1.0-alpha.4-win64-setup.exe).
Close FreeCAD. Select UniStation, AxisFlow and optional documentation/Start menu
links, then select the **parent Mod directory**. Default:
`%APPDATA%\FreeCAD\v1-1\Mod`. Start FreeCAD normally after installation.
FreeCAD is installed separately. [Installer guide](installer.md).

Windows x64 / Python 3.11. The declared FreeCAD range remains 1.1.1–1.1.4.
Earlier UniStation functionality was tested in 1.1.1; the recent feature checks
used 1.1.4. Alpha.4 as a whole has not been retested in 1.1.1, and the full range
and arbitrary binary/library combinations are not certified.

The installer is built with NSIS 3.12 and inspected without executing it.
Setup, uninstall and failure recovery still require runtime validation.
The executable has no Authenticode signature. Existing feature checks are
documented separately from this release's checks in [testing](testing.md).
There is no claim of complete regression or clean-machine acceptance.

AxisFlow theme_01 (0.2.1) and its corresponding source archive are retained
unchanged from alpha.3. FreeCAD and AxisFlow are not rebuilt. UniStation is
GPL-3.0-only; AxisFlow is LGPL-2.1-or-later. Full AxisFlow sources and notices
are supplied with its selected component. The source asset includes current
UniStation and installer sources; the pinned alpha.2 archive supplies AxisFlow
when rebuilding. [Build instructions](../packaging/installer/BUILD.md).

## Limits and next work

Layer protection outside the active UniStation workbench, per-view layer
visibility, TechDraw output and external layer libraries are deferred. PDF is
direct XY vector output, not a general print-layout or TechDraw replacement.
Rectangle/Freeform and Scale/Rotate/Mirror/Array remain disabled placeholders.
Move/Copy require preselected supported whole objects. Recorded Circle lifecycle,
Reset, coordinate-entry, Palette/Locate and legacy test limitations remain open.
[Status](status.md).

Next: local project configuration and search paths, followed by external layer
libraries. Block libraries (cells/shared cells), reference management and saved
views are planned. Current delivery is a workbench; a future FreeCAD fork remains
a possible direction.

## По-русски

В alpha.4 опубликованы текущие слои FCStd, «По слою», Change Attributes,
Edit Palette с Load/Save и прямой PDF. Установщик предлагает выбор компонентов
и каталога, по умолчанию `%APPDATA%\FreeCAD\v1-1\Mod`.
FreeCAD устанавливается отдельно. Новые функции проверялись целевыми сценариями
в 1.1.4; прежняя проверка 1.1.1 не означает повторную проверку в ней всей alpha.4.
Исполнение мастера, удаления и аварийного восстановления ещё не проверено.
Бинарник AxisFlow и его исходники сохранены без изменений. Старые выпуски
остаются в истории. Публикация не закрывает перечисленные ограничения.

## Alpha.4 unit run — 20 November 2026

The approved axisflow-core run completed without FreeCAD or GUI: **67 tests,
58 passed, 5 failures, 4 errors, 0 skipped**. The nine non-passing cases are
Circle/Arc tests, consistent with the recorded TEST-004 live-plane test-double
limitation. They are not marked fixed and the release is not a passing full
regression. [Machine-readable report](alpha4-unit-result.json).
The first sandbox attempt stopped after an error/hang without a completed
report; the completed run used the same allowlist outside that sandbox.
