; UniStation per-user installer. Builds only: no AxisFlow compilation.
; All component replacement is by same-volume rename, with retained backups.
; No recursive deletion, no FreeCAD profile writes, no PowerShell launcher.
Unicode true
RequestExecutionLevel user
ManifestDPIAware true
SetCompressor /SOLID lzma
CRCCheck force
Name "UniStation ${VERSION}"
OutFile "${OUTFILE}"
InstallDir "$APPDATA\FreeCAD\v1-1\Mod"
InstallDirRegKey HKCU "Software\UniStation\Setup" "ModRoot"
VIProductVersion "${FILEVERSION}"
VIAddVersionKey "ProductName" "UniStation"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileVersion" "${FILEVERSION}"
VIAddVersionKey "FileDescription" "UniStation / AxisFlow setup for FreeCAD 1.1"
VIAddVersionKey "LegalCopyright" "UniStation contributors; GPL-3.0-only"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "Sections.nsh"
!include "FileFunc.nsh"
!include "nsDialogs.nsh"
!include "x64.nsh"
!if ${NSIS_PTR_SIZE} != 4
  !error "Use the standard x86-Unicode NSIS stub; component payload targets Windows x64."
!endif
!include "${TABLES}"
!define REGKEY "Software\UniStation\Setup"
!define UNKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\UniStation"
!define OWNER "UniStation.WindowsInstaller"
!include "${__FILEDIR__}\FreeCAD.nsh"

Var StateDir
Var TxnDir
Var TxnName
Var RunUni
Var RunAF
Var RunDocs
Var RunLinks
Var OldUniManaged
Var OldAFManaged
Var HadUni
Var HadAF
Var NewUni
Var NewAF
Var ProcessBlocked
Var MutexHandle
Var UnDialog
Var UnUniCheck
Var UnAFCheck
Var UnRunUni
Var UnRunAF
Var OriginalToken
Var OriginalPath
Var RemoveName
Var SummaryText

!define MUI_ABORTWARNING
!define MUI_LANGDLL_REGISTRY_ROOT HKCU
!define MUI_LANGDLL_REGISTRY_KEY "${REGKEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Language"
!define MUI_WELCOMEPAGE_TEXT "$(Welcome)"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${PAYLOAD}\Support\LICENSES.txt"
Page custom FreeCADPage FreeCADPageLeave
!insertmacro MUI_PAGE_COMPONENTS
!define MUI_DIRECTORYPAGE_TEXT_TOP "$(DirectoryHelp)"
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE ValidateTarget
!insertmacro MUI_PAGE_DIRECTORY
Page custom SummaryPage
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "$(Finished)"
!define MUI_FINISHPAGE_SHOWREADME "$StateDir\USER-GUIDE.txt"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
UninstPage custom un.ComponentsPage un.ComponentsLeave
!insertmacro MUI_UNPAGE_INSTFILES
!define MUI_UNFINISHPAGE_TEXT "$(UnFinished)"
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "English"

