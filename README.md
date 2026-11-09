# UniStation

[Русский](README.ru.md)

**[Download UniStation Windows installer](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/UniStation-0.1.0-alpha.3-win64-setup.exe)**
([v0.1.0-alpha.3 prerelease](https://github.com/LeonidWiebe/UniStation/releases/tag/v0.1.0-alpha.3)).
Choose components and installation directory; default `%APPDATA%\FreeCAD\v1-1\Mod`.
[Instructions and review status](docs/installer.md). The wizard itself still
awaits user validation; compilation and payload checks are complete.

UniStation is an experimental Python workbench for FreeCAD. It brings a drafting
workflow inspired by MicroStation to FreeCAD, with precise point input through
[AxisFlow](https://github.com/LeonidWiebe/AxisFlow).

The installer includes UniStation and optional AxisFlow theme_01 with sources.
FreeCAD is installed separately and started normally. No PowerShell launcher
or separate candidate profile is required. The Git repository tracks no
AxisFlow binary. The earlier ZIP release remains available in release history.

The user reported successful testing in **FreeCAD 1.1.1**, the minimum checked
in that reported scope. 1.1.4 remains the earlier reference environment.
This does not establish every ABI combination or a complete regression.
Read [release notes and installation](docs/release-v0.1.0-alpha.3.md),
[compatibility](docs/compatibility-1.1.1.md) and [distribution](docs/distribution.md).

## Available features

- Line, open/closed polyline, circle from center and radius point, three-point arc.
- Move and Copy for supported, preselected whole objects.
- Document palette with 256 indexed colors and JSON import/export.
- Active color, four line styles and 32 screen weight indices for new geometry.
  These can change during drawing, updating the preview without losing points.
- Six toolbars, shared Draft/AxisFlow snapping controls, mouse Reset assignment,
  optional selection of operation results, and English/Russian interfaces.
- A separate modeless coordinate window for Line/Wire/Circle, supporting world
  `abs`/`rel` XYZ input and mm/cm/m units.

AxisFlow is the primary point-input system. Commands must respect its current
compass state. Circle follows the current compass orientation. Arc keeps already
accepted world points and derives the final arc plane from its three points.

Layer, Rectangle, Freeform Shape, Scale, Rotate, Mirror and Array are disabled
placeholders. Layers and ByLayer behavior are not implemented. See
[status and limitations](docs/status.md) before relying on a feature.

## Start here

1. Download the [installer prerelease](https://github.com/LeonidWiebe/UniStation/releases/tag/v0.1.0-alpha.3)
   and follow its [installation instructions](docs/release-v0.1.0-alpha.3.md).
   For source-only installation, read [dependencies](docs/dependencies.md)
   and the [manual procedure](docs/installation.md).
2. Follow [usage](docs/usage.md) with a compatible FreeCAD/AxisFlow environment.
3. Read [testing status](docs/testing.md): publishing preserved tests does not
   mean they have been run against this snapshot.

The installer supplies addons, with FreeCAD external.
Addon Manager installation is not yet provided or verified. User-reported
testing covers the stated scope, without claiming every installation step.

## Development

[Architecture](docs/architecture.md) · [Changes](CHANGELOG.md) ·
[Contributing and reporting problems](CONTRIBUTING.md)

Please include the commit, FreeCAD/AxisFlow versions, operating system and a
short reproduction when reporting a problem. Do not attach a personal profile
or private drawing. Contact: [info@imapp.su](mailto:info@imapp.su).

## License

UniStation code, original icons, translations and documentation in this
repository are licensed under the GNU General Public License version 3
(`GPL-3.0-only`). See [LICENSE](LICENSE) and
[third-party notices](THIRD_PARTY_NOTICES.md). External dependencies retain
their own licenses.
