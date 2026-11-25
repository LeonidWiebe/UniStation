# Installation / Установка

## Windows installer — recommended

Download the [alpha.12 setup executable](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.12/UniStation-0.1.0-alpha.12-win64-setup.exe) and close FreeCAD.
Use the same Windows account for setup and work. Confirm the detected FreeCAD
or choose its EXE, then select components and a directory named **Mod**.
Default: `%APPDATA%\FreeCAD\v1-1\Mod`. Use **UniStation - FreeCAD** from
the desktop or Start menu to open the configured FreeCAD with UniStation active.
FreeCAD remains external. For a custom/portable layout, select its actual Mod.

The wizard checks version 1.1.1–1.1.4 and required x64/Python 3.11 files, not
arbitrary ABI combinations. Earlier alpha.6 installation/launch/uninstall and alpha.11 installer checks
passed in their recorded scope. The new alpha.12 EXE needs a separate installation
smoke check; full regression and failure recovery are not certified. [Installer guide](installer.md) ·
[Release notes](release-v0.1.0-alpha.12.md) · [Dependencies](dependencies.md).

## Alpha.12 upgrade

The alpha.12 build includes Line continuation and circular Wire segments.
When upgrading, select the same Mod directory. Keep the shortcuts component
selected to refresh existing UniStation shortcuts.
[Candidate instructions](installer.md#upgrade-and-removal).

## Manual source installation — advanced

Before copying files, close FreeCAD and preserve existing addon folders.
Find the profile's data directory beforehand with `App.getUserAppDataDir()`.
Copy the complete repository checkout into a folder such as:

```text
<FreeCAD user data>/Mod/UniStation/
  package.xml
  LICENSE
  UniStation/
    InitGui.py
    unistation/...
<FreeCAD user data>/Mod/AxisFlow/
  InitGui.py
  AxisFlow.pyd
  ... compatible separate AxisFlow distribution ...
```

The root package.xml points to the inner UniStation directory. The loader uses
that metadata, so the repository layout is valid. The older workbench-only ZIP
uses a different **flat** layout: InitGui.py and package.xml directly inside
Mod/UniStation, with subdirectory `./`. Keep each package's metadata/layout
together; do not mix files from different versions. Manual source copying does
not supply AxisFlow. The old separate-profile ZIP workflow is documented in
[alpha.2 release notes](release-v0.1.0-alpha.2.md).

## По-русски

Основной способ — EXE: выбрать компоненты и родительский Mod, затем запустить
FreeCAD привычным способом. Подробности — в руководстве мастера выше. При ручной
установке целого checkout сохраняйте корневой package.xml и внутренний UniStation;
для плоского Workbench ZIP сохраняйте его собственную структуру/метаданные.
Совместимый AxisFlow требуется отдельно. Addon Manager пока не поддержан как
проверенный канал установки. Перед сменой документа завершайте Circle;
ограничение AF-002 не объявлено исправленным.

Loader reference: [FreeCAD 1.1.1 GUI init](https://github.com/FreeCAD/FreeCAD/blob/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Gui/FreeCADGuiInit.py).
