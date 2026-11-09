# Distribution / Поставка

Recommended download: **[Windows setup v0.1.0-alpha.3](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/UniStation-0.1.0-alpha.3-win64-setup.exe)**.
The release also provides the installer-source ZIP and SHA256SUMS.
[Release notes](release-v0.1.0-alpha.3.md), [installation](installation.md).

Choose components and the parent Mod directory (default
`%APPDATA%\FreeCAD\v1-1\Mod`), then start FreeCAD normally. FreeCAD is external.
The source repository has no AxisFlow binary; setup includes the separately
replaceable theme_01 module, LGPL and its complete source ZIP when selected.

The installer was compiled with NSIS 3.12 and inspected as PE/archive. Server
digests and anonymous downloads match the saved release files. Runtime
installation/uninstallation/rollback validation remains pending. The EXE is unsigned.

## Source and rebuilding

The installer source/build instructions are under packaging/installer and
tools/build-installer.py. Exact released installer source state is commit
`290f4d5254bad762473be7919b5da684106a09be`; later commits may update documentation.
The source ZIP asset preserves the build snapshot. Documentation refreshes do
not rebuild or replace the published EXE under its existing name/hash.

The older tools/build-package.py produces a workbench-only ZIP with flat module
metadata. It does not download/build AxisFlow. This is separate from the Windows
wizard. Read [installer build instructions](../packaging/installer/BUILD.md).

## Earlier alpha.2

The previous ZIP/PowerShell distribution, workbench-only ZIP and standalone
AxisFlow sources remain in [alpha.2](release-v0.1.0-alpha.2.md). The full ZIP is
the pinned input of the current installer build, so it is retained. Its original
candidate/pending wording records the build-time state. For new installations,
use alpha.3. Old versions and immutable build/tag snapshots retain their own text.

## По-русски

Основная установка — EXE alpha.3 с выбором компонентов и каталога.
Старый alpha.2 сохранён для истории и сборки. Исходники/лицензии включены,
FreeCAD устанавливается отдельно. Работа в 1.1.1 проверена, сам мастер ещё
ожидает ручной проверки. Addon Manager как канал установки пока не подготовлен.
