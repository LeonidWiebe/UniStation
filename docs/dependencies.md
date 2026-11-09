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
| Exact corresponding source commit of that binary | Not established |

The API reference and binary hash identify different kinds of evidence. The
reference commit does not prove which sources produced the binary. The local
binary's appearance and normal operation were accepted by the user in the
reported scope; that is not a general ABI guarantee or a test of a binary
downloaded elsewhere. No AxisFlow binary is distributed here.

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

A distributable application bundle still needs corresponding AxisFlow sources,
an agreed build procedure, exact dependency notices and a user-verified
installation. See [licensing notices](../THIRD_PARTY_NOTICES.md).

## По-русски

Зафиксированная локальная среда — Windows, FreeCAD 1.1.4, Python 3.11.14 и
Qt 6.8.3. Активный AxisFlow собран в среде FreeCAD 1.1.1 и использовался
пользователем с 1.1.4. Его SHA-256 приведён выше; точный соответствующий commit
исходников пока не установлен. Commit анализа API не подтверждает происхождение
бинарника. Приёмку этой локальной сборки нельзя переносить на другой файл.

Для запуска нужен отдельный совместимый AxisFlow с указанными публичными
методами. Бинарник не включён. Python-код UniStation сборки не требует;
переводы TS/QM включены. Подготовка воспроизводимого бинарного комплекта —
отдельный этап, а ручная установка — в [инструкции](installation.md).
