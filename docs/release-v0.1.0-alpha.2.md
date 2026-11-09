# UniStation v0.1.0-alpha.2 — первый предварительный релиз

UniStation — экспериментальный Workbench для FreeCAD с основным вводом точек
через AxisFlow. Это **prerelease**, предназначенный для пробной работы.

## Совместимость и результат проверки

Пользователь сообщил об успешном тестировании в **FreeCAD 1.1.1**.
1.1.1 — минимальная версия, проверенная пользователем в сообщённом объёме.
Прежняя опорная среда — FreeCAD 1.1.4. Метаданные допускают 1.1.1–1.1.4,
но отдельная проверка 1.1.2/1.1.3 и любых сочетаний Python/Qt/ABI не заявляется.
Точные ОС/Python/Qt и отдельные сценарии последней пробы не перечислены.
Полный бинарный пакет предназначен для **Windows x86_64 / Python 3.11**;
работа этого бинарника в других ОС не подтверждена. FreeCAD в ZIP не включён.

## Что скачать

- [Полный пакет Windows](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip)
  — рекомендуемый вариант первой установки: UniStation, принятый AxisFlow
  theme_01, его исходники/LGPL и запуск с отдельным профилем.
- [Только Workbench](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/UniStation-0.1.0-alpha.2-workbench.zip)
  — для отдельной ручной установки UniStation; нужен совместимый AxisFlow.
- [Полные исходники AxisFlow](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/AxisFlow-source-7daa0ffd776eac559ed7468bec43911ec159adbb.zip)
  — снимок 7daa0ff, также вложен в полный пакет.
- [SHA256SUMS.txt](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/SHA256SUMS.txt)
  — SHA-256 трёх ZIP.

## Установка

1. Отдельно скачайте официальный Windows x64 py311 portable
   [FreeCAD 1.1.1](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.1).
2. Распакуйте полный пакет в отдельную папку. Закройте FreeCAD самостоятельно.
3. Выполните в PowerShell из распакованной папки, указав ваш путь:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Candidate.ps1 -FreeCADExe "C:\FreeCAD-1.1.1\bin\FreeCAD.exe"
   ```

Launcher использует отдельную конфигурацию; существующие дополнения и обычный
профиль не заменяются. Для сравнения 1.1.1/1.1.4 нужны разные папки распаковки.
Инструкции INSTALL.md и USER-CHECK.md находятся внутри ZIP; документ создайте
или откройте сами. Готовой установки через Addon Manager пока нет.

## Возможности и ограничения

Line, Wire, Circle, Arc; консервативные Move/Copy с предварительным выбором;
палитра, активные цвет/стиль/толщина и их смена во время рисования; привязки,
отдельное окно координат, русский/английский интерфейс.

Слой, Rectangle, Freeform, Scale, Rotate, Mirror и Array остаются отключёнными
заготовками. Полная регрессия не заявляется. Ранее зарегистрированное native
наблюдение Circle при смене документа/верстака (AF-002) не объявлено исправленным:
перед переключением завершайте команду; это не доказанный обход.
RESET-001 и старые тестовые контракты TEST-003/004 сохраняют свои статусы.
Полный перечень: [status](https://github.com/LeonidWiebe/UniStation/blob/v0.1.0-alpha.2/docs/status.md).

## Происхождение и лицензии

UniStation — **GPL-3.0-only**. AxisFlow — **LGPL-2.1-or-later**; он остаётся
отдельно заменяемым модулем. Полные тексты и исходники включены. Пакет содержит
theme_01, отличающийся от бинарника публичного релиза AxisFlow v0.2.1.
Связь исходного снимка с принятой сборкой восстановлена по манифестам;
независимая пересборка и побитовая воспроизводимость бинарника не проверялись.
Подробности — Mod/AxisFlow/SOURCE-INFO.md внутри полного ZIP.

Архивы собраны из commit `25fca51d6c116290ebd004eb07744e5fc3b02073` и после
пользовательской пробы не менялись. Слова pending/candidate внутри них отражают
момент сборки до обратной связи; сведения этого релиза дополняют тот снимок.
Тег содержит последующие изменения публичной документации, без изменений
45 runtime-файлов UniStation и бинарника AxisFlow. Для точного воспроизведения
исходного ZIP используйте указанный build commit, а не обновлённую документацию.
Codex не запускал FreeCAD/GUI/автотесты, не имитировал ввод и не собирал AxisFlow.

## English

First experimental prerelease. The user reported successful UniStation testing
with **FreeCAD 1.1.1**, accepted in the reported scope; exact Python/Qt versions
and individual scenarios were not supplied. 1.1.4 remains the earlier reference.
The declared 1.1.1–1.1.4 range is not certification of every build/version.
Download the full Windows x64/Python 3.11 ZIP for UniStation plus the accepted
AxisFlow theme_01, corresponding source archive, LGPL notice and separate-profile
launcher. FreeCAD is external. The workbench-only ZIP needs AxisFlow separately.
Artifacts are unchanged from build commit 25fca51; their pre-check pending text
is superseded by this scoped user result. GPL-3.0-only / LGPL-2.1-or-later.
Disabled placeholders and known limitations remain; this is not a stable release.
