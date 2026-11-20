; Detection runs only when the user executes setup, never while building it.
!include "WordFunc.nsh"
!include "StrFunc.nsh"
${StrStr}

Var FcExe
Var FcVersion
Var FcCandidate
Var FcProbeVersion
Var FcProbeError
Var FcLastCandidate
Var FcLastError
Var FcBin
Var FcEdit
Var FcStatus
Var FcUser

LangString FcTitle 1049 "FreeCAD для UniStation"
LangString FcTitle 1033 "FreeCAD for UniStation"
LangString FcHelp 1049 "Выберите FreeCAD ${FREECAD_MIN}–${FREECAD_MAX}, Windows x64 / Python 3.11."
LangString FcHelp 1033 "Choose FreeCAD ${FREECAD_MIN}–${FREECAD_MAX}, Windows x64 / Python 3.11."
LangString FcAccount 1049 "Установка для: $FcUser. Запускайте ярлык под этой же учётной записью Windows."
LangString FcAccount 1033 "Installing for: $FcUser. Run the shortcut using this same Windows account."
LangString FcBrowse 1049 "Обзор…"
LangString FcBrowse 1033 "Browse…"
LangString FcCheck 1049 "Проверить"
LangString FcCheck 1033 "Check"
LangString FcDownload 1049 "Открыть страницу загрузки FreeCAD"
LangString FcDownload 1033 "Open the FreeCAD download page"
LangString FcMissing 1049 "Подходящий FreeCAD не найден. Указать FreeCAD.exe вручную?$\r$\n$\r$\n«Нет» — выйти из мастера и сначала установить FreeCAD."
LangString FcMissing 1033 "No suitable FreeCAD was found. Locate FreeCAD.exe manually?$\r$\n$\r$\nChoose No to exit setup and install FreeCAD first."
LangString FcChoose 1049 "Укажите полный путь к FreeCAD.exe и нажмите «Проверить»."
LangString FcChoose 1033 "Enter the full path to FreeCAD.exe and click Check."
LangString FcInvalid 1049 "Нужен FreeCAD.exe с FreeCADCmd.exe и FreeCADApp.dll в той же папке."
LangString FcInvalid 1033 "Choose FreeCAD.exe with FreeCADCmd.exe and FreeCADApp.dll in the same folder."
LangString FcArch 1049 "Нужна 64-разрядная сборка FreeCAD с Python 3.11 (python311.dll)."
LangString FcArch 1033 "A 64-bit FreeCAD build with Python 3.11 (python311.dll) is required."
LangString FcProbeFailed 1049 "Не удалось получить версию через FreeCADCmd.exe --version. Выберите исправную установку FreeCAD."
LangString FcProbeFailed 1033 "FreeCADCmd.exe --version did not return a usable version. Choose a working FreeCAD installation."
LangString FcUnsupported 1049 "Обнаружен FreeCAD $FcProbeVersion. Для этого дистрибутива допустимы версии ${FREECAD_MIN}–${FREECAD_MAX}."
LangString FcUnsupported 1033 "Found FreeCAD $FcProbeVersion. This package allows versions ${FREECAD_MIN}–${FREECAD_MAX}."
LangString FcReady 1049 "Найден FreeCAD $FcVersion, Windows x64 / Python 3.11.$\r$\nПроверена версия и состав файлов; полная совместимость требует рабочей пробы."
LangString FcReady 1033 "Found FreeCAD $FcVersion, Windows x64 / Python 3.11.$\r$\nVersion and required files checked; full compatibility requires a runtime check."

