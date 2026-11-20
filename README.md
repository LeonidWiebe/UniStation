# UniStation

[Русский](README.ru.md) · [Website](https://ustation.ru/en/)

I am building UniStation for my own work with the help of AI tools and sharing
it with anyone interested. It is an experimental FreeCAD workbench for people
used to MicroStation and AutoCAD. AxisFlow provides AccuDraw-like precision input.

**[Download Windows installer v0.1.0-alpha.6](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.6/UniStation-0.1.0-alpha.6-win64-setup.exe)** ·
[Release notes and checks](docs/release-v0.1.0-alpha.6.md).

Setup detects FreeCAD or asks for its executable, checks the version, and
installs selected UniStation/AxisFlow components for the current Windows account.
Default Mod: `%APPDATA%\FreeCAD\v1-1\Mod`. With shortcuts selected, use
**UniStation - FreeCAD** to open the selected FreeCAD with UniStation active.
FreeCAD is installed separately. [Installer guide](docs/installer.md).

## Available

- Drawing and editing supported whole objects with AxisFlow, live attributes
  and shared Draft snapping.
- FCStd layers, modeless manager, active layer/assignment, Global Display,
  Global Freeze, Lock in supported operations and Plot.
- Persistent ByLayer color/style/weight and Change Attributes for existing objects.
- Edit Palette with 256 indexed colors and JSON Load/Save.
- Direct vector PDF for supported planar XY geometry, A4–A0 and scale selection.
- Five toolbars, English/Russian UI and a separate coordinate input window.

[Usage](docs/usage.md) · [Status and limits](docs/status.md).
Rectangle/Freeform and Scale/Rotate/Mirror/Array remain disabled. Move/Copy
require preselected supported whole objects. Per-view layers, protection outside
UniStation, external layer libraries and TechDraw are deferred.

## Compatibility and validation

Windows x64 / Python 3.11; declared FreeCAD range 1.1.1–1.1.4. Earlier product
functionality was tested in 1.1.1; recent feature checks used 1.1.4. This does
not establish a complete alpha.6 regression in 1.1.1 or every ABI combination.

The alpha.4 unit run completed with **58/67 passing, 5 failures and 4 errors**
in Circle/Arc legacy tests; the recorded test-double limitation remains open.
Manual installation and FreeCAD launch passed; the alpha.6 uninstall retest
succeeded in the reported scope. Complete regression, every detection branch
and forced failure recovery are not certified. No new automated run was made.
EXE is unsigned. [Testing details](docs/testing.md).

## Planned

Local project configuration and search paths, then external layer libraries;
block libraries (cells/shared cells), a references manager and saved views.
The project is currently a workbench; a future FreeCAD fork is possible.

## Source and license

[Source installation](docs/installation.md) · [Build](packaging/installer/BUILD.md) ·
[Changes](CHANGELOG.md) · [Contributing](CONTRIBUTING.md).
AxisFlow is separately replaceable; its unchanged theme_01 binary, LGPL notice
and complete corresponding source archive are included when selected in setup.
Old releases remain available. Addon Manager delivery is not provided.

UniStation is **GPL-3.0-only**; AxisFlow is **LGPL-2.1-or-later**.
[LICENSE](LICENSE) · [Third-party notices](THIRD_PARTY_NOTICES.md).
