# Сборка установщика

Сборка не устанавливает дополнения и не запускает FreeCAD или сам `.exe`.
Понадобятся Python 3.11+ и portable NSIS **3.12**, без Visual Studio.

1. Получите NSIS 3.12 ZIP с официального хостинга либо проверяемого зеркала:
   https://nsis.sourceforge.io/Download
   https://distfiles.macports.org/nsis/nsis-3.12.zip
2. Для использованного архива: 2 362 938 байт, SHA-256
   `56581f90db321581c5381193d796fffcf2d24b2f8fed2160a6c6a3baa67f2c4f`.
   Эти размер/хэш опубликованы также в MacPorts devel/nsis/Portfile.
3. Скачайте неизменённый полный ZIP релиза alpha.2:
   https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip
4. В корне исходников выполните:

   ```text
   python tools/build-installer.py --makensis C:/tools/nsis-3.12/makensis.exe --payload-archive C:/downloads/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip
   ```

SHA входного ZIP закреплён в config.json. Упаковщик сверяет 45 runtime-файлов
UniStation и бинарник AxisFlow, переносит исходный ZIP AxisFlow/LGPL без изменений,
разбирает Python/XML без импорта продукта, генерирует точный список копирования
и вызывает только компилятор NSIS. Новая версия меняет установочные метаданные,
но не геометрию/ввод/переводы UniStation и не код/бинарник AxisFlow.

Результат — dist/installer-build: EXE, compile.log, BUILD-MANIFEST.json и SHA-256.
Промежуточный stage — только явно перечисленные файлы; посторонние файлы в нём
вызывают отказ сборки. Для новой сборки с другим составом выберите новый
`--output-dir`; автоматически удалять старые деревья упаковщик не будет.
Compiler/EXE timestamp не объявлен побитово воспроизводимым.

Для статической проверки используйте `7z x <setup.exe> -o<отдельный каталог>`:
это чтение архива, не запуск мастера. Сверьте содержимое `$PLUGINSDIR` с
BUILD-MANIFEST.json, PE manifest `asInvoker`, отсутствие рекурсивного удаления
Mod, лицензии и исходники. Установку/удаление проверяет пользователь отдельно.
