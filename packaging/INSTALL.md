# Установка UniStation

Для новой обычной установки подготовлен Windows-мастер
`UniStation-0.1.0-alpha.3-win64-setup.exe`: выбор UniStation/AxisFlow,
документации, ссылок в меню «Пуск» и родительского каталога Mod.
По умолчанию `%APPDATA%\FreeCAD\v1-1\Mod`. FreeCAD устанавливается отдельно.
[Инструкция нового мастера](installer/USER-GUIDE.md).
Новый мастер ожидает пользовательской пробы; опубликованный alpha.2 сохранён.

Ниже — прежняя инструкция ZIP alpha.2 для отдельного профиля. Она относится
к старому способу доставки, а не к работе нового `.exe`.

## Архивный кандидат 0.1.0-alpha.2

Это кандидат установочного пакета для пользовательской проверки, не
подтверждённый стабильный релиз. Функционал соответствует первому
опубликованному снимку; новые команды не добавлены.

## Целевая среда

Минимум для новой пользовательской пробы — **FreeCAD 1.1.1, Windows x86_64,
официальная portable-сборка py311**.
[Скачать 1.1.1](https://github.com/FreeCAD/FreeCAD/releases/download/1.1.1/FreeCAD_1.1.1-Windows-x86_64-py311.7z).
SHA-256 из официального списка файлов релиза:
`aef51acb6725d5667bbae73494d04794a1e1725e17c6589650b044c15808144f`.
В этом аудите сам архив FreeCAD 1.1.1 не скачивался. Совместимость API проверена
статически; загрузка бинарного AxisFlow в этой официальной сборке ещё не проверена.

Прежняя опорная среда — **1.1.4 / Python 3.11.14 / Qt 6.8.3**.
[Скачать 1.1.4](https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311.7z).
SHA-256 архива:
`4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d`.
FreeCAD в пакет не включён. Номер 1.1.4 без совпадающей ABI не гарантирует
работу приложенного AxisFlow. То же относится к номеру 1.1.1: важна ABI.
Диапазон метаданных 1.1.1–1.1.4 разрешает тестирование, а не подтверждает все
промежуточные версии. Другие сборки и ОС этим кандидатом не проверены.

## Вариант A: полный кандидат для отдельного профиля

1. Распакуйте `UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip`
   в отдельную папку, например `C:\UniStation-Candidate`. Не размещайте поверх
   рабочего FreeCAD или существующей версии дополнений. Для сравнения версий
   распакуйте пакет в две разные папки: одна для 1.1.1, другая для 1.1.4.
   Профили и данные этих проб не смешивайте.
2. Закройте все экземпляры FreeCAD сами. Launcher не закрывает чужие процессы.
3. Откройте PowerShell в распакованной папке и выполните, указав ваш FreeCAD:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Candidate.ps1 -FreeCADExe "C:\FreeCAD-1.1.1\bin\FreeCAD.exe"
   ```

4. Скрипт создаёт только отдельный профиль `candidate-profile` рядом с собой,
   передаёт его конфигурацию FreeCAD и подключает папки `Mod/AxisFlow` и
   `Mod/UniStation`. Каталогом данных служит распакованная папка кандидата:
   так AxisFlow находит свои ресурсы и начальные горячие клавиши. Настройки
   обычного профиля не копируются. Папка без
   маркера кандидата не используется, если уже содержит файлы. Для нового
   отдельного профиля можно передать `-ProfileDirectory`.
5. Откроется видимое окно; выбраны Draft и UniStation. Документ создайте сами.
   Выполните [короткую проверку](USER-CHECK.md).

В полном кандидате есть рабочий AxisFlow theme_01 и его исходный архив.
Он отличается от бинарника публичного релиза AxisFlow v0.2.1. Сборка binary:
FreeCAD 1.1.1; пользовательская работа ранее подтверждена в 1.1.4 в сообщённом
объёме. Новая чистая установка ещё ожидает проверки.

## Вариант B: только Workbench

Архив `UniStation-0.1.0-alpha.2-workbench.zip` содержит верхнюю папку
`UniStation` с **InitGui.py непосредственно внутри неё**. При закрытом FreeCAD
скопируйте её в `Mod` нужного профиля. Путь профиля заранее можно прочитать
через `App.getUserAppDataDir()` в Python-консоли FreeCAD.

```text
<профиль>/Mod/UniStation/InitGui.py
<профиль>/Mod/UniStation/unistation/...
<профиль>/Mod/UniStation/package.xml
<профиль>/Mod/AxisFlow/AxisFlow.pyd  # отдельный совместимый AxisFlow
```

Существующие папки сначала сохраните; версии файлов не смешивайте.
Workbench-only ZIP не включает AxisFlow и самостоятельно не обеспечивает ввод.
При установке из checkout репозитория структура другая: корневой package.xml
указывает внутренний каталог UniStation. Метаданные установочного ZIP
адаптированы к плоской структуре; Python/SVG/TS/QM сохранены побайтно.

## Возврат и лицензии

Закройте окно кандидата. Чтобы вернуться к обычной работе, используйте прежний
способ запуска FreeCAD/UniStation. Кандидат не заменяет прежние дополнения и
профиль. Созданные чертежи сохраняйте в выбранном вами месте вне профиля.

UniStation — GPL-3.0-only; AxisFlow — LGPL-2.1-or-later. Библиотечный исходный
архив находится в `Mod/AxisFlow/sources/`; сведения о сборке —
`Mod/AxisFlow/SOURCE-INFO.md`. Бинарник не пересобирался; соответствие исходного
снимка восстановлено по принятым манифестам, не независимой пересборкой.
В launcher нет блокировки по хэшу AxisFlow: интерфейсно совместимая замена
модуля возможна при закрытом FreeCAD. Build-манифест нужен для идентификации
поставленного кандидата, а не для запрета изменённого модуля.

## English

This is an installation candidate for Windows x64 with FreeCAD 1.1.1 as an
experimental test minimum and 1.1.4 as the recorded reference runtime. Static
API review passed; the official 1.1.1 binary ABI and installation remain untested.
The declared 1.1.1–1.1.4 range is not a claim that every version was tested.
Extract the full
candidate into a separate directory, close FreeCAD, then run Start-Candidate.ps1
with `-FreeCADExe` pointing at the matching FreeCAD executable. It uses a
separate marked profile and never replaces an existing addon installation.
The workbench-only ZIP requires AxisFlow separately. Runtime files are unchanged.
The complete candidate includes AxisFlow theme_01, the corresponding source
snapshot and build information. It is not the public v0.2.1 release binary.
