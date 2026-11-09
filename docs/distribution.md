# Installation candidate 0.1.0-alpha.1 / Кандидат установки

This branch prepares packages; it has not been published as a GitHub Release.
Product Python, SVG and TS/QM files remain byte-identical to the initial source
publication, commit `0025de737dcf86152d2e8661ea164217ed2eb955`.

- `UniStation-0.1.0-alpha.1-workbench.zip`: UniStation alone, with InitGui.py
  directly inside UniStation/. AxisFlow is needed separately.
- `UniStation-0.1.0-alpha.1-Windows-FC1.1.4-candidate.zip`: local installation
  candidate with accepted AxisFlow theme_01, its complete source archive and
  LGPL notice, and a separate-profile launcher. FreeCAD is external.
- `AxisFlow-source-7daa0ffd776eac559ed7468bec43911ec159adbb.zip`: all 100 tracked
  files of the source snapshot associated with the accepted theme build through
  documented source equivalence. Not an independent binary rebuild.
- `SHA256SUMS.txt`: checksums of those exact archives.

Read [installation instructions](../packaging/INSTALL.md) and the short
[user check](../packaging/USER-CHECK.md). These are candidate artifact names,
not existing download links or a claim of installation acceptance.

## Metadata and build tool

Repository-root package.xml declares UniStation's inner workbench directory,
GPL-3.0-only, FreeCAD 1.1.4 and AxisFlow. A version dependency alone cannot
verify a C++ addon ABI. Addon Manager listing/installation has not been tested.

```text
python tools/build-package.py --output-dir dist
```

This tool builds only the workbench ZIP. It uses Python's standard library,
parses Python/XML without executing product code, fixes ZIP timestamps and
entry order, and refuses to replace a different archive with the same name.
It flattens only package metadata; runtime code/resources remain unchanged.
It neither downloads nor builds AxisFlow. The full local candidate is assembled
separately from the accepted binary and audited public source snapshot.

The full candidate starts a user-invoked visible FreeCAD with separate config,
data and logs. Existing addons and normal profiles are not installation targets.
No automatic GUI/input checks were performed.

## По-русски

Это подготовка кандидата, а не опубликованный GitHub Release. Полный ZIP
предназначен для новой пользовательской пробы установки на Windows x64 с
зафиксированным FreeCAD 1.1.4. Конфигурация отдельная, личные настройки не
копируются. FreeCAD скачивается отдельно. Рабочий бинарник AxisFlow theme_01
отличается от публичного релиза v0.2.1; приложены соответствующий исходный
снимок, LGPL и сведения о сборке. Побитовая воспроизводимость бинарника новой
сборкой не проверялась. После пользовательской пробы можно готовить GitHub
Release с проверенными архивами и контрольными суммами.
