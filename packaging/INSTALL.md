# Установка UniStation

Основной способ — **[Windows-инсталлятор alpha.3](https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.3/UniStation-0.1.0-alpha.3-win64-setup.exe)**.
Выберите UniStation/AxisFlow, язык, документацию/ссылки и родительский Mod.
По умолчанию `%APPDATA%\FreeCAD\v1-1\Mod`. FreeCAD устанавливается отдельно;
после мастера запускается привычным способом, без команды PowerShell.

[Подробная инструкция](installer/USER-GUIDE.md) · [Ручная проверка](installer/USER-CHECK.md) ·
[Релиз и контрольные суммы](https://github.com/LeonidWiebe/UniStation/releases/tag/v0.1.0-alpha.3).

Работа продукта в FreeCAD 1.1.1 проверена. Мастер установки/удаления и аварийный
откат ещё не проверены выполнением; это предварительный релиз, EXE не подписан.
При custom/portable-профиле выбирайте его фактический Mod. Версия/ABI FreeCAD
автоматически не определяется. Сохранённый совместимый AxisFlow можно не заменять.

Предыдущий [alpha.2](https://github.com/LeonidWiebe/UniStation/releases/tag/v0.1.0-alpha.2)
содержит ZIP/PowerShell-поставку с отдельным профилем. Она сохранена как история
и закреплённый вход сборки мастера; её способ запуска не требуется для alpha.3.
