# Distribution / Поставка

Recommended download: **[Windows setup v0.1.0-alpha.6](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.6/UniStation-0.1.0-alpha.6-win64-setup.exe)**.
The release also provides the complete repository source ZIP, BUILD-MANIFEST.json and SHA256SUMS.
[Release notes](release-v0.1.0-alpha.6.md), [installation](installation.md).

Confirm the detected FreeCAD, choose components and a parent directory named Mod
(default `%APPDATA%\FreeCAD\v1-1\Mod`), then use UniStation - FreeCAD.
Setup and work use the same Windows account. FreeCAD is external.
The source repository has no AxisFlow binary; setup includes the separately
replaceable theme_01 module, LGPL and its complete source ZIP when selected.

The installer was compiled with NSIS 3.12 and inspected as PE/archive. Server
digests and anonymous downloads match the saved release files. Manual installation/launch and the alpha.6 uninstall retest passed in the
reported scope; complete regression and forced failure recovery are not certified. The EXE is unsigned.

## Source and rebuilding

The current source snapshot includes tools/build-installer.py and packaging/installer. UniStation is packaged from current source files; the pinned alpha.2 archive supplies only unchanged AxisFlow. The source ZIP asset preserves the complete build inputs for UniStation and the installer. Old release assets and tags remain immutable.

The older tools/build-package.py produces a workbench-only ZIP with flat module
metadata. It does not download/build AxisFlow. This is separate from the Windows
wizard. Read [installer build instructions](../packaging/installer/BUILD.md).

## Earlier alpha.2

The previous ZIP/PowerShell distribution, workbench-only ZIP and standalone
AxisFlow sources remain in [alpha.2](release-v0.1.0-alpha.2.md). The full ZIP is
the pinned input of the current installer build, so it is retained. Its original
candidate/pending wording records the build-time state. For new installations,
use alpha.6. Old versions and immutable build/tag snapshots retain their own text.

## По-русски

Основная установка — EXE alpha.6 с выбором компонентов и каталога.
Старый alpha.2 сохранён для истории и сборки. Исходники/лицензии включены,
FreeCAD устанавливается отдельно. Прежняя версия проверена в 1.1.1, новые функции — в 1.1.4; установка, запуск и повтор удаления проверены в объёме ручной пробы; аварийный откат не подтверждён. Addon Manager как канал установки пока не подготовлен.
