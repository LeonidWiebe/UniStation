# Distribution / Поставка

**Recommended:** [Windows installer v0.1.0-alpha.3](release-v0.1.0-alpha.3.md),
with component/directory selection and default `%APPDATA%\FreeCAD\v1-1\Mod`.
FreeCAD is external and started normally; no PowerShell command is required.
The new wizard's runtime GUI validation is pending. Sources/checksums are in
the release. The previous ZIP delivery below is retained as history/build input.

## Previous ZIP delivery — v0.1.0-alpha.2

[Download prerelease v0.1.0-alpha.2](https://github.com/LeonidWiebe/UniStation/releases/tag/v0.1.0-alpha.2).
The user reported successful testing in FreeCAD 1.1.1, accepted in the reported
scope. [Release notes, downloads and installation](release-v0.1.0-alpha.2.md).
Product Python, SVG and TS/QM files remain byte-identical to the initial source
publication, commit `0025de737dcf86152d2e8661ea164217ed2eb955`.

- `UniStation-0.1.0-alpha.2-workbench.zip`: UniStation alone, with InitGui.py
  directly inside UniStation/. AxisFlow is needed separately.
- `UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip`: local installation
  candidate with accepted AxisFlow theme_01, its complete source archive and
  LGPL notice, and a separate-profile launcher. FreeCAD is external.
- `AxisFlow-source-7daa0ffd776eac559ed7468bec43911ec159adbb.zip`: all 100 tracked
  files of the source snapshot associated with the accepted theme build through
  documented source equivalence. Not an independent binary rebuild.
- `SHA256SUMS.txt`: checksums of those exact archives.

Read [installation instructions](../packaging/INSTALL.md) and the short
[user check](../packaging/USER-CHECK.md). Assets keep their original candidate
filenames and bytes. They were built before the user response, so pending text
inside the ZIP is historical. The release notes record the subsequent result,
without claiming unreported steps or all ABI combinations.

## Metadata and build tool

Repository-root package.xml declares UniStation's inner workbench directory,
GPL-3.0-only, user-tested minimum FreeCAD 1.1.1, declared maximum 1.1.4,
and AxisFlow. [Minimum-version review](compatibility-1.1.1.md).
A version dependency alone cannot
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

Это предварительный релиз. Пользователь сообщил об успешной пробе FreeCAD 1.1.1;
результат принят в сообщённом объёме. Полный ZIP предназначен для Windows x64
с минимальной проверенной пользователем версией 1.1.1 и опорной средой 1.1.4.
Метаданные разрешают диапазон 1.1.1–1.1.4 для пробы, но совместимость каждой
версии не подтверждена. Конфигурация отдельная, личные настройки не
копируются. FreeCAD скачивается отдельно. Рабочий бинарник AxisFlow theme_01
отличается от публичного релиза v0.2.1; приложены соответствующий исходный
снимок, LGPL и сведения о сборке. Побитовая воспроизводимость бинарника новой
сборкой не проверялась. ZIP и контрольные суммы сохранены после пробы.
Для точного воспроизведения ZIP используйте build commit 25fca51, а не
последующие изменения документации под release tag.

Alpha.1 archives remain unchanged as the previous 1.1.4-only candidate.
