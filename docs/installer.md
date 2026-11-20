# Windows installer v0.1.0-alpha.4

[Download the setup executable](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.4/UniStation-0.1.0-alpha.4-win64-setup.exe).
[Release notes and checksums](release-v0.1.0-alpha.4.md).
The NSIS wizard is published as a prerelease for user review. It installs into an
existing FreeCAD 1.1 profile; FreeCAD is external. Default parent directory:
`%APPDATA%\FreeCAD\v1-1\Mod`. The installer is per-user, without elevation.

Choose UniStation and/or AxisFlow, optional documentation and Start menu links,
then the parent Mod directory. Both main components are selected by default.
If installing UniStation alone, a compatible AxisFlow must already be present.
Restart FreeCAD normally and select UniStation; no command-line launcher or
separate candidate profile is needed.

Selected existing module folders are renamed into retained same-volume backup
transactions under `Mod/.UniStation-Installer`. The uninstaller can remove
selected managed components and restore their previous folders. Retired new
folders and added files are retained as well. It never recursively deletes the
shared Mod directory or resets FreeCAD configuration. Manual replacement without
the ownership marker is preserved instead of being guessed to be installer-owned.

Alpha.4 includes the current 57 UniStation runtime files, including layers, Change Attributes, Edit Palette and PDF. The 34 AxisFlow component files remain unchanged. Wizard execution, uninstall and failure recovery still require separate validation. The executable is unsigned.

[User guide](../packaging/installer/USER-GUIDE.md),
[manual check](../packaging/installer/USER-CHECK.md),
[build instructions](../packaging/installer/BUILD.md),
[source](../packaging/installer/UniStation.nsi).
