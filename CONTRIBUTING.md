# Contributing

UniStation is a prototype. Keep changes small and describe their observable
effect, affected commands and known limitations. Discuss a larger behavior
change before implementing it. Code contributions are accepted under the
repository's [GPL-3.0-only license](LICENSE); only submit material you have
the right to contribute, and identify any third-party source and its license.

## Reporting an issue

Include the repository commit, operating system, FreeCAD version, AxisFlow
version or binary identity when available, concise reproduction steps, expected
behavior and actual behavior. Attach only relevant, redacted log excerpts and
a small non-confidential example if needed. Avoid complete profiles and private
drawings. [Known limitations](docs/status.md) include unresolved lifecycle,
selection and palette observations.

## Proposing a change

Use a short branch and a pull request with a concrete description. Preserve
stable command IDs, toolbar identities and persisted `Ustn` metadata. AxisFlow
is the primary input system: new or changed commands must respect its current
compass plane/orientation through its public API while the command runs. Keep
accepted world points according to the command's semantics. Changes to AxisFlow
itself belong in its own project and are not implied by a UniStation change.

Explain how the change was checked and what was not run. See
[testing status](docs/testing.md). There is no enabled automatic test workflow
in this snapshot. Do not present old test counts as results for a new commit.

AI-assisted contributions need the same human review as other changes. Identify
material AI assistance and check API use, provenance and licensing. Do not add
an assistant's internal chat, credentials or local user configuration.

## Участие по-русски

В сообщении об ошибке укажите commit, ОС, версии FreeCAD/AxisFlow, короткие шаги,
ожидаемый и фактический результат. Из журналов удалите личные данные; полный
профиль и частные чертежи не нужны.

Предлагайте небольшие изменения отдельными PR. Описывайте поведение и реальную
проверку. Сохраняйте command ID, имена панелей и метаданные `Ustn`. Основной
ввод — AxisFlow с актуальным состоянием компаса во время команды. Для
организации объектов используйте термин «слой». Вклад — по GPL-3.0-only;
укажите сторонние источники и существенное использование ИИ.
