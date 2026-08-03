# Installs a Desktop and Start Menu shortcut for Run Tracker on Windows.
# Run this from PowerShell inside the cloned repo folder:
#   powershell -ExecutionPolicy Bypass -File install-launcher.ps1

$AppDir = $PSScriptRoot
$IconPath = Join-Path $AppDir "icons\running_icon.ico"
$ScriptPath = Join-Path $AppDir "Run.py"

# Prefer pythonw.exe (runs without a console window); fall back to python.exe
$PythonExe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    $PythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
}
if (-not $PythonExe) {
    Write-Host "Could not find python.exe or pythonw.exe on PATH. Install Python from python.org first (check 'Add python.exe to PATH' during setup)." -ForegroundColor Red
    exit 1
}

$WshShell = New-Object -ComObject WScript.Shell

function New-AppShortcut($path) {
    $Shortcut = $WshShell.CreateShortcut($path)
    $Shortcut.TargetPath = $PythonExe
    $Shortcut.Arguments = "`"$ScriptPath`""
    $Shortcut.WorkingDirectory = $AppDir
    if (Test-Path $IconPath) {
        $Shortcut.IconLocation = $IconPath
    }
    $Shortcut.Description = "Run Tracker & Analytics"
    $Shortcut.Save()
}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$StartMenuPath = [Environment]::GetFolderPath("Programs")

New-AppShortcut (Join-Path $DesktopPath "Run Tracker.lnk")
New-AppShortcut (Join-Path $StartMenuPath "Run Tracker.lnk")

Write-Host "Shortcuts created on your Desktop and in the Start Menu."
Write-Host "To pin to the taskbar: right-click the Desktop shortcut (or find 'Run Tracker' in the Start Menu) and choose 'Pin to taskbar'."
