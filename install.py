#!/usr/bin/env python3
"""
Installs a Run Tracker launcher for whichever OS you're running this on.
One script, all three platforms — Python itself detects the OS and does
the right thing, so there's nothing else to pick or run separately.

Usage (same command everywhere):
    python3 install.py
"""

import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent


def install_linux():
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "run-tracker.desktop"
    icon_path = APP_DIR / "icons" / "running_icon.png"

    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Run Tracker
Comment=Run Tracker & Analytics
Exec=python3 {APP_DIR / 'Run.py'}
Path={APP_DIR}
Icon={icon_path}
Terminal=false
Categories=Utility;
StartupNotify=true
"""
    desktop_file.write_text(content)
    desktop_file.chmod(0o755)

    try:
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        )
    except FileNotFoundError:
        pass  # not present on all distros; the .desktop file itself is still valid without it

    print(f"Installed launcher: {desktop_file}")
    print("Search for 'Run Tracker' in your app menu, then right-click it and choose")
    print("'Add to Favorites' (or your desktop's equivalent) to pin it to the taskbar/dock.")


def install_macos():
    dest = Path.home() / "Applications" / "Run Tracker.app"
    (dest / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
    (dest / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)

    icns_src = APP_DIR / "icons" / "running_icon.icns"
    icon_line = ""
    if icns_src.exists():
        icon_dest = dest / "Contents" / "Resources" / "AppIcon.icns"
        icon_dest.write_bytes(icns_src.read_bytes())
        icon_line = "<key>CFBundleIconFile</key><string>AppIcon</string>"

    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>Run Tracker</string>
    <key>CFBundleDisplayName</key><string>Run Tracker</string>
    <key>CFBundleIdentifier</key><string>com.runtracker.app</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleExecutable</key><string>run-tracker-launcher</string>
    {icon_line}
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
"""
    (dest / "Contents" / "Info.plist").write_text(plist)

    launcher = f"""#!/usr/bin/env bash
cd "{APP_DIR}"
python3 "{APP_DIR / 'Run.py'}"
"""
    launcher_path = dest / "Contents" / "MacOS" / "run-tracker-launcher"
    launcher_path.write_text(launcher)
    launcher_path.chmod(0o755)

    print(f"Installed: {dest}")
    print("Open Finder -> Applications (in your Home folder), find 'Run Tracker',")
    print("then drag it onto the Dock to pin it there.")


def install_windows():
    icon_path = APP_DIR / "icons" / "running_icon.ico"
    script_path = APP_DIR / "Run.py"

    # Creating a real .lnk shortcut (with a working icon) needs Windows'
    # own shortcut APIs, which Python's standard library doesn't expose.
    # Rather than requiring an extra pip package, this shells out to
    # PowerShell (present on every Windows install) to do just that part.
    ps_script = f'''
$AppDir = "{APP_DIR}"
$IconPath = "{icon_path}"
$ScriptPath = "{script_path}"

$PythonExe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {{
    $PythonExe = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
}}
if (-not $PythonExe) {{
    Write-Host "Could not find python.exe or pythonw.exe on PATH. Install Python from python.org first (check 'Add python.exe to PATH' during setup)." -ForegroundColor Red
    exit 1
}}

$WshShell = New-Object -ComObject WScript.Shell

function New-AppShortcut($path) {{
    $Shortcut = $WshShell.CreateShortcut($path)
    $Shortcut.TargetPath = $PythonExe
    $Shortcut.Arguments = "`"$ScriptPath`""
    $Shortcut.WorkingDirectory = $AppDir
    if (Test-Path $IconPath) {{
        $Shortcut.IconLocation = $IconPath
    }}
    $Shortcut.Description = "Run Tracker & Analytics"
    $Shortcut.Save()
}}

$DesktopPath = [Environment]::GetFolderPath("Desktop")
$StartMenuPath = [Environment]::GetFolderPath("Programs")

New-AppShortcut (Join-Path $DesktopPath "Run Tracker.lnk")
New-AppShortcut (Join-Path $StartMenuPath "Run Tracker.lnk")

Write-Host "Shortcuts created on your Desktop and in the Start Menu."
Write-Host "To pin to the taskbar: right-click either shortcut and choose 'Pin to taskbar'."
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ps1", delete=False) as f:
        f.write(ps_script)
        temp_ps1 = f.name

    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", temp_ps1],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
    finally:
        os.unlink(temp_ps1)


def main():
    system = platform.system()

    if system == "Linux":
        install_linux()
    elif system == "Darwin":
        install_macos()
    elif system == "Windows":
        install_windows()
    else:
        print(f"Unrecognized OS: {system}. This installer supports Linux, macOS, and Windows.")
        sys.exit(1)


if __name__ == "__main__":
    main()