LangString Welcome ${LANG_RUSSIAN} "Мастер установит выбранные компоненты в ваш FreeCAD 1.1.$\r$\n$\r$\nЗакройте FreeCAD перед продолжением.$\r$\n$\r$\nПуть по умолчанию: %APPDATA%\FreeCAD\v1-1\Mod.$\r$\nСуществующие выбранные компоненты будут сохранены в резервную копию. FreeCAD устанавливается отдельно."
LangString Welcome ${LANG_ENGLISH} "Install selected components into your FreeCAD 1.1.$\r$\n$\r$\nClose FreeCAD before continuing.$\r$\n$\r$\nDefault: %APPDATA%\FreeCAD\v1-1\Mod.$\r$\nExisting selected components will be backed up. FreeCAD is installed separately."
LangString DirectoryHelp ${LANG_RUSSIAN} "Выберите родительский каталог Mod вашего профиля FreeCAD. Внутри будут созданы папки UniStation и/или AxisFlow. Для обычного FreeCAD 1.1 оставьте предложенный путь. Для portable/другого профиля укажите его каталог Mod."
LangString DirectoryHelp ${LANG_ENGLISH} "Choose the parent Mod directory of your FreeCAD profile. UniStation and/or AxisFlow will be created inside it. Keep the default for ordinary FreeCAD 1.1; choose its actual Mod directory for a portable/custom profile."
LangString UniName ${LANG_RUSSIAN} "UniStation — инструменты черчения"
LangString UniName ${LANG_ENGLISH} "UniStation — drafting tools"
LangString AFName ${LANG_RUSSIAN} "AxisFlow — ввод координат (рекомендуется)"
LangString AFName ${LANG_ENGLISH} "AxisFlow — coordinate input (recommended)"
LangString DocsName ${LANG_RUSSIAN} "Документация UniStation"
LangString DocsName ${LANG_ENGLISH} "UniStation documentation"
LangString LinksName ${LANG_RUSSIAN} "Ярлыки UniStation и ссылки в меню «Пуск»"
LangString LinksName ${LANG_ENGLISH} "UniStation shortcuts and Start menu links"
LangString UniDesc ${LANG_RUSSIAN} "Верстак UniStation. Требуется выбранный здесь либо уже установленный совместимый AxisFlow."
LangString UniDesc ${LANG_ENGLISH} "UniStation workbench. Requires the selected or an existing compatible AxisFlow."
LangString AFDesc ${LANG_RUSSIAN} "Проверенный ранее AxisFlow theme_01 для Windows x64 / Python 3.11, вместе с LGPL и полными исходниками. Можно пропустить при наличии совместимого модуля."
LangString AFDesc ${LANG_ENGLISH} "Previously accepted AxisFlow theme_01 for Windows x64 / Python 3.11, including LGPL and complete sources. Skip only when a compatible module already exists."
LangString DocsDesc ${LANG_RUSSIAN} "Руководство по установке, использованию и ограничениям."
LangString DocsDesc ${LANG_ENGLISH} "Installation, usage and limitations documentation."
LangString LinksDesc ${LANG_RUSSIAN} "Запуск FreeCAD с активным UniStation: меню «Пуск» и рабочий стол. Ссылки на проект и удаление."
LangString LinksDesc ${LANG_ENGLISH} "Start FreeCAD with UniStation active from the Start menu and desktop. Project and uninstall links."
LangString CloseFreeCAD ${LANG_RUSSIAN} "Закройте FreeCAD и FreeCADCmd, затем повторите. Мастер не завершает процессы."
LangString CloseFreeCAD ${LANG_ENGLISH} "Close FreeCAD and FreeCADCmd, then retry. Setup never terminates processes."
LangString ProcessError ${LANG_RUSSIAN} "Не удалось проверить запущенные процессы. Установка остановлена до изменения компонентов."
LangString ProcessError ${LANG_ENGLISH} "Unable to inspect running processes. Setup stopped before changing components."
LangString InvalidPath ${LANG_RUSSIAN} "Укажите полный путь к каталогу с именем Mod. Не выбирайте корень диска, папку самого компонента или служебную папку установщика."
LangString InvalidPath ${LANG_ENGLISH} "Choose an absolute directory named Mod, not a drive root, component directory or setup state directory."
LangString OtherInstall ${LANG_RUSSIAN} "Есть установка в другом каталоге. Для переноса сначала удалите её управляемые компоненты либо выберите прежний каталог."
LangString OtherInstall ${LANG_ENGLISH} "A managed installation exists elsewhere. Uninstall its managed components before moving, or select its existing directory."
LangString ForeignState ${LANG_RUSSIAN} "Служебная папка уже существует, но не принадлежит этой установке. Выберите другой каталог; существующие файлы сохранены."
LangString ForeignState ${LANG_ENGLISH} "The state directory already exists but does not belong to this installation. Choose another location; existing files were preserved."
LangString UnForeignState ${LANG_RUSSIAN} "Не удалось подтвердить принадлежность служебной папки:$\r$\n$StateDir$\r$\n$\r$\nУдаление остановлено до изменения компонентов. Не перемещайте служебные файлы; повторите установку в прежний Mod."
LangString UnForeignState ${LANG_ENGLISH} "Cannot verify ownership of the setup state directory:$\r$\n$StateDir$\r$\n$\r$\nUninstall stopped before changing components. Keep the setup files in place; reinstall into the existing Mod directory."
LangString SelectComponent ${LANG_RUSSIAN} "Выберите UniStation и/или AxisFlow."
LangString SelectComponent ${LANG_ENGLISH} "Select UniStation and/or AxisFlow."
LangString KeepAF ${LANG_RUSSIAN} "Оставленный UniStation требует AxisFlow. Оставьте AxisFlow либо выберите удаление обоих компонентов."
LangString KeepAF ${LANG_ENGLISH} "The retained UniStation needs AxisFlow. Keep AxisFlow or select both components for removal."
LangString NeedAF ${LANG_RUSSIAN} "В выбранном Mod не найден AxisFlow. Вернитесь к компонентам и выберите AxisFlow либо укажите Mod с совместимым AxisFlow."
LangString NeedAF ${LANG_ENGLISH} "AxisFlow was not found in the selected Mod directory. Select it in Components, or choose a Mod directory with a compatible AxisFlow."
LangString SummaryTitle ${LANG_RUSSIAN} "Готово к установке"
LangString SummaryTitle ${LANG_ENGLISH} "Ready to install"
LangString SummaryHelp ${LANG_RUSSIAN} "Проверьте каталог и выбранные компоненты."
LangString SummaryHelp ${LANG_ENGLISH} "Review the target and selected components."
LangString SummaryBody ${LANG_RUSSIAN} "FreeCAD $FcVersion: $FcExe$\r$\nПользователь: $FcUser$\r$\nКаталог Mod: $INSTDIR$\r$\n$\r$\nВыбрано:$\r$\n$SummaryText$\r$\nПрежние компоненты сохраняются в .UniStation-Installer\transactions. Настройки и документы FreeCAD не изменяются. Снятый флажок пропускает компонент, а не удаляет его."
LangString SummaryBody ${LANG_ENGLISH} "FreeCAD $FcVersion: $FcExe$\r$\nAccount: $FcUser$\r$\nMod directory: $INSTDIR$\r$\n$\r$\nSelected:$\r$\n$SummaryText$\r$\nPrevious components are retained in .UniStation-Installer\transactions. FreeCAD settings/documents are unchanged. Unchecking a component skips it; it does not uninstall it."
LangString InstallError ${LANG_RUSSIAN} "Установка не завершена. Прежние папки восстановлены там, где это возможно. Все перемещённые версии/частичные файлы сохранены в:$\r$\n$TxnDir$\r$\nПроверьте журнал в этом каталоге перед повтором."
LangString InstallError ${LANG_ENGLISH} "Setup did not complete. Previous folders were restored where possible. All moved versions/partial files were retained in:$\r$\n$TxnDir$\r$\nInspect its journal before retrying."
LangString RegistryError ${LANG_RUSSIAN} "Компоненты установлены, но запись удаления Windows создать не удалось. Удаление можно запустить напрямую:$\r$\n$StateDir\Uninstall.exe"
LangString RegistryError ${LANG_ENGLISH} "Components are installed, but the Windows uninstall entry could not be written. Run the uninstaller directly:$\r$\n$StateDir\Uninstall.exe"
LangString Finished ${LANG_RUSSIAN} "Выбранные компоненты установлены для $FcUser.$\r$\n$\r$\nЕсли выбраны ярлыки и UniStation, запускайте «UniStation - FreeCAD»: верстак будет выбран автоматически. Создайте или откройте документ.$\r$\n$\r$\nИспользуйте ту же учётную запись Windows. Удаление доступно в списке приложений."
LangString Finished ${LANG_ENGLISH} "Selected components are installed for $FcUser.$\r$\n$\r$\nIf shortcuts and UniStation were selected, start UniStation - FreeCAD to activate the workbench automatically. Create/open a document.$\r$\n$\r$\nUse the same Windows account. Uninstall is available in Windows Apps."
LangString ShortcutError ${LANG_RUSSIAN} "Не удалось создать один из ярлыков UniStation, либо такой ярлык уже существует и не принадлежит мастеру. Компоненты установлены; существующий ярлык не заменён."
LangString ShortcutError ${LANG_ENGLISH} "A UniStation shortcut could not be created, or an existing shortcut is not owned by setup. Components are installed; the existing shortcut was preserved."
LangString UnHelp ${LANG_RUSSIAN} "Выберите компоненты для удаления. Если сохранена прежняя версия, она будет восстановлена. AxisFlow можно оставить для других дополнений."
LangString UnHelp ${LANG_ENGLISH} "Select components to remove. A saved previous version will be restored. You may keep AxisFlow for other addons."
LangString UnError ${LANG_RUSSIAN} "Не удалось безопасно обработать компонент $RemoveName. Его файлы и резервные копии сохранены. Закройте FreeCAD и проверьте:$\r$\n$StateDir"
LangString UnError ${LANG_ENGLISH} "Unable to safely process $RemoveName. Its files and backups were preserved. Close FreeCAD and inspect:$\r$\n$StateDir"
LangString UnFinished ${LANG_RUSSIAN} "Выбранные компоненты обработаны. Если вы оставили другие компоненты, запись удаления сохраняется.$\r$\n$\r$\nПрежние версии восстановлены при наличии. Убранные версии и дополнительные файлы сохранены в:$\r$\n$StateDir$\r$\n$\r$\nКаталог Mod и настройки FreeCAD не удалены."
LangString UnFinished ${LANG_ENGLISH} "Selected components were processed. The uninstall entry remains if other components were kept.$\r$\n$\r$\nPrevious versions were restored when available. Retired versions and additional files remain at:$\r$\n$StateDir$\r$\n$\r$\nThe Mod directory and FreeCAD settings were not deleted."

