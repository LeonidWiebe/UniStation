# UniStation v0.1.0-alpha.6 — FreeCAD detection and startup shortcut

[Download the Windows installer](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.6/UniStation-0.1.0-alpha.6-win64-setup.exe).

This prerelease updates packaging. UniStation's 57 runtime source files and all
34 AxisFlow payload files are unchanged from alpha.4.

- Setup detects FreeCAD from the saved path, Windows registry and standard
  Program Files locations, with manual selection when no suitable copy is found.
- It checks FreeCAD 1.1.1–1.1.4, x64 executables and Python 3.11 files. The
  console `FreeCADCmd.exe --version` check does not open the FreeCAD GUI.
- Optional **UniStation - FreeCAD** shortcuts on the desktop and Start menu
  select the configured FreeCAD and open UniStation automatically. Install and
  work using the same Windows account; the launcher reports an account mismatch.
- Fixed uninstall startup: the state directory is resolved from the original
  uninstaller location, rather than the temporary NSIS copy. Ownership checks
  remain enabled. Install alpha.6 over alpha.5 into the same Mod directory before
  retrying uninstall; no manual state.ini changes are required.
- Installed metadata handles FreeCAD's revision component at the 1.1.4 upper
  boundary; setup and startup still enforce the exact 1.1.1–1.1.4 range.

## Validation and limits

Manual installation and FreeCAD launch in 1.1.3 passed; the retest after the
alpha.6 uninstall fix succeeded in the reported scope. Detailed acceptance of
every component, rollback, detection branch and library combination is not
claimed. Both NSIS 3.12 builds have zero warnings; all 123 extracted payload
files match the build manifest. No new automated/FreeCAD/GUI run was performed
for publication, and the tested EXE was not rebuilt.

The alpha.4 allowlisted unit result remains **58/67 passed, 5 failures, 4 errors**
in legacy Circle/Arc tests. It was not rerun and is not a passing full regression.
Earlier product checks in 1.1.1 and targeted feature checks in 1.1.4 retain their
original scope. The full 1.1.1–1.1.4 range and arbitrary ABI combinations are not
certified. The installer has no Authenticode signature.

Layers, ByLayer, Change Attributes, Edit Palette and direct XY vector PDF remain
as in alpha.4. Circle lifecycle, Reset, coordinate-entry, Palette/Locate and
legacy testing limitations remain open. Per-view layers, protection outside
UniStation, TechDraw and external layer libraries are deferred.
[Status](status.md) · [Testing](testing.md).

## Files and rebuilding

The release includes the tested Windows EXE, the complete current repository
source ZIP, BUILD-MANIFEST.json and SHA256SUMS.txt. The EXE's embedded documents
and Installer-source.zip preserve the earlier build-time snapshot; these notes
and the current guides record subsequent manual acceptance. The pinned alpha.2
archive supplies unchanged AxisFlow when rebuilding. Full corresponding
AxisFlow sources and LGPL notices are included with its component.
UniStation is GPL-3.0-only; AxisFlow is LGPL-2.1-or-later. FreeCAD is external.
[Installer guide](installer.md) · [Build](../packaging/installer/BUILD.md).

## По-русски

Выпуск добавляет поиск и проверку версии FreeCAD, ручной выбор EXE и ярлыки
«UniStation - FreeCAD» с автоматическим выбором верстака. Установка выполняется
для текущего пользователя Windows. Исправлено начало удаления: деинсталлятор
использует исходный каталог служебных файлов, проверка принадлежности сохранена.

Ручные установка и запуск FreeCAD прошли успешно; повтор после исправления
удаления alpha.6 также успешен в объёме этой пробы. Полная регрессия и аварийный
откат не заявлены. Проверенный EXE не пересобирался, новых автопрогонов нет.
Для обновления alpha.5 установите alpha.6 поверх в тот же Mod. Предыдущие
публичные выпуски сохранены; alpha.5 был локальным кандидатом.

Следующий функциональный пакет — локальная конфигурация проекта и пути поиска,
затем внешние библиотеки слоёв. Сайт в этом выпуске не обновлялся.
