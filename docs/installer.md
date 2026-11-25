# Windows installer alpha.12

[Download setup](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.12/UniStation-0.1.0-alpha.12-win64-setup.exe) · [Release notes](release-v0.1.0-alpha.12.md).

Close FreeCAD and run setup under the Windows account used for CAD work.
Confirm the detected FreeCAD.exe or browse to it. Setup checks the version,
64-bit executable and Python 3.11 files. Supported range: FreeCAD 1.1.1–1.1.4.
FreeCAD is not bundled or downloaded automatically.

Choose UniStation, AxisFlow and optional documentation/shortcuts. Select the
**parent Mod directory**; default `%APPDATA%\FreeCAD\v1-1\Mod`.
Both main components are selected by default. UniStation alone requires a
compatible existing AxisFlow in that Mod. Use **UniStation - FreeCAD** on the
desktop or Start menu to open the configured FreeCAD with the workbench active.
The launcher sets the data directory for its child process, without resetting
the account's preferences. Ordinary FreeCAD launch also allows manual selection.

## Upgrade and removal

Close FreeCAD before upgrading in the same Mod. Existing selected components
are retained in installer transactions. To change Mod, first remove the managed
components from the old location. Unchecking a setup component skips it rather
than uninstalling it.

Use Windows Apps or the uninstall shortcut. Both managed components are selected
by default. A UniStation removal error stops processing before AxisFlow.
Partial removal retains service state. After the last component is removed,
`.UniStation-Installer` is moved out of Mod and sent to the Recycle Bin
automatically, including with /S; there is no extra confirmation or success
message. Cleanup errors identify the remaining path. A failed move leaves
the service folder in Mod. Drawings and FreeCAD preferences are not reset.

The alpha.11 installer passed a manual check in the recorded scope. A short
installation/installed-feature check of alpha.12 is still pending. The EXE is
unsigned; full regression, silent mode and forced recovery are not certified.
[Detailed guide](../packaging/installer/USER-GUIDE.md) ·
[Check](../packaging/installer/USER-CHECK.md) ·
[Build](../packaging/installer/BUILD.md).
