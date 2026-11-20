# Current status — 20 November 2026

Alpha.6 updates the installer, FreeCAD detection and startup shortcut; product runtime remains as in alpha.4. [Release notes](release-v0.1.0-alpha.6.md).

Implemented: drawing and supported whole-object Move/Copy, FCStd layers and
modeless manager, assignment, persistent ByLayer attributes, Global Display /
Global Freeze, Lock in supported UniStation operations, Plot, Change Attributes,
256-color Edit Palette with JSON Load/Save, and direct planar XY PDF output.
Five toolbars, English/Russian UI, shared Draft/AxisFlow snaps and live attributes.

Recent targeted checks used FreeCAD 1.1.4. Earlier product functionality was
tested in 1.1.1; alpha.4 has not received a complete 1.1.1 regression. Feature
acceptance, static package inspection and installer execution are separate.
[Testing](testing.md).

## Known limits

| Area | Limit |
| --- | --- |
| Layers | Protection outside UniStation, per-view visibility and external layer libraries are deferred. Lock applies to supported operations, not arbitrary FreeCAD tools. |
| PDF | Supported planar XY geometry only; direct vector output respects Plot/Global Freeze. TechDraw integration is deferred. |
| Drawing / transforms | Rectangle/Freeform and Scale/Rotate/Mirror/Array are disabled. Move/Copy require supported preselected whole objects. Wire arc segments are deferred. |
| Circle lifecycle / AF-002 | Historical native access violation during lifecycle checks remains unresolved; ownership was not established. Finish/cancel Circle before switching documents/workbenches as a precaution, not a proven fix. |
| Reset / key-in | Corrected right-click Reset has no separate complete acceptance; earlier coordinate-entry/focus scenarios remain open. AxisFlow is primary point input. |
| Palette / Locate | Earlier Undo/failure/read-only, JSON validation and compound-click observations remain recorded; publication does not establish their resolution. |
| TEST-003/004 | Legacy GUI assertions/doubles require separate work. Publishing them is not evidence of passing. |
| Installation | Manual installation/launch and the alpha.6 uninstall retest passed in the reported scope. Complete regression and forced failure recovery are not certified. EXE is unsigned; Addon Manager delivery is not provided. |

Next work is local project configuration and search paths, then external layer
libraries. Cells/shared cells, a references manager and saved views are planned.
The project is currently a workbench; a future FreeCAD fork is possible.
