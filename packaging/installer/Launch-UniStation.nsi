; Small native current-user launcher. No shell script or profile configuration writes.
Unicode true
RequestExecutionLevel user
ManifestDPIAware true
SilentInstall silent
AutoCloseWindow true
SetCompressor /SOLID lzma
Name "UniStation"
OutFile "${OUTFILE}"
Icon "${__FILEDIR__}\unistation.ico"
VIProductVersion "${FILEVERSION}"
VIAddVersionKey "ProductName" "UniStation launcher"
VIAddVersionKey "FileVersion" "${FILEVERSION}"
VIAddVersionKey "FileDescription" "Start FreeCAD with the UniStation workbench"
VIAddVersionKey "LegalCopyright" "UniStation contributors; GPL-3.0-only"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
Var ModRoot
Var DataRoot
Var FreeCADExe
Var UserProfile

Function .onInit
  SetErrorLevel 2
  SetShellVarContext current
  ${GetParent} "$EXEDIR" $ModRoot
  ReadINIStr $0 "$EXEDIR\state.ini" "Install" "Owner"
  ReadINIStr $1 "$EXEDIR\state.ini" "Install" "Root"
  ReadINIStr $2 "$EXEDIR\state.ini" "Managed" "UniStation"
  ${If} $0 != "UniStation.WindowsInstaller"
  ${OrIf} $1 != $ModRoot
  ${OrIf} $2 != 1
    MessageBox MB_ICONSTOP "UniStation is not installed here. / UniStation здесь не установлен."
    Quit
  ${EndIf}
  ReadINIStr $UserProfile "$EXEDIR\state.ini" "Launch" "UserProfile"
  ${If} $UserProfile != $PROFILE
    MessageBox MB_ICONSTOP "Run UniStation using the Windows account that installed it, or install it for this account.$\r$\n$\r$\nЗапустите UniStation под учётной записью Windows, выполнившей установку, либо установите его для этой учётной записи."
    Quit
  ${EndIf}
  ReadINIStr $FreeCADExe "$EXEDIR\state.ini" "Launch" "FreeCADExe"
  IfFileExists "$FreeCADExe" 0 launch_missing
  IfFileExists "$EXEDIR\Start-UniStation.FCMacro" 0 launch_missing
  IfFileExists "$ModRoot\UniStation\InitGui.py" 0 launch_missing
  IfFileExists "$ModRoot\AxisFlow\InitGui.py" 0 launch_missing
  ${GetFileName} "$ModRoot" $0
  StrCmp $0 "Mod" 0 launch_missing
  ${GetParent} "$ModRoot" $DataRoot
  ; Only the child process environment changes. Keep this account's user.cfg.
  System::Call 'kernel32::SetEnvironmentVariableW(w "FREECAD_USER_DATA", w "$DataRoot") i .r0'
  StrCmp $0 0 launch_missing
  System::Call 'kernel32::SetEnvironmentVariableW(w "USTN_INSTALLER_MOD_ROOT", w "$ModRoot") i .r0'
  StrCmp $0 0 launch_missing
  ${GetParent} "$FreeCADExe" $0
  SetOutPath "$0"
  ClearErrors
  ; No --single-instance: always start the selected binary with its startup macro.
  Exec '"$FreeCADExe" "$EXEDIR\Start-UniStation.FCMacro"'
  IfErrors launch_missing
  SetErrorLevel 0
  Quit
launch_missing:
  MessageBox MB_ICONSTOP "The configured FreeCAD or UniStation installation is unavailable. Run UniStation setup again.$\r$\n$\r$\nВыбранный FreeCAD или файлы UniStation недоступны. Повторите установку UniStation."
  Quit
FunctionEnd

Section
SectionEnd
