# Dependencies and compatibility / Зависимости

UniStation has been tested with **FreeCAD 1.1.1**. The earlier reference runtime
is 1.1.4. The manifest declares 1.1.1–1.1.4 and Python 3.11; this is not a full
test of every intermediate version, library combination or lifecycle scenario.
The new Windows installer's runtime check remains pending.

| Component | Recorded state |
| --- | --- |
| Installer / binary payload | Windows x64, FreeCAD 1.1 with compatible Python 3.11 libraries |
| FreeCAD 1.1.1 source | 0108fd4b4850cc46e625b60e53cea7a7bbe69f8d |
| FreeCAD 1.1.4 source | 4fd3bf320d9566a27e60069fc8387448aaa3a094 |
| Earlier portable 1.1.4 | Python 3.11.14 / Qt 6.8.3 |
| AxisFlow theme_01 SHA-256 | 222678c61f86bb576160c8c939e394470abb2242449fc9d924ea44e9f580426e |
| AxisFlow build SDK | FreeCAD 1.1.1, Python 3.11.14, MSVC 19.44 |
| Equivalent source snapshot by build manifests | 7daa0ffd776eac559ed7468bec43911ec159adbb |

Exact library versions from the earlier 1.1.4 environment must not be assumed
for every 1.1.1 installation. The binary source association matches all 29 C++
files, CMake and QRC; 56/57 baseline entries match, except a non-build archive
helper. It is reconstructed source equivalence, not an independent rebuild or
bit-reproducibility proof. The public AxisFlow v0.2.1 release has a different pyd.

The installer optionally supplies theme_01 with LGPL text, SOURCE-INFO and the
complete source ZIP. The Git repository itself contains no AxisFlow binary.
FreeCAD, Python, Qt/PySide, Coin/pivy and OCC come from the separate FreeCAD
installation. Matching Python package names do not establish compatibility.

## APIs

Point commands use AxisFlow getPoint/endSession/setPlane/isActive. Explicit
coordinates use confirm/setBasePoint; Circle/Arc read getCompassInfo during the
command. Snapping uses getSettings/setSetting and native Draft Snapper modes.
Required input capabilities are checked before ownership. Geometry factories,
transactions, views and selection are provided by FreeCAD/Draft/Part.

UniStation Python needs no compilation. TS/QM sources/catalogs are included;
they were not regenerated for the installer or this documentation refresh.
See [installation](installation.md), [distribution](distribution.md) and
[notices](../THIRD_PARTY_NOTICES.md).

## По-русски

Работа проверена в 1.1.1; 1.1.4 — прежняя опорная среда. Инсталлятор содержит
выбираемый AxisFlow с исходниками, но FreeCAD ставится отдельно. Происхождение
theme_01 восстановлено по принятым манифестам; независимая пересборка не выполнена.
Продуктовая проверка не заменяет проверку нового мастера установки/удаления.
