# Licensing and external dependencies

UniStation code, original SVG icons, translations, documentation and installer
source are **GPL-3.0-only**; see [LICENSE](LICENSE). The GPL text's copyright
notice belongs to the Free Software Foundation. TS sources accompany QM catalogs.
No proprietary MicroStation code or icon files are included.

## Component delivery

| Component | Recorded license and source | Delivery |
| --- | --- | --- |
| UniStation | GPL-3.0-only | Repository source and optional installed workbench |
| AxisFlow theme_01 | LGPL-2.1-or-later; source snapshot 7daa0ffd776eac559ed7468bec43911ec159adbb | Selected installer component; LGPL and complete source ZIP always included with it |
| NSIS runtime | Included COPYING notice | Installer support directory |
| FreeCAD/Draft/Part | Root LGPL 2.1; individual files may specify LGPL-2.1-or-later or other terms | External FreeCAD installation |
| Python, Qt/PySide, Coin/pivy, OCC | Notices of the exact FreeCAD distribution | External runtime, not bundled by this installer |

AxisFlow remains separately replaceable by a compatible modified module. The
installer uses the accepted theme_01 binary, not the different pyd from the public
v0.2.1 release. Source equivalence was reconstructed from accepted build manifests;
no independent rebuild/bit-reproducibility claim is made. SOURCE-INFO and sources
are installed under Mod/AxisFlow. The repository itself tracks no AxisFlow binary.

Draft snapping icons are referenced by FreeCAD resource names rather than copied.
The old alpha.2 release remains available as the pinned input/build source archive.
[Distribution](docs/distribution.md), [dependencies](docs/dependencies.md).

Primary license files: [FreeCAD](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/LICENSE),
[AxisFlow](https://github.com/LeonidWiebe/AxisFlow/blob/7daa0ffd776eac559ed7468bec43911ec159adbb/LICENSE),
[AxisFlow metadata](https://github.com/LeonidWiebe/AxisFlow/blob/7daa0ffd776eac559ed7468bec43911ec159adbb/package.xml).

MicroStation and AccuDraw are Bentley Systems product names, used to describe
workflow inspiration; no affiliation or endorsement is implied.

## По-русски

Собственные материалы UniStation — GPL-3.0-only. Выбираемый AxisFlow —
LGPL-2.1-or-later, с полным исходным архивом и текстом лицензии. FreeCAD и его
runtime устанавливаются отдельно со своими уведомлениями. Обновление этих
документов не меняет лицензии или уже выпущенные файлы с фиксированными SHA.
