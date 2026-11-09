# FreeCAD 1.1.1 — experimental test minimum

**Conclusion, 2026-11-09:** FreeCAD 1.1.1 can be admitted as an experimental
minimum for a user installation check. This is a static compatibility finding,
not acceptance of the official Windows binary runtime.

## Evidence

- Official tag 1.1.1 is commit
  `0108fd4b4850cc46e625b60e53cea7a7bbe69f8d`; reference 1.1.4 is
  `4fd3bf320d9566a27e60069fc8387448aaa3a094`.
- 23 reviewed implementation files are byte-identical between those commits:
  package metadata/GUI loader, command resources and actions, selection and view
  Python APIs, GUI document observer, Draft entry points, working plane,
  line/wire/circle factories, Move, snapping, Wire/Circle objects and Part Arc.
- Custom user-path handling and the launcher's user/system config and log
  command-line options are unchanged. The module loader differs only by added
  macro-directory bookkeeping, which this launcher does not use.
- All 29 UniStation Python files parse under Python 3.11 syntax. Product files
  are unchanged. The accepted AxisFlow theme_01 binary was built against
  FreeCAD **1.1.1** source/SDK with Python 3.11.14, MSVC 19.44.

The SDK provenance alone does not prove compatibility with every official or
third-party 1.1.1 binary. No official 1.1.1 runtime was downloaded or launched in
this review. Exact bundled Python/Qt/Coin/fmt versions and .pyd loading remain
to be checked in the user session. API review does not prove all transitive
behavior is equivalent: later Draft color/view-provider and core/Part fixes
exist in 1.1.4. Earlier limitations and scoped acceptances remain in force.

## Candidate and user check

Alpha.2 declares `freecadmin=1.1.1`, `freecadmax=1.1.4`, Python 3.11 minimum.
The range permits testing; 1.1.2/1.1.3 were not separately audited or tested.
1.1.4 remains the previously used reference environment, with its recorded
user acceptances. New clean-profile installation checks are pending.

Use the official Windows x64 py311 archive from the
[1.1.1 release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.1), follow
[INSTALL](../packaging/INSTALL.md), then report [USER-CHECK](../packaging/USER-CHECK.md)
with the actual Python/Qt versions. Extract separate candidate folders for
1.1.1 and 1.1.4; do not share their profiles. No AxisFlow rebuild is needed to
attempt this check. A load failure would require diagnosis, not an assumed fix.

## По-русски

1.1.1 допущена как **экспериментальный минимум для тестирования**. Статических
препятствий в проверенных API не найдено. Совместимость официального runtime
и успешная установка ещё не подтверждены пользователем. В alpha.2 изменены
метаданные и документы; геометрия, ввод, переводы и бинарник AxisFlow прежние.

Primary sources: [1.1.1 GUI loader](https://github.com/FreeCAD/FreeCAD/blob/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Gui/FreeCADGuiInit.py),
[Draft factories](https://github.com/FreeCAD/FreeCAD/tree/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Mod/Draft/draftmake),
[working plane](https://github.com/FreeCAD/FreeCAD/blob/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Mod/Draft/WorkingPlane.py).
