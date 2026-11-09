# Dependencies and compatibility / Зависимости

## Recorded local environment

| Component | Recorded state |
| --- | --- |
| Operating system | Windows; other systems not validated here |
| FreeCAD | 1.1.4, source reference `4fd3bf320d9566a27e60069fc8387448aaa3a094` |
| Python / Qt in the recorded portable runtime | 3.11.14 / 6.8.3 |
| AxisFlow API source reference | `5dda554759d813559d94416286014f0cb6fc780e` |
| Active local AxisFlow binary SHA-256 | `222678c61f86bb576160c8c939e394470abb2242449fc9d924ea44e9f580426e` |
| AxisFlow build environment / intended runtime | FreeCAD 1.1.1 / FreeCAD 1.1.4 |
| Corresponding source snapshot by accepted build manifests | `7daa0ffd776eac559ed7468bec43911ec159adbb` (no independent rebuild) |

The API reference and binary hash identify different kinds of evidence. The
reference commit does not prove which sources produced the binary. The local
binary's appearance and normal operation were accepted by the user in the
reported scope; that is not a general ABI guarantee or a test of a binary
downloaded elsewhere. No AxisFlow binary is tracked in this repository.
A separate local candidate includes the accepted binary, complete source
snapshot and build information; see [distribution](distribution.md).

The packaging audit matched all 29 C++ source/header files, CMake and the QRC
to accepted build evidence. 56 of 57 baseline records matched; the exception
is a non-build archive helper. The public snapshot postdates the build and
establishes source-content equivalence, not a new reproducibility check.
The public v0.2.1 release binary has a different hash. The separate working
AxisFlow checkout has older panel sources; it was not used or edited.

## Public APIs used

Point-based commands use AxisFlow `getPoint`, `endSession`, `setPlane` and
`isActive`. Explicit coordinate input also uses `confirm` and `setBasePoint`;
Circle/Arc read the live frame through `getCompassInfo`. Snapping uses
`getSettings` and `setSetting`, sharing Draft's existing Snapper modes.
UniStation checks required input capabilities before taking ownership.

FreeCAD provides Draft geometry factories, Part/OCC geometry, document
transactions and selection. PySide and pivy/Coin come from the FreeCAD
environment. Installing unrelated Python packages with matching names does
not establish compatibility with that environment.

## Source preparation versus binary delivery

UniStation's Python files do not require compilation. English/Russian `.qm`
catalogs are included with their `.ts` sources. `tools/update-translations.py`
can regenerate catalogs when intentionally invoked with compatible Qt tools;
it is not run during this publication work.

The candidate includes corresponding source/build information and component
notices. A clean installation check by the user remains pending; no binary
was rebuilt. See [distribution](distribution.md) and
[licensing notices](../THIRD_PARTY_NOTICES.md).

## По-русски

Зафиксированная локальная среда — Windows, FreeCAD 1.1.4, Python 3.11.14 и
Qt 6.8.3. Активный AxisFlow собран в среде FreeCAD 1.1.1 и использовался
пользователем с 1.1.4. Его SHA-256 приведён выше; точный соответствующий commit
исходников восстановлен по манифестам принятой сборки как эквивалентный по
содержанию снимок `7daa0ffd776eac559ed7468bec43911ec159adbb`. Независимая
пересборка не выполнялась. Commit анализа API сам по себе не подтверждает
происхождение бинарника. Приёмку локальной сборки нельзя переносить на другой файл.

Для запуска нужен отдельный совместимый AxisFlow с указанными публичными
методами. Бинарник не включён. Python-код UniStation сборки не требует;
переводы TS/QM включены. Подготовка воспроизводимого бинарного комплекта —
отдельный этап. Локальный кандидат подготовлен и ожидает пользовательской
пробы; порядок установки — в [инструкции](../packaging/INSTALL.md).