Section "-Prepare"
  Call ValidateTarget
  InitPluginsDir
  System::Call 'kernel32::GetCurrentProcessId() i .r0'
  System::Call 'kernel32::GetTickCount() i .r1'
  StrCpy $TxnName "install-$0-$1"
  StrCpy $TxnDir "$StateDir\transactions\$TxnName"
  IfFileExists "$TxnDir" 0 +2
    Abort
  ClearErrors
  CreateDirectory "$TxnDir"
  IfErrors prepare_failed
  IfFileExists "$StateDir\state.ini" 0 +2
    CopyFiles /SILENT "$StateDir\state.ini" "$TxnDir\state-before.ini"
  ReadINIStr $OldUniManaged "$StateDir\state.ini" "Managed" "UniStation"
  ReadINIStr $OldAFManaged "$StateDir\state.ini" "Managed" "AxisFlow"
  ; A folder replaced manually is a new pre-existing version, not our old payload.
  ReadINIStr $0 "$INSTDIR\UniStation\.managed-by-unistation.ini" "Owner" "Product"
  ReadINIStr $1 "$INSTDIR\UniStation\.managed-by-unistation.ini" "Owner" "Root"
  ${If} $0 != "${OWNER}"
  ${OrIf} $1 != $INSTDIR
    StrCpy $OldUniManaged 0
  ${EndIf}
  ReadINIStr $0 "$INSTDIR\AxisFlow\.managed-by-unistation.ini" "Owner" "Product"
  ReadINIStr $1 "$INSTDIR\AxisFlow\.managed-by-unistation.ini" "Owner" "Root"
  ${If} $0 != "${OWNER}"
  ${OrIf} $1 != $INSTDIR
    StrCpy $OldAFManaged 0
  ${EndIf}
  ClearErrors
  WriteINIStr "$StateDir\state.ini" "Install" "Owner" "${OWNER}"
  WriteINIStr "$StateDir\state.ini" "Install" "Root" "$INSTDIR"
  WriteINIStr "$TxnDir\journal.ini" "Transaction" "State" "prepared"
  IfErrors prepare_failed
  StrCpy $HadUni 0
  StrCpy $HadAF 0
  StrCpy $NewUni 0
  StrCpy $NewAF 0
  SetOutPath "$PLUGINSDIR\Support"
  File /r "${PAYLOAD}\Support\*.*"
  IfErrors prepare_failed
  Goto prepare_done