Function ProbeFreeCAD
  ; Input FcCandidate, outputs FcProbeVersion/FcProbeError. Preserve enum registers.
  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $5
  StrCpy $FcProbeVersion ""
  StrCpy $FcProbeError "$(FcInvalid)"
  ${GetRoot} "$FcCandidate" $0
  StrCmp $0 "" fc_probe_done
  GetFullPathName $FcCandidate "$FcCandidate"
  ${GetFileName} "$FcCandidate" $0
  StrCmp $0 "FreeCAD.exe" 0 fc_probe_done
  IfFileExists "$FcCandidate" 0 fc_probe_done
  ${GetParent} "$FcCandidate" $FcBin
  IfFileExists "$FcBin\FreeCADCmd.exe" 0 fc_probe_done
  IfFileExists "$FcBin\FreeCADApp.dll" 0 fc_probe_done
  StrCpy $FcProbeError "$(FcArch)"
  System::Call 'kernel32::GetBinaryTypeW(w "$FcCandidate", *i .r1) i .r0'
  StrCmp $0 0 fc_probe_done
  StrCmp $1 6 0 fc_probe_done
  System::Call 'kernel32::GetBinaryTypeW(w "$FcBin\FreeCADCmd.exe", *i .r1) i .r0'
  StrCmp $0 0 fc_probe_done
  StrCmp $1 6 0 fc_probe_done
  IfFileExists "$FcBin\python311.dll" 0 fc_probe_done
  StrCpy $FcProbeError "$(FcProbeFailed)"
  ; --version returns before module/profile initialization in supported FreeCAD.
  ; nsExec's timeout is an inactivity timeout, not a total process deadline.
  nsExec::ExecToStack /TIMEOUT=10000 '"$FcBin\FreeCADCmd.exe" --version'
  Pop $0
  Pop $1
  StrCmp $0 0 0 fc_probe_done
  ${StrStr} $1 "$1" "FreeCAD "
  StrCmp $1 "" fc_probe_done
  StrCpy $1 $1 "" 8
  ${WordFind} "$1" " " "+1" $FcProbeVersion
  ; Require three nonempty numeric components. Reject dev/unknown output.
  StrCpy $2 0
  StrCpy $3 0
  StrCpy $5 0
fc_version_char:
  StrCpy $4 $FcProbeVersion 1 $2
  StrCmp $4 "" fc_version_end
  StrCmp $4 "." fc_version_dot
  ${StrStr} $0 "0123456789" "$4"
  StrCmp $0 "" fc_probe_done
  IntOp $5 $5 + 1
  IntOp $2 $2 + 1
  Goto fc_version_char
fc_version_dot:
  StrCmp $5 0 fc_probe_done
  StrCpy $5 0
  IntOp $3 $3 + 1
  IntOp $2 $2 + 1
  Goto fc_version_char
fc_version_end:
  StrCmp $3 2 0 fc_probe_done
  StrCmp $5 0 fc_probe_done
  StrCpy $FcProbeError "$(FcUnsupported)"
  ${VersionCompare} "$FcProbeVersion" "${FREECAD_MIN}" $0
  StrCmp $0 2 fc_probe_done
  ${VersionCompare} "$FcProbeVersion" "${FREECAD_MAX}" $0
  StrCmp $0 1 fc_probe_done
  StrCpy $FcProbeError ""
fc_probe_done:
  Pop $5
  Pop $4
  Pop $3
  Pop $2
  Pop $1
  Pop $0
FunctionEnd

Function TryFreeCAD
  StrCmp $FcExe "" 0 fc_try_done
  IfFileExists "$FcCandidate" 0 fc_try_done
  Call ProbeFreeCAD
  StrCmp $FcProbeError "" fc_try_accept
  StrCmp $FcLastCandidate "" 0 fc_try_done
  StrCpy $FcLastCandidate $FcCandidate
  StrCpy $FcLastError $FcProbeError
  Return
fc_try_accept:
  StrCpy $FcExe $FcCandidate
  StrCpy $FcVersion $FcProbeVersion
fc_try_done:
FunctionEnd

!macro FindFreeCADInRegistry ROOT VIEW
  SetRegView ${VIEW}
  ReadRegStr $FcCandidate ${ROOT} "Software\Microsoft\Windows\CurrentVersion\App Paths\FreeCAD.exe" ""
  Call TryFreeCAD
  StrCpy $2 0
