# UniStation v0.1.0-alpha.12 — Line continuation and Wire arcs

This prerelease publishes the source snapshot of 25 November 2026 and the
existing alpha.12 Windows installer. The EXE is published without rebuilding.

## Changes since alpha.6

- **Line continuation:** Continue drawing is enabled on command start. Each
  accepted endpoint creates a separate line and becomes the start and AxisFlow
  origin for the next segment. Clear the checkbox to finish after the next line.
- **Wire circular segments:** combine Line and Arc segments in one object.
  Choose the arc center, then its end using AxisFlow polar mode. The preview
  shows the construction circle/radius, then the arc and guide radii. The prior
  compass mode returns after the arc or switching back to Line. Circular edges
  remain exact geometry.
- Fixed floating-toolbar width restoration when the saved monitor is unavailable.
- Added the approved FreeCAD workbench icon and Windows icons, with a download
  badge on setup icons from 32 px. Both EXEs contain 14 icon sizes.
- Uninstall stops before removing AxisFlow if UniStation removal fails.
  Both managed components are selected for removal by default. After the last
  component is removed, backup data is moved out of Mod and sent automatically
  to the Recycle Bin, including in silent mode. Cleanup errors show the path
  that remains. Partial removal or a failed move preserves the service folder.

Existing layers/ByLayer, Change Attributes, Edit Palette Load/Save, direct XY PDF,
five toolbars, snapping and English/Russian UI remain included.

## Install

[Download the Windows setup](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.12/UniStation-0.1.0-alpha.12-win64-setup.exe). Close FreeCAD and use your normal
Windows account. Confirm the detected FreeCAD or browse to FreeCAD.exe. Choose
UniStation/AxisFlow, optional documentation and shortcuts, and the parent Mod
directory. Default: `%APPDATA%\FreeCAD\v1-1\Mod`.
FreeCAD is installed separately. The selected FreeCAD must be 1.1.1–1.1.4,
Windows x64 / Python 3.11. Use **UniStation - FreeCAD** to start with the
workbench active. [Guide](installer.md).

## Validation and boundaries

The existing alpha.12 EXE is 3,480,991 bytes, SHA-256
`134189f242ca70e5b86ce446edd22b829d9e7ba3d83e339bea3c7d33bee78fca`.
NSIS 3.12 compiled setup and launcher without warnings. Static inspection
compares all 127 payload files, 59 current UniStation runtime source files and
34 unchanged AxisFlow files. Both EXEs use asInvoker and the approved 14-frame icons.

Targeted development checks on 25 November passed: Line continuation 22/22
Python tests and 2/2 FreeCAD 1.1.4 Qt scenarios; Wire arcs 14/14 Python tests
and 1/1 Qt scenario. Manual checks of both changes passed in the recorded scope.
Python tests used 3.12.10; the Qt environment used FreeCAD 1.1.4, Python 3.11.14
and Qt 6.8.3. These are prior feature checks, not a new publication regression.

The alpha.11 installer passed its manual check on 24 November in the recorded
scope. That does not automatically accept the new alpha.12 EXE: a short install,
shortcut-launch and installed Line/Wire smoke check remains pending. Silent
mode, forced failures and all icon/DPI combinations are not certified.
No tests, FreeCAD/GUI, setup/uninstall or launcher were run for this publication.
The EXE is unsigned. [Testing details](testing.md).

Earlier product revisions were checked in FreeCAD 1.1.1 and 1.1.3. The new
feature checks used 1.1.4. The entire alpha.12 range and arbitrary ABI combinations
have not been tested. Historical Circle lifecycle, Reset, Palette/Locate,
coordinate-entry and TEST-003/004 limitations are retained. Earlier alpha.4's
unit failures are historical and are not described as a new alpha.12 run.
[Current limits](status.md).

UniStation is GPL-3.0-only. AxisFlow theme_01 is LGPL-2.1-or-later; its binary,
license and full corresponding source archive remain unchanged and are supplied
with its selected component. FreeCAD/AxisFlow/QM were not rebuilt. Old releases
and tags are retained. The new full source ZIP matches this tag. Documents inside
the unchanged EXE remain its build-time snapshot; release notes describe the
publication state. [Build instructions](../packaging/installer/BUILD.md).

## По-русски

Выпуск включает продолжение Line и дуговые сегменты Wire в одном объекте,
исправление автоширины, значки FreeCAD/Windows и изменения удаления.
Установщик позволяет выбрать компоненты, FreeCAD и каталог; по умолчанию
`%APPDATA%\FreeCAD\v1-1\Mod`. FreeCAD в комплект не входит.

Целевые и ручные пробы Line/Wire приняты в своём объёме. Ручная проверка
установщика alpha.11 также принята; короткая проба нового EXE alpha.12
остаётся отдельным шагом. Для публикации тесты и приложения не запускались.
EXE сохранён побайтно, предыдущие выпуски остаются доступными.