prepare_failed:
  MessageBox MB_ICONSTOP "$(InstallError)"
  Abort
prepare_done:
SectionEnd

Section "$(UniName)" SEC_UNI
  SectionIn 1 2
  SetOutPath "$PLUGINSDIR\UniRuntime"
  ClearErrors
  File /r "${PAYLOAD}\UniRuntime\*.*"
  IfErrors 0 +2
    Abort
SectionEnd
Section "$(AFName)" SEC_AF
  SectionIn 1
  SetOutPath "$PLUGINSDIR\AxisFlow"
  ClearErrors
  File /r "${PAYLOAD}\AxisFlow\*.*"
  IfErrors 0 +2
    Abort
SectionEnd
Section "$(DocsName)" SEC_DOCS
  SectionIn 1 2
  SetOutPath "$PLUGINSDIR\UniDocs"
  ClearErrors
  File /r "${PAYLOAD}\UniDocs\*.*"
  IfErrors 0 +2
    Abort
SectionEnd
Section "$(LinksName)" SEC_LINKS
  SectionIn 1 2
SectionEnd

Section "-Commit"
  Call EnsureClosed
  !insertmacro CopySupport "$PLUGINSDIR\Support" "$StateDir"
  ${If} $RunUni == 1
    IfFileExists "$INSTDIR\UniStation" 0 uni_not_present
    ClearErrors
    Rename "$INSTDIR\UniStation" "$TxnDir\UniStation"
    IfErrors install_failed
    StrCpy $HadUni 1
uni_not_present:
  ${EndIf}
  ${If} $RunAF == 1
    IfFileExists "$INSTDIR\AxisFlow" 0 af_not_present
    ClearErrors
    Rename "$INSTDIR\AxisFlow" "$TxnDir\AxisFlow"
    IfErrors install_failed
    StrCpy $HadAF 1
af_not_present:
  ${EndIf}
  ${If} $RunUni == 1
    StrCpy $NewUni 1
    !insertmacro CopyUniRuntime "$PLUGINSDIR\UniRuntime" "$INSTDIR\UniStation"
    ${If} $RunDocs == 1
      !insertmacro CopyUniDocs "$PLUGINSDIR\UniDocs" "$INSTDIR\UniStation"
    ${EndIf}
    ClearErrors
    WriteINIStr "$INSTDIR\UniStation\.managed-by-unistation.ini" "Owner" "Product" "${OWNER}"
    WriteINIStr "$INSTDIR\UniStation\.managed-by-unistation.ini" "Owner" "Root" "$INSTDIR"
    IfErrors install_failed
  ${EndIf}
  ${If} $RunAF == 1
    StrCpy $NewAF 1
    !insertmacro CopyAxisFlow "$PLUGINSDIR\AxisFlow" "$INSTDIR\AxisFlow"
    ClearErrors
    WriteINIStr "$INSTDIR\AxisFlow\.managed-by-unistation.ini" "Owner" "Product" "${OWNER}"
    WriteINIStr "$INSTDIR\AxisFlow\.managed-by-unistation.ini" "Owner" "Root" "$INSTDIR"
    IfErrors install_failed
  ${EndIf}
  ClearErrors
  WriteUninstaller "$StateDir\Uninstall.exe"
  IfErrors install_failed
  ClearErrors
  ${If} $RunUni == 1
    ${If} $HadUni == 1
    ${AndIf} $OldUniManaged != 1
      WriteINIStr "$StateDir\state.ini" "Original" "UniStation" "$TxnName"
    ${EndIf}
    WriteINIStr "$StateDir\state.ini" "Managed" "UniStation" 1
  ${EndIf}
  ${If} $RunAF == 1
    ${If} $HadAF == 1
    ${AndIf} $OldAFManaged != 1
      WriteINIStr "$StateDir\state.ini" "Original" "AxisFlow" "$TxnName"
    ${EndIf}
    WriteINIStr "$StateDir\state.ini" "Managed" "AxisFlow" 1
  ${EndIf}
  WriteINIStr "$StateDir\state.ini" "Install" "Version" "${VERSION}"
  WriteINIStr "$StateDir\state.ini" "Launch" "FreeCADExe" "$FcExe"
  WriteINIStr "$StateDir\state.ini" "Launch" "FreeCADVersion" "$FcVersion"
  WriteINIStr "$StateDir\state.ini" "Launch" "UserProfile" "$PROFILE"
  WriteINIStr "$StateDir\state.ini" "Install" "Status" "installed"
  IfErrors install_failed
  ; Rollback is for component/filesystem errors above. Registration follows commit.
  ClearErrors
  WriteRegStr HKCU "${REGKEY}" "ModRoot" "$INSTDIR"
  WriteRegStr HKCU "${REGKEY}" "FreeCADExe" "$FcExe"
  WriteRegStr HKCU "${UNKEY}" "DisplayName" "UniStation ${VERSION} / AxisFlow"
  WriteRegStr HKCU "${UNKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNKEY}" "Publisher" "UniStation contributors"
  WriteRegStr HKCU "${UNKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNKEY}" "UninstallString" '$\"$StateDir\Uninstall.exe$\"'
  WriteRegStr HKCU "${UNKEY}" "DisplayIcon" "$StateDir\Uninstall.exe"
  WriteRegStr HKCU "${UNKEY}" "URLInfoAbout" "https://github.com/LeonidWiebe/UniStation"
  WriteRegDWORD HKCU "${UNKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNKEY}" "NoRepair" 1
  IfErrors 0 +2
    MessageBox MB_ICONEXCLAMATION "$(RegistryError)"
  ${If} $RunLinks == 1
    CreateDirectory "$SMPROGRAMS\UniStation"
    CreateShortcut "$SMPROGRAMS\UniStation\Uninstall.lnk" "$StateDir\Uninstall.exe"
    WriteINIStr "$SMPROGRAMS\UniStation\UniStation.url" "InternetShortcut" "URL" "https://github.com/LeonidWiebe/UniStation"
    ReadINIStr $0 "$StateDir\state.ini" "Managed" "UniStation"
    ${If} $0 == 1
      Call CreateLaunchShortcuts
    ${EndIf}
  ${EndIf}
  WriteINIStr "$TxnDir\journal.ini" "Transaction" "State" "committed"
  Goto install_done
