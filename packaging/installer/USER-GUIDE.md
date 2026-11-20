# UniStation — установка через мастер Windows

Установщик UniStation 0.1.0-alpha.6 устанавливает дополнения в существующий
FreeCAD 1.1 для текущего пользователя. Сам FreeCAD не включён. Допустимый диапазон
версий — 1.1.1–1.1.4, Windows x64 / Python 3.11. Проверка номера версии и файлов
не является гарантией полной совместимости. Для alpha.4 подтверждён нормальный
запуск верстака в FreeCAD 1.1.3 под той же учётной записью Windows.

1. Закройте FreeCAD и запустите файл `UniStation-0.1.0-alpha.6-win64-setup.exe`
   под учётной записью Windows, в которой будете работать.
2. Выберите язык и проверьте найденный FreeCAD. При необходимости нажмите «Обзор»
   и выберите `FreeCAD.exe`. Если подходящий FreeCAD не найден, мастер спросит,
   указать ли его вручную; отказ завершает мастер. Ссылка на страницу загрузки
   открывается только по нажатию. FreeCAD автоматически не скачивается.
3. В составе отметьте UniStation, AxisFlow и при необходимости
   документацию/ярлыки. Для первого запуска оставьте оба основных компонента.
4. Выберите **родительский каталог Mod**. По умолчанию:
   `%APPDATA%\FreeCAD\v1-1\Mod`. Внутри мастер создаёт `UniStation` и `AxisFlow`.
   Если у вас другой профиль/portable FreeCAD, выберите его настоящий каталог Mod.
   Последняя папка пути должна называться `Mod`.
5. Проверьте FreeCAD, его версию, пользователя, путь и компоненты в сводке
   и нажмите «Установить». Существующие папки выбранных
   компонентов сохраняются в резервную копию перед заменой.
6. Запустите **«UniStation - FreeCAD»** с рабочего стола или из меню «Пуск → UniStation».
   Ярлыки создаются при выборе компонента ярлыков и установленном UniStation.
   Выбранный FreeCAD откроется с активным верстаком UniStation. Создайте или
   откройте документ. При обычном запуске FreeCAD верстак можно выбрать вручную.

Мастер ищет сохранённый путь предыдущей установки, App Paths и записи удаления
FreeCAD в HKCU/HKLM (32/64-bit), затем каталоги `Program Files\FreeCAD*`.
Если найдено несколько версий, можно выбрать нужную вручную. Проверка вызывает
только `FreeCADCmd.exe --version`, без загрузки верстаков и главного окна,
а также проверяет 64-разрядность EXE и наличие `python311.dll`.
Неподдерживаемая или неопределённая версия блокирует установку.

Ярлык запускает небольшой штатный запускатель из `.UniStation-Installer`.
Он выбирает сохранённый EXE и каталог данных, соответствующий выбранному Mod,
только для дочернего процесса; постоянные переменные среды и `user.cfg` мастер
не меняет. При обычной работе FreeCAD сам сохраняет пользовательские настройки.
Запускатель не создаёт документ и не запускает команд черчения.
Под другой учётной записью он предложит установить UniStation для неё.
Не переносите ярлык между пользователями. Существующие одноимённые ярлыки,
не созданные мастером, сохраняются с предупреждением.

Если AxisFlow уже установлен, его можно не выбирать. В этом случае мастер
проверяет наличие файлов существующего модуля, но не доказывает его ABI/API
совместимость. Настройки FreeCAD, документы и профиль не переносятся и не
сбрасываются. Мастер не открывает главное окно FreeCAD; для проверки номера
версии запускается только консольная команда `--version`.

Удаление: «Параметры Windows → Приложения → UniStation», либо пункт удаления
в меню «Пуск». Можно выбрать удаляемые компоненты, например оставить AxisFlow.
Прежняя версия восстанавливается из резервной копии, если она была сохранена.
Папки удаляемых версий также сохраняются в служебном каталоге
`Mod\.UniStation-Installer`, чтобы не потерять добавленные файлы.
Сам каталог Mod и конфигурация FreeCAD не удаляются. Резервные копии можно
удалить вручную после проверки результата. Не перемещайте служебный каталог
пока хотите пользоваться восстановлением/удалением.
При удалении UniStation его ярлыки удаляются, в том числе если AxisFlow оставлен.
Служебные файлы и резервные копии сохраняются; запускатель проверяет, что
UniStation ещё установлен, прежде чем открывать FreeCAD.

Alpha.6 исправляет ошибку начала удаления alpha.5: деинсталлятор искал
служебные файлы рядом со своей временной копией. Если alpha.5 уже установлен,
закройте FreeCAD и установите alpha.6 поверх него **в тот же Mod**, затем
повторите удаление через список приложений. Удалять или исправлять state.ini
вручную не требуется. Существующие компоненты сохранятся как резервные версии.

Повторный запуск установщика обслуживает текущий каталог установки. Для смены
каталога сначала удалите управляемые компоненты прежней установки. Снятый при
повторной установке флажок пропускает компонент; удаление выполняется отдельно.

UniStation — GPL-3.0-only, AxisFlow — LGPL-2.1-or-later. Исходники AxisFlow и
лицензия всегда устанавливаются вместе с выбранным AxisFlow. Тексты лицензий,
исходники самого установщика и инструкция находятся в служебном каталоге.

Установка alpha.5 и запуск FreeCAD проверены вручную. При удалении alpha.5
обнаружена ошибка; исправление alpha.6 проверено по коду и составу сборки,
повтор удаления с alpha.6 прошёл успешно в объёме ручной пробы. Полная регрессия и аварийный откат не заявлены.

## English

Close FreeCAD and run setup using your working Windows account. Confirm the
detected FreeCAD or browse to FreeCAD.exe. Setup asks for a manual path when no
suitable installation is found; declining exits setup. It checks FreeCAD
1.1.1–1.1.4, x64 executables and python311.dll using FreeCADCmd.exe --version,
without opening the FreeCAD GUI. An unknown or unsupported version blocks setup.
Choose components and a directory named Mod (default `%APPDATA%\FreeCAD\v1-1\Mod`).
Existing selected modules are backed up. With shortcuts selected, use
**UniStation - FreeCAD** on the desktop or Start menu: it starts the selected
FreeCAD with UniStation active, using this installation's data directory and the
current account's preferences. It does not create a document or start drawing.
Use the same Windows account; other accounts need their own installation.
FreeCAD remains external and is not downloaded automatically. Alpha.5 installation
and FreeCAD launch passed a manual check; its uninstaller failed during startup.
Alpha.6 fixes the original-directory lookup in the uninstaller. Install alpha.6
over alpha.5 into the same Mod directory before trying uninstall again; do not
edit state.ini manually. The uninstall retest succeeded in the reported scope; forced failure recovery is not certified. Use Windows Apps
to uninstall selected components and restore their previous versions. Backup
and retired directories are retained in `.UniStation-Installer`; the shared
Mod directory and FreeCAD configuration are never recursively deleted.
