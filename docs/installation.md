# Manual installation / Ручная установка

[English overview](../README.md) · [Русское описание](../README.ru.md)

**Packaging branch update, 2026-11-09:** alpha.2 admits Windows/FreeCAD 1.1.1
as the experimental test minimum, with 1.1.4 as reference. See
[compatibility](compatibility-1.1.1.md). For that candidate use
[INSTALL](../packaging/INSTALL.md) and [USER-CHECK](../packaging/USER-CHECK.md).
The conventional source-only procedure below remains available; it supplies
no AxisFlow binary. Addon Manager installation has not been verified.

## English

This procedure describes the conventional FreeCAD user-module layout. It has
been reviewed against FreeCAD 1.1.4's module-loading source, but a clean-machine
installation of this published snapshot has not yet been user-verified.

1. Install FreeCAD and a compatible AxisFlow separately. Read
   [dependencies](dependencies.md) first: this repository supplies neither the
   tested AxisFlow binary nor a reproducible build of it. If you cannot obtain
   a compatible module, stop here; the source snapshot alone is insufficient
   to run UniStation.
2. In FreeCAD's Python console, read `App.getUserAppDataDir()` to find the
   actual user data directory. Close FreeCAD before adding module files.
   Existing installations and profiles should be preserved.
3. Copy the **inner `UniStation` directory** from this repository into the
   user data directory's `Mod` directory. The resulting layout is:

   ```text
   <FreeCAD user data>/
     Mod/
       UniStation/
         InitGui.py
         unistation/
           gui.py
           icons/
           translations/
       AxisFlow/
         ... separately installed compatible module ...
   ```

   Do not copy the entire repository as `Mod/UniStation`: that adds an extra
   directory level above `InitGui.py`. If the destination exists, preserve it
   and resolve which version to use before replacing files.
4. Restart FreeCAD. Select Draft, then UniStation. Create or open a document;
   activating the workbench does not start drawing automatically.
5. Follow [usage](usage.md). Read [limitations](status.md), especially the
   unresolved Circle lifecycle observation, before switching document/workbench
   during an active command.

Other operating systems, FreeCAD versions and AxisFlow binaries have not been
validated by this source-publication work. Addon Manager installation is not
advertised. The development computer's portable launcher is intentionally not
included because it depends on a local runtime and profile.

FreeCAD's pinned source references:
[module paths](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/App/FreeCADInit.py),
[InitGui loading](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Gui/FreeCADGuiInit.py).

## По-русски

Это порядок ручного размещения модуля FreeCAD, сверенный с исходниками 1.1.4.
Установка опубликованного снимка на чистом компьютере ещё не проверена
пользователем.

1. Отдельно установите FreeCAD и совместимый AxisFlow. Прочитайте
   [зависимости](dependencies.md). Бинарника AxisFlow и его воспроизводимой
   сборки в репозитории нет. Без совместимого AxisFlow работа UniStation
   не обеспечена.
2. Узнайте действительный каталог пользователя через
   `App.getUserAppDataDir()` в Python-консоли FreeCAD. Затем закройте FreeCAD.
3. Скопируйте внутренний каталог `UniStation` из репозитория в `Mod` этого
   каталога пользователя. `InitGui.py` должен оказаться непосредственно в
   `Mod/UniStation`, как на схеме выше. Существующую версию сначала сохраните;
   не смешивайте файлы разных редакций.
4. Перезапустите FreeCAD, выберите Draft, затем UniStation. Создайте или
   откройте документ и используйте [руководство](usage.md).

Локальный portable-launcher разработчика не включён: он требует локального
рабочего окружения. Готового установщика и подтверждения других ОС/версий
FreeCAD в этой публикации нет.