fc_enum_${ROOT}_${VIEW}:
  EnumRegKey $3 ${ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall" $2
  StrCmp $3 "" fc_enum_done_${ROOT}_${VIEW}
  IntOp $2 $2 + 1
  ReadRegStr $4 ${ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\$3" "DisplayName"
  StrCpy $4 $4 7
  StrCmp $4 "FreeCAD" 0 fc_enum_${ROOT}_${VIEW}
  ReadRegStr $4 ${ROOT} "Software\Microsoft\Windows\CurrentVersion\Uninstall\$3" "InstallLocation"
  StrCmp $4 "" fc_enum_${ROOT}_${VIEW}
  StrCpy $FcCandidate "$4\bin\FreeCAD.exe"
  Call TryFreeCAD
  StrCpy $FcCandidate "$4\FreeCAD.exe"
  Call TryFreeCAD
  Goto fc_enum_${ROOT}_${VIEW}
fc_enum_done_${ROOT}_${VIEW}:
!macroend

Function DetectFreeCAD
  UserInfo::GetName
  Pop $FcUser
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} "$0" "/FREECAD=" $FcCandidate
  IfErrors fc_detect_saved
  ; An explicit selection must not silently fall back to a different binary.
  Call ProbeFreeCAD
  StrCmp $FcProbeError "" 0 fc_detect_explicit_bad
  StrCpy $FcExe $FcCandidate
  StrCpy $FcVersion $FcProbeVersion
  Return
fc_detect_explicit_bad:
  StrCpy $FcLastCandidate $FcCandidate
  StrCpy $FcLastError $FcProbeError
  Return
fc_detect_saved:
  ReadRegStr $FcCandidate HKCU "${REGKEY}" "FreeCADExe"
  Call TryFreeCAD
  !insertmacro FindFreeCADInRegistry HKCU 64
  !insertmacro FindFreeCADInRegistry HKLM 64
  !insertmacro FindFreeCADInRegistry HKCU 32
  !insertmacro FindFreeCADInRegistry HKLM 32
  SetRegView 32
  ; Standard installed distributions, including ones without usable registry data.
  FindFirst $2 $3 "$PROGRAMFILES64\FreeCAD*"
fc_find_directory:
  StrCmp $3 "" fc_find_done
  StrCpy $FcCandidate "$PROGRAMFILES64\$3\bin\FreeCAD.exe"
  Call TryFreeCAD
  FindNext $2 $3
  Goto fc_find_directory
fc_find_done:
  FindClose $2
FunctionEnd

Function FcCheckSelection
  ${NSD_GetText} $FcEdit $FcCandidate
  Call ProbeFreeCAD
  StrCmp $FcProbeError "" fc_selection_ok
  StrCpy $FcExe ""
  StrCpy $FcVersion ""
  ${NSD_SetText} $FcStatus "$FcProbeError"
  Return
fc_selection_ok:
  StrCpy $FcExe $FcCandidate
  StrCpy $FcVersion $FcProbeVersion
  ${NSD_SetText} $FcEdit "$FcExe"
  ${NSD_SetText} $FcStatus "$(FcReady)"
FunctionEnd

Function FcCheckClick
  Pop $0
  Call FcCheckSelection
FunctionEnd

Function FcBrowseClick
  Pop $0
  nsDialogs::SelectFileDialog open "$FcExe" "FreeCAD.exe|FreeCAD.exe"
  Pop $0
  StrCmp $0 "" fc_browse_done
  ${NSD_SetText} $FcEdit "$0"
  Call FcCheckSelection
fc_browse_done:
FunctionEnd

Function FcDownloadClick
  Pop $0
  ExecShell "open" "https://www.freecad.org/downloads.php"
FunctionEnd

Function FreeCADPage
  !insertmacro MUI_HEADER_TEXT "$(FcTitle)" "$(FcHelp)"
  nsDialogs::Create 1018
  Pop $0
  ${NSD_CreateLabel} 0 0 100% 28u "$(FcAccount)"
  Pop $0
  ${NSD_CreateFileRequest} 0 36u 78% 14u "$FcExe"
  Pop $FcEdit
  ${NSD_CreateBrowseButton} 80% 36u 20% 14u "$(FcBrowse)"
  Pop $0
  ${NSD_OnClick} $0 FcBrowseClick
  ${NSD_CreateButton} 0 57u 28% 16u "$(FcCheck)"
  Pop $0
  ${NSD_OnClick} $0 FcCheckClick
  ${NSD_CreateLabel} 0 83u 100% 48u "$(FcChoose)"
  Pop $FcStatus
  ${NSD_CreateLink} 0 141u 100% 16u "$(FcDownload)"
  Pop $0
  ${NSD_OnClick} $0 FcDownloadClick
  StrCmp $FcExe "" fc_page_missing
  ${NSD_SetText} $FcStatus "$(FcReady)"
  Goto fc_page_show
fc_page_missing:
  ${If} $FcLastCandidate != ""
    ${NSD_SetText} $FcEdit "$FcLastCandidate"
    ${NSD_SetText} $FcStatus "$FcLastError"
  ${EndIf}
  MessageBox MB_YESNO|MB_ICONQUESTION|MB_DEFBUTTON2 "$(FcMissing)" IDYES fc_page_show
  Quit
fc_page_show:
  nsDialogs::Show
FunctionEnd

Function FreeCADPageLeave
  Call FcCheckSelection
  StrCmp $FcExe "" 0 fc_page_valid
  MessageBox MB_ICONSTOP "$FcProbeError"
  Abort
fc_page_valid:
FunctionEnd
