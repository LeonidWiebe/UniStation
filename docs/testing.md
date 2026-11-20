# Testing status

This release separates source review, automated execution and manual acceptance.
Compilation and reading an EXE as an archive do not test installation behavior.

Before alpha.4, targeted FreeCAD 1.1.4 runs passed for palette Load/Save (4/4),
Change Attributes before its final button relocation (7/7), the modeless layer
manager/tooltips (6/6), layer Lock (7/7), visibility/freeze (7/7), persistent
ByLayer (8/8), direct PDF (5/5) and its toolbar/dialog (4/4). These are individual
feature runs, not an alpha.4 regression. Final button placement and palette
workflow have manual acceptance in the recorded scope. Lock's separate full
manual acceptance remains pending; later checks cover only their own scope.

Earlier UniStation operation in FreeCAD 1.1.1 was successful. The new feature
set was checked in 1.1.4; a complete alpha.4 run in 1.1.1 is not claimed.
Known Circle lifecycle, Reset, key-in, Palette/Locate and TEST-003/004 limitations
are retained. [Status](status.md).

For alpha.4, an explicitly approved axisflow-core unit run uses the allowlist
in tests/current_scope.json, without FreeCAD or GUI. Its actual result is
recorded in the release notes after completion; no broad discover or deferred
key-in cases are added. Repeated/full runs require separate approval.

The alpha.6 setup and launcher compile without warnings; 123 extracted payload
files match the manifest. Manual installation/FreeCAD launch passed in 1.1.3;
the retest after the alpha.6 uninstall fix succeeded in the reported scope.
This does not certify complete regression, every detection/component branch or
forced failure recovery. No new automated run was made for publication.
Additional manual scenarios remain documented separately:
[installer check](../packaging/installer/USER-CHECK.md).

## Alpha.4 unit run — 20 November 2026

The approved axisflow-core run completed without FreeCAD or GUI: **67 tests,
58 passed, 5 failures, 4 errors, 0 skipped**. The nine non-passing cases are
Circle/Arc tests, consistent with the recorded TEST-004 live-plane test-double
limitation. They are not marked fixed and the release is not a passing full
regression. [Machine-readable report](alpha4-unit-result.json).
The first sandbox attempt stopped after an error/hang without a completed
report; the completed run used the same allowlist outside that sandbox.
