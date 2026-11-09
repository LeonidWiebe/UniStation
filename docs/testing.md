# Testing status / Состояние проверок

The publication preparation performs only static source/resource checks:
file hashes, Python AST parsing, SVG/TS XML structure, links, selected-file
inventory and the exact Git diff. It does not import the workbench, launch
FreeCAD, run unit/smoke/Qt tests, simulate user input, regenerate QM catalogs
or write a FreeCAD profile.

## Preserved sources

`tests/` contains the Python test/helper sources, five FreeCAD macros and
`current_scope.json` copied from development. Supporting `tools/acceptance.py`,
`tools/run-current-unit.py` and `tools/update-translations.py` are retained.
The original test catalog is preserved; it is not an assertion of present
passing results. The local Windows process runners and `test_runner.ps1`
are excluded because they require the development runtime/profile layout.
Historical JSON results, screenshots and FCStd fixtures are also excluded.

## Known stale contracts

- TEST-003: `qt_input.FCMacro` asserts the existence of instruction widgets that
  were intentionally removed from the task panel.
- TEST-004: old Circle/Arc doubles do not implement the current
  `getCompassInfo` / `set_circle_plane` contract.
- Earlier coordinate key-in tests remain preserved but were deferred from
  the last selected automation scope.

The existing runner can execute tests; preserving its source does not enable
automation or authorize a run. Do not use broad discovery as evidence that the
snapshot is validated. Adapt stale contracts and agree a suitable runtime and
scope before any future automation. No GitHub Actions workflow is included.

Historical user checks and their limits are described in [status](status.md).
They are distinct from a regression run of the eventual public commit and
from a clean-machine installation check.

## По-русски

При подготовке публикации выполняется статическая сверка файлов, AST, XML,
ссылок и diff. Код продукта не импортируется; FreeCAD, GUI, unit/smoke/Qt и
имитационные пробы не запускаются. TS/QM не пересобираются, профиль не меняется.

Сохранены исходники Python-тестов, помощники, пять макросов FreeCAD, каталог
сценариев и три необходимых Python-инструмента. Локальные Windows runner,
зависящие от рабочего runtime/профиля, и исторические результаты/модели не
включены. Все исходники остаются также в рабочем проекте.

TEST-003/004 требуют адаптации при возврате к автоматизации. Наличие тестов
не означает успешный прогон или включение CI. Пользовательские результаты
относятся к объёму записанных приёмок, а не к полной регрессии этого commit.