install_failed:
  ; Preserve partial new directories, then try to put previous directories back.
  ${If} $NewUni == 1
    Rename "$INSTDIR\UniStation" "$TxnDir\partial-UniStation"
  ${EndIf}
  ${If} $NewAF == 1
    Rename "$INSTDIR\AxisFlow" "$TxnDir\partial-AxisFlow"
  ${EndIf}
  ${If} $HadUni == 1
    Rename "$TxnDir\UniStation" "$INSTDIR\UniStation"
  ${EndIf}
  ${If} $HadAF == 1
    Rename "$TxnDir\AxisFlow" "$INSTDIR\AxisFlow"
  ${EndIf}
  IfFileExists "$TxnDir\state-before.ini" rollback_existing_state rollback_new_state
rollback_existing_state:
  CopyFiles /SILENT "$TxnDir\state-before.ini" "$StateDir\state.ini"
  Goto rollback_state_done
rollback_new_state:
  WriteINIStr "$StateDir\state.ini" "Managed" "UniStation" 0
  WriteINIStr "$StateDir\state.ini" "Managed" "AxisFlow" 0
  DeleteINIStr "$StateDir\state.ini" "Original" "UniStation"
  DeleteINIStr "$StateDir\state.ini" "Original" "AxisFlow"
rollback_state_done:
  WriteINIStr "$TxnDir\journal.ini" "Transaction" "State" "failed-rollback-attempted"
  MessageBox MB_ICONSTOP "$(InstallError)"
  Abort
install_done:
SectionEnd

InstType "UniStation + AxisFlow"
InstType "UniStation"

!macro ProcessGuard PREFIX
Function ${PREFIX}EnsureClosed
  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  StrCpy $ProcessBlocked 0
  System::Call 'kernel32::CreateToolhelp32Snapshot(i 2, i 0) p .r0'
  ${If} $0 == -1
    StrCpy $ProcessBlocked 2
    Goto process_done
  ${EndIf}
  System::Alloc 556
  Pop $1
  ${If} $1 == 0
    StrCpy $ProcessBlocked 2
    Goto process_close
  ${EndIf}
  ; Unicode x86 NSIS PROCESSENTRY32W: dwSize=556, szExeFile offset=36.
  System::Call '*$1(i 556)'
  System::Call 'kernel32::Process32FirstW(p r0, p r1) i .r2'
  ${If} $2 == 0
    StrCpy $ProcessBlocked 2
  ${EndIf}
  ${DoWhile} $2 != 0
    IntOp $3 $1 + 36
    System::Call '*$3(&w260 .r4)'
    ${If} $4 == "FreeCAD.exe"
    ${OrIf} $4 == "FreeCADCmd.exe"
      StrCpy $ProcessBlocked 1
      ${ExitDo}
    ${EndIf}
    System::Call 'kernel32::Process32NextW(p r0, p r1) i .r2'
  ${Loop}
  System::Free $1
process_close:
  System::Call 'kernel32::CloseHandle(p r0)'
process_done:
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0
  ${If} $ProcessBlocked == 1
    MessageBox MB_ICONSTOP "$(CloseFreeCAD)"
    Abort
  ${ElseIf} $ProcessBlocked == 2
    MessageBox MB_ICONSTOP "$(ProcessError)"
    Abort
  ${EndIf}
FunctionEnd
!macroend
!insertmacro ProcessGuard ""
!insertmacro ProcessGuard "un."

Function ReadSelection
  StrCpy $RunUni 0
  StrCpy $RunAF 0
  StrCpy $RunDocs 0
  StrCpy $RunLinks 0
  ${If} ${SectionIsSelected} ${SEC_UNI}
    StrCpy $RunUni 1
  ${EndIf}
  ${If} ${SectionIsSelected} ${SEC_AF}
    StrCpy $RunAF 1
  ${EndIf}
  ${If} ${SectionIsSelected} ${SEC_DOCS}
    StrCpy $RunDocs 1
  ${EndIf}
  ${If} ${SectionIsSelected} ${SEC_LINKS}
    StrCpy $RunLinks 1
  ${EndIf}
