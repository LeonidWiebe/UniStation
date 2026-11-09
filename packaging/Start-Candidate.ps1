# User-invoked visible session for a separate, marked candidate profile.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$FreeCADExe,
    [string]$ProfileDirectory
)
$ErrorActionPreference = 'Stop'
$candidateRoot = $PSScriptRoot
$freecadPath = (Resolve-Path -LiteralPath $FreeCADExe).Path
if (-not (Test-Path -LiteralPath $freecadPath -PathType Leaf)) { throw 'FreeCAD executable not found.' }
if ([System.IO.Path]::GetFileName($freecadPath) -ine 'FreeCAD.exe') { throw 'Choose the FreeCAD.exe executable.' }
if (@(Get-Process -Name FreeCAD, FreeCADCmd -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'Close the existing FreeCAD window yourself before starting the candidate.'
}
$axisflowPath = Join-Path $candidateRoot 'Mod\AxisFlow'
$unistationPath = Join-Path $candidateRoot 'Mod\UniStation'
foreach ($modulePath in @($axisflowPath, $unistationPath)) {
    if (-not (Test-Path -LiteralPath (Join-Path $modulePath 'InitGui.py') -PathType Leaf)) {
        throw "Candidate module missing: $modulePath"
    }
}
if (-not $ProfileDirectory) { $ProfileDirectory = Join-Path $candidateRoot 'candidate-profile' }
$profilePath = [System.IO.Path]::GetFullPath($ProfileDirectory)
$markerPath = Join-Path $profilePath 'unistation-candidate-profile.json'
if (Test-Path -LiteralPath $profilePath) {
    if (-not (Test-Path -LiteralPath $profilePath -PathType Container)) { throw 'Profile path is not a directory.' }
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
        if (@(Get-ChildItem -LiteralPath $profilePath -Force).Count -gt 0) {
            throw 'Existing nonempty directory is not a marked candidate profile. Choose a new directory.'
        }
    }
    else {
        $profileMarker = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($profileMarker.kind -ne 'UniStation installation candidate') { throw 'Wrong profile marker.' }
    }
}
New-Item -ItemType Directory -Path $profilePath -Force | Out-Null
if (-not (Test-Path -LiteralPath $markerPath)) {
    @{kind='UniStation installation candidate'; version='0.1.0-alpha.2'} |
        ConvertTo-Json | Set-Content -LiteralPath $markerPath -Encoding UTF8
}
$logDirectory = Join-Path $profilePath 'logs'
$temporaryDirectory = Join-Path $profilePath 'temp'
New-Item -ItemType Directory -Path $logDirectory, $temporaryDirectory -Force | Out-Null
$userConfig = Join-Path $profilePath 'user.cfg'
$systemConfig = Join-Path $profilePath 'system.cfg'
$logFile = Join-Path $logDirectory ('freecad-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.log')
$macroPath = Join-Path $candidateRoot 'start-candidate.FCMacro'
if (-not (Test-Path -LiteralPath $macroPath -PathType Leaf)) { throw 'Startup macro missing.' }
$environmentNames = @('FREECAD_USER_HOME', 'FREECAD_USER_DATA', 'FREECAD_USER_TEMP')
$previousEnvironment = @{}
foreach ($environmentName in $environmentNames) {
    $previousEnvironment[$environmentName] = [Environment]::GetEnvironmentVariable($environmentName, 'Process')
}
try {
    $env:FREECAD_USER_HOME = $profilePath
    # AxisFlow locates resources via getUserAppDataDir()/Mod/AxisFlow.
    # Keep user data at this extracted candidate root, where Mod already lives.
    $env:FREECAD_USER_DATA = $candidateRoot
    $env:FREECAD_USER_TEMP = $temporaryDirectory
    $candidateProcess = Start-Process -FilePath $freecadPath -ArgumentList @(
        '-u', "`"$userConfig`"", '-s', "`"$systemConfig`"",
        '--log-file', "`"$logFile`"", "`"$macroPath`""
    ) -WorkingDirectory $candidateRoot -WindowStyle Normal -PassThru
    Write-Output "Candidate started. PID: $($candidateProcess.Id)"
    Write-Output "Separate profile: $profilePath"
    Write-Output "Log: $logFile"
}
finally {
    foreach ($environmentName in $environmentNames) {
        [Environment]::SetEnvironmentVariable($environmentName, $previousEnvironment[$environmentName], 'Process')
    }
}
