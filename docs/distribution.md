# Distribution

Use the [alpha.12 Windows installer](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.12/UniStation-0.1.0-alpha.12-win64-setup.exe).
[Release notes](release-v0.1.0-alpha.12.md) · [Installation](installation.md).

The release provides the existing setup EXE, a complete source ZIP matching the
tag, the original BUILD-MANIFEST.json and SHA256SUMS.txt. Publication does not
rebuild or replace the EXE. Documents inside it remain the build-time snapshot;
the repository and release description record current status.

The per-user wizard offers component selection, FreeCAD detection/version checks,
shortcuts and a parent Mod directory, default `%APPDATA%\FreeCAD\v1-1\Mod`.
FreeCAD is external. Selected AxisFlow includes its unchanged theme_01 binary,
LGPL text and full corresponding source ZIP. The Git repository has no AxisFlow
binary. [Build instructions](../packaging/installer/BUILD.md).

UniStation runtime source bytes match the installer manifest. Only AxisFlow is
taken from the hash-pinned alpha.2 archive when rebuilding. Old versions and tags
remain available unchanged. Addon Manager delivery is not yet provided.

Alpha.11 installer manual acceptance and the accepted Line/Wire feature checks
retain their scopes. The new alpha.12 EXE's own installation smoke remains pending.
