# Installation / Установка

## Windows installer — recommended

Download the [alpha.3 setup executable](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/UniStation-0.1.0-alpha.3-win64-setup.exe)
and close FreeCAD. Choose language, components and the parent **Mod** directory.
Default: `%APPDATA%\FreeCAD\v1-1\Mod`. Setup creates UniStation/AxisFlow inside it.
Start FreeCAD normally, select UniStation, then create/open a document.
FreeCAD is external; no PowerShell command or separate candidate profile is needed.

The setup/uninstall/restore workflow still requires runtime validation.
It is a prerelease and the executable is unsigned. Read the
[installer guide](../packaging/installer/USER-GUIDE.md),
[release notes](release-v0.1.0-alpha.3.md) and [dependencies](dependencies.md).
For a custom/portable profile, choose its actual Mod directory. Setup does not
auto-detect FreeCAD.exe or establish arbitrary binary ABI compatibility.

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