FunctionEnd

Function .onSelChange
  ${IfNot} ${SectionIsSelected} ${SEC_UNI}
    !insertmacro UnselectSection ${SEC_DOCS}
    !insertmacro SetSectionFlag ${SEC_DOCS} ${SF_RO}
  ${Else}
    !insertmacro ClearSectionFlag ${SEC_DOCS} ${SF_RO}
  ${EndIf}
FunctionEnd

Function ValidateTarget
  Call EnsureClosed
  StrCpy $FcCandidate $FcExe
  Call ProbeFreeCAD
  ${If} $FcProbeError != ""
    IfSilent invalid_freecad_silent
    MessageBox MB_ICONSTOP "$FcProbeError"
    Abort
invalid_freecad_silent:
    SetErrorLevel 2
    Abort
  ${EndIf}
  StrCpy $FcExe $FcCandidate
  StrCpy $FcVersion $FcProbeVersion
  Call ReadSelection
  ${GetRoot} "$INSTDIR" $0
  ${If} $0 == ""
    Goto invalid_target
  ${EndIf}
  ; Win32 GetFullPathNameW canonicalizes even a fresh, not-yet-created Mod path.
  System::Call 'kernel32::GetFullPathNameW(w "$INSTDIR", i ${NSIS_MAX_STRLEN}, w .r9, p 0) i .r8'
  ${If} $8 == 0
  ${OrIf} $8 >= ${NSIS_MAX_STRLEN}
    Goto invalid_target
  ${EndIf}
  StrCpy $INSTDIR $9
  GetFullPathName $0 "$0\"
  ${If} $INSTDIR == $0
    Goto invalid_target
  ${EndIf}
  ${GetFileName} "$INSTDIR" $0
  ${If} $0 != "Mod"
    Goto invalid_target
  ${EndIf}
  StrCpy $StateDir "$INSTDIR\.UniStation-Installer"
  IfFileExists "$StateDir" 0 state_ok
  ReadINIStr $0 "$StateDir\state.ini" "Install" "Owner"
  ReadINIStr $1 "$StateDir\state.ini" "Install" "Root"
  ${If} $0 != "${OWNER}"
  ${OrIf} $1 != $INSTDIR
    MessageBox MB_ICONSTOP "$(ForeignState)"
    Abort
  ${EndIf}
state_ok:
  ReadRegStr $0 HKCU "${REGKEY}" "ModRoot"
  ${If} $0 != ""
  ${AndIf} $0 != $INSTDIR
    IfFileExists "$0\.UniStation-Installer\state.ini" 0 old_install_absent
    MessageBox MB_ICONSTOP "$(OtherInstall)"
    Abort
  ${EndIf}
old_install_absent:
  ${If} $RunUni == 0
  ${AndIf} $RunAF == 0
    MessageBox MB_ICONSTOP "$(SelectComponent)"
    Abort
  ${EndIf}
  ${If} $RunUni == 1
  ${AndIf} $RunAF == 0
    IfFileExists "$INSTDIR\AxisFlow\AxisFlow.pyd" 0 need_axisflow
    IfFileExists "$INSTDIR\AxisFlow\InitGui.py" target_ok need_axisflow
  ${EndIf}
  Goto target_ok
need_axisflow:
  MessageBox MB_ICONSTOP "$(NeedAF)"
  Abort
invalid_target:
  MessageBox MB_ICONSTOP "$(InvalidPath)"
  Abort
target_ok:
FunctionEnd

Function SummaryPage
  Call ValidateTarget
  !insertmacro MUI_HEADER_TEXT "$(SummaryTitle)" "$(SummaryHelp)"
  StrCpy $SummaryText ""
  ${If} $RunUni == 1
    StrCpy $SummaryText "$SummaryText  UniStation$\r$\n"
  ${EndIf}
  ${If} $RunAF == 1
    StrCpy $SummaryText "$SummaryText  AxisFlow$\r$\n"
  ${EndIf}
  ${If} $RunDocs == 1
    StrCpy $SummaryText "$SummaryText  $(DocsName)$\r$\n"
  ${EndIf}
  ${If} $RunLinks == 1
    StrCpy $SummaryText "$SummaryText  $(LinksName)$\r$\n"
  ${EndIf}
  nsDialogs::Create 1018
  Pop $0
  ${NSD_CreateLabel} 0 0 100% 100% "$(SummaryBody)"
  Pop $0
  nsDialogs::Show
FunctionEnd

Function .onInit
  SetShellVarContext current
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "Windows x64 is required."
    Quit
  ${EndIf}
  System::Call 'kernel32::CreateMutexW(p 0, i 0, w "Local\UniStationInstaller") p .r0 ?e'
  Pop $1
  StrCpy $MutexHandle $0
  ${If} $MutexHandle == 0
    MessageBox MB_ICONSTOP "$(ProcessError)"
    Quit
  ${EndIf}
  ${If} $1 == 183
    MessageBox MB_ICONSTOP "Another UniStation setup/uninstaller is running."
    Quit
  ${EndIf}
  !insertmacro MUI_LANGDLL_DISPLAY
  Call EnsureClosed
  Call DetectFreeCAD
