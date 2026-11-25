# UniStation

[Русский](README.ru.md) · [Website](https://ustation.ru/en/)

I am building UniStation for my own work with the help of AI tools and sharing
it with anyone interested. It is an experimental FreeCAD workbench for people
used to MicroStation and AutoCAD. AxisFlow provides AccuDraw-like precision input.

**[Download Windows installer v0.1.0-alpha.12](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.12/UniStation-0.1.0-alpha.12-win64-setup.exe)** ·
[Release notes](docs/release-v0.1.0-alpha.12.md).

Select UniStation/AxisFlow, FreeCAD, documentation/shortcuts and the parent Mod
directory. Default: `%APPDATA%\FreeCAD\v1-1\Mod`. FreeCAD is installed
separately. The **UniStation - FreeCAD** shortcut opens it with the workbench active.
[Installer guide](docs/installer.md).

## Available

- Drawing and supported whole-object editing with AxisFlow and shared Draft snaps.
- Line continuation, enabled by default: each endpoint anchors the next segment.
- Wire with straight and exact circular arc segments in one object.
- FCStd layers, modeless manager, assignment, Global Display/Freeze, supported
  Lock behavior, Plot, persistent ByLayer attributes and Change Attributes.
- Edit Palette with 256 indexed colors and JSON Load/Save; direct planar XY PDF.
- Five toolbars, English/Russian UI, coordinate input and live drawing attributes.
- Updated FreeCAD/Windows icons and floating-toolbar width restoration.

[Usage](docs/usage.md) · [Status and limits](docs/status.md).
Rectangle/Freeform and Scale/Rotate/Mirror/Array remain disabled. Move/Copy need
preselected supported whole objects. Per-view layers, protection outside
UniStation, external layer libraries and TechDraw are deferred.

## Compatibility and checks

Windows x64 / Python 3.11, FreeCAD 1.1.1–1.1.4. Earlier revisions were checked
in 1.1.1 and 1.1.3; recent feature checks used 1.1.4. Full alpha.12 coverage of
the range and arbitrary ABI combinations are not established.

Line continuation passed 22/22 targeted Python tests and 2/2 Qt scenarios;
Wire arcs passed 14/14 and 1/1. Both manual feature checks passed in their scope.
The alpha.11 installer passed its manual check; the new alpha.12 EXE's own
installation/installed-feature smoke remains pending. No fresh tests or GUI
runs were performed for publication. EXE is unsigned. [Testing](docs/testing.md).

Full removal now selects both managed components and automatically sends backup
data to the Recycle Bin after removing the last component. Cleanup errors show
the remaining path. [Removal details](docs/installer.md#upgrade-and-removal).

## Plans and source

Local project configuration/search paths, external layer libraries, cell/shared
cell libraries, references management and saved views. Current delivery is a
workbench; a future FreeCAD fork is possible.

[Build](packaging/installer/BUILD.md) · [Changes](CHANGELOG.md) ·
[Contributing](CONTRIBUTING.md). AxisFlow and old releases remain unchanged.
UniStation: **GPL-3.0-only**. AxisFlow: **LGPL-2.1-or-later**.
[LICENSE](LICENSE) · [Notices](THIRD_PARTY_NOTICES.md).
