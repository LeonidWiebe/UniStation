# UniStation v0.1.0-alpha.3 — Windows Installer

Новый рекомендуемый способ установки — **мастер Windows** вместо прежнего
ZIP/PowerShell-комплекта. Это предварительный релиз для Windows x64.

## Скачать

**[Скачать установщик UniStation](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/UniStation-0.1.0-alpha.3-win64-setup.exe)** — около 2,9 МБ.

Дополнительно:

- [SHA256SUMS.txt](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/SHA256SUMS.txt).
- [Исходники установщика](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/UniStation-0.1.0-alpha.3-installer-source.zip).

## Установка

1. Закройте FreeCAD и запустите `.exe`.
2. Выберите язык и компоненты: **UniStation**, **AxisFlow**, документацию и
   ссылки меню «Пуск». Для первой установки оставьте оба основных компонента.
3. Выберите родительский каталог **Mod**. По умолчанию:

   ```text
   %APPDATA%\FreeCAD\v1-1\Mod\
   ```

   Внутри мастер создаёт `UniStation` и `AxisFlow`. При другом/portable профиле
   укажите его настоящий каталог Mod.
4. Завершите установку. Запустите FreeCAD привычным способом и выберите
   UniStation. Документ создайте или откройте самостоятельно.

FreeCAD устанавливается отдельно. Команда PowerShell и отдельный профиль
кандидата для этой установки не требуются. Мастер работает для текущего
пользователя, без запроса административных прав, не меняет конфигурацию FreeCAD.
Установка через FreeCAD Addon Manager пока не подготовлена.

Если совместимый AxisFlow уже установлен, его можно не выбирать. Мастер
проверяет наличие файлов модуля, а не гарантирует ABI/API произвольной сборки.

## Прежние версии и удаление

Выбранные существующие папки сохраняются в `Mod/.UniStation-Installer/transactions`.
Удаление доступно через список приложений Windows, с выбором компонентов.
При наличии резервной копии прежние папки восстанавливаются. Убранные версии
и добавленные файлы остаются в служебном каталоге. Общий Mod рекурсивно не
удаляется. Подробности — в [инструкции](https://github.com/LeonidWiebe/UniStation/blob/main/packaging/installer/USER-GUIDE.md).

## Проверки и совместимость

**Проверка установки/удаления выполнением ещё не завершена.**
Выполнены сборка NSIS 3.12 без предупреждений, извлечение EXE как архива и
сверка 94 вложенных файлов, PE manifest и контрольных сумм. Исполнение
установки, удаления и аварийного восстановления этим не подтверждается.
Исполняемый файл не имеет подписи Authenticode.

Проверена работа UniStation в FreeCAD **1.1.1**; прежняя опорная среда — 1.1.4. Этот результат не является
отдельной приёмкой нового мастера. Бинарный AxisFlow рассчитан на Windows x64 /
Python 3.11 и совместимые библиотеки FreeCAD; весь диапазон/ABI не сертифицирован.
[Короткая проверка мастера](https://github.com/LeonidWiebe/UniStation/blob/main/packaging/installer/USER-CHECK.md).

45 runtime-файлов UniStation и поставка принятого AxisFlow theme_01 не менялись.
Сохранены отключённые заготовки и известные ограничения, включая AF-002 и
неподтверждённые отдельно RESET-001/TEST-003/004. [Состояние продукта](https://github.com/LeonidWiebe/UniStation/blob/main/docs/status.md).

## Лицензии и исходники

UniStation — GPL-3.0-only; AxisFlow — LGPL-2.1-or-later. Исходный архив AxisFlow
и LGPL всегда устанавливаются вместе с выбранным AxisFlow; модуль остаётся
отдельно заменяемым. Связь снимка исходников с принятой сборкой восстановлена
по манифестам, независимой пересборки не было. Лицензии, NSIS COPYING, исходники
мастера и текстовая инструкция также включены в установщик.

EXE и source ZIP сохранены от сборки `installer/0.1.0-alpha.3`, commit
`290f4d5254bad762473be7919b5da684106a09be`. Последующие изменения под тегом —
документы публикации. [Предыдущий alpha.2](https://github.com/LeonidWiebe/UniStation/releases/tag/v0.1.0-alpha.2)
сохранён для истории и воспроизведения сборки; для новой установки используйте `.exe` выше.

## English

The Windows setup wizard replaces the earlier ZIP/PowerShell workflow as the
recommended download. Choose components and the parent Mod directory; default
`%APPDATA%\FreeCAD\v1-1\Mod`. Start FreeCAD normally after setup. FreeCAD is
external. Per-user installation, retained backups and component uninstall/restore.
**Installer/uninstaller GUI behavior is not yet user-validated**; only compilation,
payload/hash and PE inspection were performed. The executable is unsigned.
The completed FreeCAD 1.1.1 check concerns the unchanged product,
not this new wizard. GPL-3.0-only / LGPL-2.1-or-later; sources included.