FunctionEnd

Function CreateLaunchShortcuts
  ; An existing unrelated shortcut must never be overwritten.
  ReadINIStr $0 "$StateDir\state.ini" "Launch" "StartMenuOwned"
  IfFileExists "$SMPROGRAMS\UniStation\UniStation - FreeCAD.lnk" 0 create_start_shortcut
  StrCmp $0 1 create_start_shortcut
  MessageBox MB_ICONEXCLAMATION "$(ShortcutError)"
  Goto desktop_shortcut
create_start_shortcut:
  ClearErrors
  CreateShortcut "$SMPROGRAMS\UniStation\UniStation - FreeCAD.lnk" "$StateDir\Launch-UniStation.exe" "" "$FcExe" 0 SW_SHOWNORMAL "" "UniStation / FreeCAD"
  IfErrors start_shortcut_failed
  WriteINIStr "$StateDir\state.ini" "Launch" "StartMenuOwned" 1
  Goto desktop_shortcut
start_shortcut_failed:
  MessageBox MB_ICONEXCLAMATION "$(ShortcutError)"
desktop_shortcut:
  ReadINIStr $0 "$StateDir\state.ini" "Launch" "DesktopOwned"
  IfFileExists "$DESKTOP\UniStation - FreeCAD.lnk" 0 create_desktop_shortcut
  StrCmp $0 1 create_desktop_shortcut
  MessageBox MB_ICONEXCLAMATION "$(ShortcutError)"
  Return
create_desktop_shortcut:
  ClearErrors
  CreateShortcut "$DESKTOP\UniStation - FreeCAD.lnk" "$StateDir\Launch-UniStation.exe" "" "$FcExe" 0 SW_SHOWNORMAL "" "UniStation / FreeCAD"
  IfErrors desktop_shortcut_failed
  WriteINIStr "$StateDir\state.ini" "Launch" "DesktopOwned" 1
  Return
desktop_shortcut_failed:
  MessageBox MB_ICONEXCLAMATION "$(ShortcutError)"
FunctionEnd

Function un.onInit
  SetShellVarContext current
  !insertmacro MUI_UNGETLANGUAGE
  ; NSIS self-copies the uninstaller to TEMP. EXEDIR belongs to that copy;
  ; initial INSTDIR is the original uninstaller directory passed by the stub.
  ; Taking the parent of a dummy filename also removes a trailing backslash.
  GetFullPathName $0 "$INSTDIR\state.ini"
  ${GetParent} "$0" $StateDir
  ${GetFileName} "$StateDir" $0
  ${If} $0 != ".UniStation-Installer"
    Goto un_invalid_state
  ${EndIf}
  ${GetParent} "$StateDir" $INSTDIR
  GetFullPathName $INSTDIR "$INSTDIR"
  ReadINIStr $0 "$StateDir\state.ini" "Install" "Owner"
  ReadINIStr $1 "$StateDir\state.ini" "Install" "Root"
  ${If} $0 != "${OWNER}"
  ${OrIf} $1 != $INSTDIR
    Goto un_invalid_state
  ${EndIf}
  System::Call 'kernel32::CreateMutexW(p 0, i 0, w "Local\UniStationInstaller") p .r0 ?e'
  Pop $1
  StrCpy $MutexHandle $0
  ${If} $MutexHandle == 0
    MessageBox MB_ICONSTOP "$(ProcessError)"
    Quit
  ${EndIf}
  ${If} $1 == 183
    MessageBox MB_ICONSTOP "Another UniStation setup/uninstaller is running."
    Quit
  ${EndIf}
  Call un.EnsureClosed
  ReadINIStr $UnRunUni "$StateDir\state.ini" "Managed" "UniStation"
  ReadINIStr $UnRunAF "$StateDir\state.ini" "Managed" "AxisFlow"
  Return
un_invalid_state:
  SetErrorLevel 2
  MessageBox MB_ICONSTOP "$(UnForeignState)"
  Quit
FunctionEnd

Function un.ComponentsPage
  nsDialogs::Create 1018
  Pop $UnDialog
  ${NSD_CreateLabel} 0 0 100% 45u "$(UnHelp)"
  Pop $0
  ${NSD_CreateCheckbox} 0 55u 100% 18u "UniStation"
  Pop $UnUniCheck
  ${If} $UnRunUni == 1
    ${NSD_Check} $UnUniCheck
  ${Else}
    EnableWindow $UnUniCheck 0
  ${EndIf}
  ${NSD_CreateCheckbox} 0 80u 100% 18u "AxisFlow"
  Pop $UnAFCheck
  ${If} $UnRunAF == 1
    ${NSD_Check} $UnAFCheck
  ${Else}
    EnableWindow $UnAFCheck 0
  ${EndIf}
  nsDialogs::Show
FunctionEnd

