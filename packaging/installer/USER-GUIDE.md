# UniStation — установка через мастер Windows

Установщик UniStation 0.1.0-alpha.3 устанавливает дополнения в существующий
FreeCAD 1.1 для текущего пользователя. Сам FreeCAD не включён. Минимум 1.1.1
проверен пользователем в ранее сообщённом объёме; Windows x64 / Python 3.11.

1. Закройте FreeCAD и запустите файл `UniStation-0.1.0-alpha.3-win64-setup.exe`.
2. Выберите язык. В составе отметьте UniStation, AxisFlow и при необходимости
   документацию/ярлыки. Для первого запуска оставьте оба основных компонента.
3. Выберите **родительский каталог Mod**. По умолчанию:
   `%APPDATA%\FreeCAD\v1-1\Mod`. Внутри мастер создаёт `UniStation` и `AxisFlow`.
   Если у вас другой профиль/portable FreeCAD, выберите его настоящий каталог Mod.
4. Проверьте сводку и нажмите «Установить». Существующие папки выбранных
   компонентов сохраняются в резервную копию перед заменой.
5. Запустите FreeCAD привычным способом и выберите UniStation. Создайте или
   откройте документ. Команды PowerShell и отдельный профиль для этого не нужны.

Если AxisFlow уже установлен, его можно не выбирать. В этом случае мастер
проверяет наличие файлов существующего модуля, но не доказывает его ABI/API
совместимость. Настройки FreeCAD, документы и профиль не переносятся и не
сбрасываются. Мастер не скачивает и не запускает FreeCAD автоматически.

Удаление: «Параметры Windows → Приложения → UniStation», либо пункт удаления
в меню «Пуск». Можно выбрать удаляемые компоненты, например оставить AxisFlow.
Прежняя версия восстанавливается из резервной копии, если она была сохранена.
Папки удаляемых версий также сохраняются в служебном каталоге
`Mod\.UniStation-Installer`, чтобы не потерять добавленные файлы.
Сам каталог Mod и конфигурация FreeCAD не удаляются. Резервные копии можно
удалить вручную после проверки результата. Не перемещайте служебный каталог
пока хотите пользоваться восстановлением/удалением.

Повторный запуск установщика обслуживает текущий каталог установки. Для смены
каталога сначала удалите управляемые компоненты прежней установки. Снятый при
повторной установке флажок пропускает компонент; удаление выполняется отдельно.

UniStation — GPL-3.0-only, AxisFlow — LGPL-2.1-or-later. Исходники AxisFlow и
лицензия всегда устанавливаются вместе с выбранным AxisFlow. Тексты лицензий,
исходники самого установщика и инструкция находятся в служебном каталоге.

Проверка этого нового мастера пользователем ещё ожидается; прежняя успешная
проба UniStation в FreeCAD 1.1.1 не является отдельной приёмкой установщика.

## English

Close FreeCAD and run the setup executable. Choose language, components and the
parent Mod directory (default `%APPDATA%\FreeCAD\v1-1\Mod`). Existing selected
modules are backed up. Start FreeCAD normally and select UniStation. FreeCAD is
external; no launcher command or separate profile is needed. Use Windows Apps
to uninstall selected components and restore their previous versions. Backup
and retired directories are retained in `.UniStation-Installer`; the shared
Mod directory and FreeCAD configuration are never recursively deleted.
