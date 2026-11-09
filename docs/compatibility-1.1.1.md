# FreeCAD 1.1.1 compatibility

**Tested with FreeCAD 1.1.1.** It is the checked minimum; 1.1.4 remains the earlier
reference. This covers the completed product check, without claiming a complete
regression, every ABI combination, or the new installer's setup/uninstall flow.
Version 1.1.2/1.1.3 were not separately checked in this minimum-version review.

## Static evidence

Tag 1.1.1: `0108fd4b4850cc46e625b60e53cea7a7bbe69f8d`.
Reference 1.1.4: `4fd3bf320d9566a27e60069fc8387448aaa3a094`.

23 reviewed implementation files are identical: metadata/GUI loading,
commands/actions, selection/view APIs, GUI observer, Draft entry points,
working plane, Line/Wire/Circle factories, Move, snapping, Wire/Circle objects
and Part Arc. Custom user-path handling and the old launcher's config/log
options match; the module-loader difference is macro-directory bookkeeping.
All 29 product Python files parse under Python 3.11 syntax.

The included AxisFlow binary was built on SDK 1.1.1, Python 3.11.14, MSVC 19.44.
That provenance alone does not certify every official or third-party runtime.
Later Draft color/view-provider and core/Part fixes exist in 1.1.4; API checks
do not establish complete transitive behavior equivalence.

## Current delivery

The manifest declares freecadmin 1.1.1, freecadmax 1.1.4 and Python minimum 3.11.
Use the [alpha.3 Windows installer](release-v0.1.0-alpha.3.md) with the correct
FreeCAD/profile, choosing the parent Mod directory. The earlier alpha.2
separate-profile package remains a build/history artifact. The installer itself
still needs runtime validation; see its [check](../packaging/installer/USER-CHECK.md).

## По-русски

Работа UniStation в FreeCAD 1.1.1 проверена. Полная регрессия и весь диапазон
версий/ABI не подтверждены. Установка, удаление и аварийное восстановление
через новый мастер alpha.3 ещё не проверены выполнением. Код продукта и
бинарник AxisFlow при смене способа поставки сохранены.

Primary references: [GUI loader](https://github.com/FreeCAD/FreeCAD/blob/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Gui/FreeCADGuiInit.py),
[Draft factories](https://github.com/FreeCAD/FreeCAD/tree/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Mod/Draft/draftmake),
[working plane](https://github.com/FreeCAD/FreeCAD/blob/0108fd4b4850cc46e625b60e53cea7a7bbe69f8d/src/Mod/Draft/WorkingPlane.py).
