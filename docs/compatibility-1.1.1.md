# FreeCAD compatibility

The metadata declares FreeCAD 1.1.1–1.1.4 and Python 3.11. The Windows installer
contains an x64 AxisFlow extension; matching package names alone do not establish
binary compatibility.

Earlier UniStation functionality was successfully checked in 1.1.1. The layers,
ByLayer, palette and PDF work added for alpha.4 was checked in 1.1.4. A complete
alpha.4 run in 1.1.1, intermediate versions 1.1.2/1.1.3 and arbitrary library
combinations have not been verified.

The earlier static minimum-version review compared official FreeCAD source
commits 0108fd4b4850cc46e625b60e53cea7a7bbe69f8d (1.1.1) and
4fd3bf320d9566a27e60069fc8387448aaa3a094 (1.1.4). That comparison does not
replace runtime validation of new features or the installer.

AxisFlow theme_01 was built with the 1.1.1 SDK, Python 3.11.14 and MSVC 19.44,
and used with the reference 1.1.4 environment. Its binary and full source archive
are unchanged from alpha.3. [Dependencies](dependencies.md) ·
[Current results](testing.md) · [Installer](installer.md).
