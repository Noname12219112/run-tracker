#!/usr/bin/env bash
# Installs a taskbar/app-menu launcher for Run Tracker.
# Works regardless of your username or where you cloned this repo,
# because it detects its own location and writes the correct absolute
# paths into the .desktop file for you.
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/run-tracker.desktop"
ICON_PATH="$APP_DIR/icons/running_icon.png"

mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Run Tracker
Comment=Run Tracker & Analytics
Exec=python3 $APP_DIR/Run.py
Path=$APP_DIR
Icon=$ICON_PATH
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo "Installed launcher: $DESKTOP_FILE"
echo "Search for 'Run Tracker' in your app menu, then right-click it and choose"
echo "'Add to Favorites' (or your desktop's equivalent) to pin it to the taskbar/dock."
