# 🏃 Run Tracker & Analytics

A lightweight desktop app for logging runs and visualizing your progress — built with Python, [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), and Matplotlib.

![Run Tracker icon](icons/running_icon.png)

## Features

- **Log runs** — date, distance, time, incline, and calories burned, with a built-in calendar date picker
- **Editable history table** — edit or delete any past run inline
- **Filter by month** — quickly narrow the table down to a specific month
- **Analytics dashboard** — auto-generated charts for distance, pace, calories, and incline over time, with hover tooltips showing exact values
- **Summary cards** — totals for this week, this month, and all-time at a glance
- **Fast & lightweight** — table rows and dialogs use plain Tkinter widgets under the hood for snappy add/edit/delete, and heavier libraries (Matplotlib) only load when you open the Analytics tab
- **Local-only data** — everything is stored in a local `runs.json` file; nothing leaves your machine

## Screenshots

*(Add a screenshot or two here once you have some — drag an image into this README on GitHub, or place it in the repo and reference it like the icon above.)*

## Requirements

- Python 3.10+
- [Tkinter](https://docs.python.org/3/library/tkinter.html) — bundled by default with Python on Windows and macOS (official python.org installers). On Linux, install it separately: `sudo apt install python3-tk` (Debian/Ubuntu) or your distro's equivalent.

## Installation

```bash
git clone https://github.com/charithsreddy2404-crypto/run-tracker.git
cd run-tracker

pip install customtkinter matplotlib
```

> On some Linux systems (externally-managed Python environments) you may need:
> ```bash
> pip install customtkinter matplotlib --break-system-packages
> ```
> or install via apt instead: `sudo apt install python3-matplotlib python3-numpy`

## Usage

```bash
python3 Run.py
```

On first run, if no `runs.json` exists yet, the app seeds itself with a few sample entries so the table and charts aren't empty. You can rename `runs.example.json` to `runs.json` for a starting template, or just start logging — the file is created automatically.

### Adding a run
Fill in the fields on the left panel (use the 📅 button for a quick date picker) and click **Save Run Log**.

### Editing or deleting a run
Use the **Edit** / **Delete** buttons on any row in the table.

### Viewing analytics
Switch to the **Analytics Dashboard** tab for charts and summary stats. Use the segmented control to switch between All Time / This Month / This Week.

## Running it from your taskbar / dock / Start Menu

Install scripts are included for all three major platforms. Each one auto-detects where you cloned the repo, so there's nothing to edit by hand.

### Linux
```bash
chmod +x install-launcher.sh
./install-launcher.sh
```
Then search for **"Run Tracker"** in your app menu (Activities/Start), right-click it, and choose **Add to Favorites** (or your desktop environment's equivalent) to pin it to the taskbar/dock.

Prefer to set it up manually? `run-tracker.desktop.template` shows the file format — copy it to `~/.local/share/applications/run-tracker.desktop`, replace the `/path/to/run-tracker` placeholders with your actual clone location, then run `update-desktop-database ~/.local/share/applications`.

### macOS
```bash
chmod +x install-launcher-mac.sh
./install-launcher-mac.sh
```
This builds a proper `Run Tracker.app` bundle in `~/Applications`. Open it in Finder and drag it onto the Dock to pin it.

### Windows
Open PowerShell in the cloned folder and run:
```powershell
powershell -ExecutionPolicy Bypass -File install-launcher.ps1
```
This creates shortcuts on your Desktop and in the Start Menu. To pin it to the taskbar, right-click either shortcut and choose **Pin to taskbar**.

> Requires Python installed from [python.org](https://www.python.org/downloads/) with "Add python.exe to PATH" checked during setup.

## Project structure

```
run-tracker/
├── Run.py                          # Main application
├── runs.example.json               # Sample data format (your real runs.json is gitignored)
├── icons/
│   ├── running_icon.png            # App icon (Linux / general use)
│   ├── running_icon.ico            # App icon (Windows)
│   └── running_icon.icns           # App icon (macOS)
├── install-launcher.sh             # Taskbar/app-menu launcher installer (Linux)
├── install-launcher-mac.sh         # Dock launcher installer (macOS)
├── install-launcher.ps1            # Desktop/Start Menu shortcut installer (Windows)
└── run-tracker.desktop.template    # Reference .desktop file for manual Linux setup
```

## Data format

Each run is stored as a simple JSON object:

```json
{
  "date": "17 July",
  "distance": "2km",
  "time": "17min 25sec",
  "incline": "1%",
  "calories": "130 kcal"
}
```

## License

Personal project — feel free to fork and adapt for your own use.
