# Windows installer v0.1.0-alpha.6

[Download setup](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.6/UniStation-0.1.0-alpha.6-win64-setup.exe) · [Release notes](release-v0.1.0-alpha.6.md).

Close FreeCAD and run setup under the Windows account you will use for work.
Confirm the detected FreeCAD.exe or browse to it. If none is found, choose a
manual path or exit and install FreeCAD first. The accepted package range is
FreeCAD 1.1.1–1.1.4, Windows x64 / Python 3.11. Version/file checks do not prove
every ABI combination. FreeCAD is not bundled or downloaded automatically.

Select UniStation/AxisFlow and optional documentation/shortcuts, then a parent
directory named **Mod**. Default: `%APPDATA%\FreeCAD\v1-1\Mod`.
Existing selected module folders are retained in same-volume transactions.
If UniStation is selected without AxisFlow, a compatible AxisFlow must already
be present in that Mod. The desktop and Start menu **UniStation - FreeCAD**
shortcuts open the configured FreeCAD with UniStation active; create/open a
document afterwards. The launcher uses this installation's data directory for
the child process and keeps the current account's preferences.

Alpha.6 fixes the uninstaller's original-directory lookup. Upgrade alpha.5 into
the same Mod before retrying uninstall. Ownership checks remain enabled;
uninstall processes selected managed components and retains retired files and
backups, without recursively deleting the shared Mod or resetting FreeCAD.

Manual installation/launch and the alpha.6 uninstall retest passed in the
reported scope. Full regression, forced failure recovery and every component
combination remain outside that acceptance. The EXE is unsigned.

[Detailed RU/EN guide](../packaging/installer/USER-GUIDE.md) ·
[Manual check](../packaging/installer/USER-CHECK.md) ·
[Build](../packaging/installer/BUILD.md).
