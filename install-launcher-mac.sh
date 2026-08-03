#!/usr/bin/env bash
# Installs Run Tracker as a proper macOS .app bundle in ~/Applications,
# so it can be dragged to the Dock like any other app.
set -e

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Run Tracker.app"
DEST="$HOME/Applications/$APP_NAME"

mkdir -p "$DEST/Contents/MacOS" "$DEST/Contents/Resources"

# Icon: prefer a prebuilt .icns if present, otherwise fall back to the PNG.
if [ -f "$APP_DIR/icons/running_icon.icns" ]; then
    cp "$APP_DIR/icons/running_icon.icns" "$DEST/Contents/Resources/AppIcon.icns"
    ICON_LINE="<key>CFBundleIconFile</key><string>AppIcon</string>"
else
    ICON_LINE=""
fi

cat > "$DEST/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key><string>Run Tracker</string>
    <key>CFBundleDisplayName</key><string>Run Tracker</string>
    <key>CFBundleIdentifier</key><string>com.runtracker.app</string>
    <key>CFBundleVersion</key><string>1.0</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleExecutable</key><string>run-tracker-launcher</string>
    $ICON_LINE
    <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF

cat > "$DEST/Contents/MacOS/run-tracker-launcher" << EOF
#!/usr/bin/env bash
cd "$APP_DIR"
python3 "$APP_DIR/Run.py"
EOF

chmod +x "$DEST/Contents/MacOS/run-tracker-launcher"

echo "Installed: $DEST"
echo "Open Finder -> Applications (or your Home folder's Applications), find 'Run Tracker',"
echo "then drag it onto the Dock to pin it there."
