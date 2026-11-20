# Установка UniStation

Основной способ — [Windows-инсталлятор alpha.6](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.6/UniStation-0.1.0-alpha.6-win64-setup.exe).
Закройте FreeCAD, проверьте найденный EXE и версию, выберите компоненты и
родительский Mod. По умолчанию `%APPDATA%\FreeCAD\v1-1\Mod`.
Ярлык **«UniStation - FreeCAD»** открывает выбранный FreeCAD с активным UniStation.
Используйте одну учётную запись Windows для установки и работы.

[Руководство RU/EN](installer/USER-GUIDE.md) · [Ручная проверка](installer/USER-CHECK.md) ·
[Описание выпуска](../docs/release-v0.1.0-alpha.6.md).

Ручные установка и запуск FreeCAD прошли успешно; повтор удаления после
исправления alpha.6 успешен в объёме этой пробы. Аварийный откат и полная
регрессия не подтверждены. EXE не подписан. Для обновления alpha.5 выбирайте
тот же Mod. FreeCAD устанавливается отдельно; диапазон — 1.1.1–1.1.4,
Windows x64 / Python 3.11. Это не гарантия произвольного ABI.

Прежний alpha.2 сохранён в истории и служит закреплённым входом AxisFlow
при сборке. Все его бинарники, исходники и лицензии сохранены.