Function un.ComponentsLeave
  ${NSD_GetState} $UnUniCheck $UnRunUni
  ${NSD_GetState} $UnAFCheck $UnRunAF
  ${If} $UnRunUni == 0
  ${AndIf} $UnRunAF == 0
    MessageBox MB_ICONSTOP "$(SelectComponent)"
    Abort
  ${EndIf}
  ${If} $UnRunAF == 1
  ${AndIf} $UnRunUni == 0
    ReadINIStr $0 "$StateDir\state.ini" "Managed" "UniStation"
    ReadINIStr $1 "$StateDir\state.ini" "Original" "AxisFlow"
    ${If} $0 == 1
    ${AndIf} $1 == ""
      MessageBox MB_ICONSTOP "$(KeepAF)"
      Abort
    ${EndIf}
  ${EndIf}
FunctionEnd

Function un.RemoveComponent
  ; RemoveName is a literal component name supplied by the section below.
  ReadINIStr $0 "$StateDir\state.ini" "Managed" "$RemoveName"
  ${If} $0 != 1
    Return
  ${EndIf}
  StrCpy $OriginalPath ""
  ReadINIStr $OriginalToken "$StateDir\state.ini" "Original" "$RemoveName"
  ${If} $OriginalToken != ""
    GetFullPathName $0 "$StateDir\transactions\$OriginalToken"
    ${GetParent} "$0" $1
    GetFullPathName $2 "$StateDir\transactions"
    ${If} $1 != $2
      Goto un_component_error
    ${EndIf}
    StrCpy $OriginalPath "$0\$RemoveName"
    IfFileExists "$OriginalPath" 0 un_component_error
  ${EndIf}
  IfFileExists "$INSTDIR\$RemoveName" 0 un_no_current
  ReadINIStr $0 "$INSTDIR\$RemoveName\.managed-by-unistation.ini" "Owner" "Product"
  ReadINIStr $1 "$INSTDIR\$RemoveName\.managed-by-unistation.ini" "Owner" "Root"
  ${If} $0 != "${OWNER}"
  ${OrIf} $1 != $INSTDIR
    Goto un_component_error
  ${EndIf}
  ClearErrors
  Rename "$INSTDIR\$RemoveName" "$TxnDir\$RemoveName"
  IfErrors un_component_error
un_no_current:
  ${If} $OriginalPath != ""
    ClearErrors
    Rename "$OriginalPath" "$INSTDIR\$RemoveName"
    IfErrors 0 un_restore_ok
    Rename "$TxnDir\$RemoveName" "$INSTDIR\$RemoveName"
    Goto un_component_error
  ${EndIf}
un_restore_ok:
  WriteINIStr "$StateDir\state.ini" "Managed" "$RemoveName" 0
  DeleteINIStr "$StateDir\state.ini" "Original" "$RemoveName"
  WriteINIStr "$TxnDir\journal.ini" "Processed" "$RemoveName" 1
  Return
un_component_error:
  WriteINIStr "$TxnDir\journal.ini" "Errors" "$RemoveName" "preserved"
  MessageBox MB_ICONSTOP "$(UnError)"
  SetErrors
FunctionEnd

Section "Uninstall"
  Call un.EnsureClosed
  System::Call 'kernel32::GetCurrentProcessId() i .r0'
  System::Call 'kernel32::GetTickCount() i .r1'
  StrCpy $TxnDir "$StateDir\transactions\remove-$0-$1"
  IfFileExists "$TxnDir" 0 +2
    Abort
  ClearErrors
  CreateDirectory "$TxnDir"
  IfErrors 0 +2
    Abort
  ${If} $UnRunUni == 1
    StrCpy $RemoveName "UniStation"
    Call un.RemoveComponent
  ${EndIf}
  ${If} $UnRunAF == 1
    StrCpy $RemoveName "AxisFlow"
    Call un.RemoveComponent
  ${EndIf}
  ReadINIStr $0 "$StateDir\state.ini" "Managed" "UniStation"
  ReadINIStr $1 "$StateDir\state.ini" "Managed" "AxisFlow"
  ${If} $0 != 1
    ReadINIStr $2 "$StateDir\state.ini" "Launch" "StartMenuOwned"
    ${If} $2 == 1
      Delete "$SMPROGRAMS\UniStation\UniStation - FreeCAD.lnk"
      DeleteINIStr "$StateDir\state.ini" "Launch" "StartMenuOwned"
    ${EndIf}
    ReadINIStr $2 "$StateDir\state.ini" "Launch" "DesktopOwned"
    ${If} $2 == 1
      Delete "$DESKTOP\UniStation - FreeCAD.lnk"
      DeleteINIStr "$StateDir\state.ini" "Launch" "DesktopOwned"
    ${EndIf}
  ${EndIf}
  ${If} $0 != 1
  ${AndIf} $1 != 1
    ReadRegStr $2 HKCU "${REGKEY}" "ModRoot"
    ${If} $2 == $INSTDIR
      DeleteRegKey HKCU "${UNKEY}"
      DeleteRegKey HKCU "${REGKEY}"
      Delete "$SMPROGRAMS\UniStation\Uninstall.lnk"
      Delete "$SMPROGRAMS\UniStation\UniStation.url"
      RMDir "$SMPROGRAMS\UniStation"
    ${EndIf}
    WriteINIStr "$StateDir\state.ini" "Install" "Status" "uninstalled-backups-retained"
    Delete "$StateDir\Uninstall.exe"
  ${EndIf}
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_UNI} "$(UniDesc)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_AF} "$(AFDesc)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DOCS} "$(DocsDesc)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_LINKS} "$(LinksDesc)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END
