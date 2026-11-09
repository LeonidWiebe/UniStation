# UniStation

[Русский](README.ru.md)

UniStation is an experimental Python workbench for FreeCAD. It brings a drafting
workflow inspired by MicroStation to FreeCAD, with precise point input through
[AxisFlow](https://github.com/LeonidWiebe/AxisFlow).

This is a source snapshot of a working prototype. The documented local runtime
is Windows with FreeCAD 1.1.4. A downloadable, independently verified installation
bundle is still being prepared; this repository does not include FreeCAD or an
AxisFlow binary.

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

1. Read [dependencies](docs/dependencies.md) and the
   [manual installation procedure](docs/installation.md).
2. Follow [usage](docs/usage.md) with a compatible FreeCAD/AxisFlow environment.
3. Read [testing status](docs/testing.md): publishing preserved tests does not
   mean they have been run against this snapshot.

Manual installation is documented for experienced FreeCAD users; it has not
been independently verified on a clean computer. Addon Manager installation,
a portable application bundle and a turnkey installer are not provided here.

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
