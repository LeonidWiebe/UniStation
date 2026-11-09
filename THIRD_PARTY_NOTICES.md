# Licensing and external dependencies

UniStation's code, original SVG icons, translations and documentation in this
repository are licensed under GNU GPL version 3 (`GPL-3.0-only`); see
[LICENSE](LICENSE). The GPL text's own copyright notice belongs to the
Free Software Foundation.

The repository contains UniStation Python code, original SVG icons, English and
Russian TS/QM translation catalogs, preserved test sources, selected supporting
tools and project documentation. QM catalogs are generated from the included
TS sources. No proprietary MicroStation code or icon files are included.

## External software, not bundled

| Component | Source inspected | License recorded | Use by UniStation |
| --- | --- | --- | --- |
| FreeCAD, including Draft/Part | [FreeCAD 1.1.4 source](https://github.com/FreeCAD/FreeCAD/tree/4fd3bf320d9566a27e60069fc8387448aaa3a094) | Root LICENSE: LGPL 2.1; individual files may specify LGPL-2.1-or-later or other terms | Host application, geometry factories, view and selection APIs |
| AxisFlow | [API source reference](https://github.com/LeonidWiebe/AxisFlow/tree/5dda554759d813559d94416286014f0cb6fc780e) | LICENSE: LGPL 2.1; package.xml: LGPL-2.1-or-later | Point input, compass and snapping settings through its public API |
| Qt/PySide, Coin/pivy, OpenCASCADE, Python | Supplied by the user's FreeCAD environment | Consult the exact installed distribution's notices | Runtime facilities reached through FreeCAD's environment |

See [FreeCAD LICENSE](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/LICENSE),
[AxisFlow LICENSE](https://github.com/LeonidWiebe/AxisFlow/blob/5dda554759d813559d94416286014f0cb6fc780e/LICENSE)
and [AxisFlow package.xml](https://github.com/LeonidWiebe/AxisFlow/blob/5dda554759d813559d94416286014f0cb6fc780e/package.xml).
The packaging audit subsequently associated the accepted theme_01 binary with
[source snapshot 7daa0ff](https://github.com/LeonidWiebe/AxisFlow/tree/7daa0ffd776eac559ed7468bec43911ec159adbb)
by matching accepted source manifests, not by an independent rebuild.
The separate local candidate includes that binary, all 100 tracked source
files, LGPL text and build information. The repository and workbench-only ZIP
include no AxisFlow binary. See [distribution](docs/distribution.md).

Draft snap icons are requested by their FreeCAD resource identifiers at runtime;
their image files are not copied here. Future binary bundles require an inventory
of the exact distributed components and their corresponding notices and sources.

MicroStation and AccuDraw are Bentley Systems product names. Their mention
describes workflow inspiration and does not imply affiliation or endorsement.

## По-русски

Собственные код, SVG, переводы и документация UniStation — GPL-3.0-only.
FreeCAD, AxisFlow и их зависимости в этот репозиторий не включены и сохраняют
свои лицензии. Указанные commits — опорные версии для анализа API, не доказанное
происхождение используемого локально бинарника AxisFlow. Перед поставкой
бинарного комплекта выполнена отдельная инвентаризация: локальный кандидат
содержит принятый AxisFlow theme_01, полный исходный снимок 7daa0ff,
LGPL и сведения о сборке. Соответствие исходников восстановлено по принятым
манифестам; независимой пересборки и новой проверки установки не было.
