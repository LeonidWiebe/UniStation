# Testing status — alpha.12

Static inspection, automated execution and manual acceptance are separate.
No new tests or applications were run as part of this publication.

## Prior targeted feature checks, 25 November 2026

| Change | Python 3.12.10 | FreeCAD 1.1.4 Qt | Result |
| --- | --- | --- | --- |
| Line continuation | 22/22 | 2/2 on retest | Endpoint anchors the next segment, compass and preview; checkbox controls completion. |
| Wire circular segments | 14/14 | 1/1 | Both preview stages, polar mode/restoration, Arc → Line reset and exact circular geometry. |

The Qt environment used FreeCAD 1.1.4, Python 3.11.14 and Qt 6.8.3 in separate
profiles. The first Line Qt run failed assertions counting document metadata;
the successful retest corrected that count. Both changes also passed manual
checks in the recorded scope. These checks cover working sources included in
alpha.12, not every release scenario.

## Installer

Alpha.12 setup and launcher compiled with NSIS 3.12, without warnings. Static
inspection covers 127 payload files, 59 current UniStation source files,
34 unchanged AxisFlow files, both asInvoker manifests and 14 icon frames per EXE.
Reading the executable as an archive/PE does not execute setup or uninstall.

The alpha.11 installer passed manual testing on 24 November in the recorded
scope. A short smoke check of the new alpha.12 EXE remains pending: installation,
FreeCAD 1.1.4 GUI launch through its shortcut, and installed Line/Wire features.
No full regression, /S coverage, forced cleanup/recovery or all DPI/icon variants
are claimed. [Scenario](../packaging/installer/USER-CHECK.md).

## Earlier results and limits

Earlier revisions operated in FreeCAD 1.1.1 and 1.1.3; recent feature checks
used 1.1.4. A complete alpha.12 run across 1.1.1–1.1.4 is not established.
The alpha.4 allowlisted unit run had 58/67 passing, 5 failures and 4 errors in
legacy Circle/Arc tests. It is a historical result, not a fresh alpha.12 run.
[Historical report](alpha4-unit-result.json). TEST-003/004 and the recorded
Circle lifecycle, Reset, Palette/Locate and key-in limitations remain open.
[Status](status.md).

Further automated checks require explicit approval for a concrete set and
declaration of whether FreeCAD/GUI will run. A completed earlier acceptance
does not authorize a new run.
