# 🏃 Running Tracker & Analytics

A lightweight desktop app for logging runs and visualizing your progress — built with Python, [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), and Matplotlib.

![Running Tracker icon](running_iconF.png)

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
- [Tkinter](https://docs.python.org/3/library/tkinter.html) (usually bundled with Python; on Ubuntu/Debian: `sudo apt install python3-tk`)

## Installation

```bash
git clone https://github.com/charithsreddy2404-crypto/running-tracker.git
cd running-tracker

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

## Running it from your taskbar (Linux)

A sample `.desktop` launcher setup is described in this repo's history — create a file like this (update the paths for your system) and place it at `~/.local/share/applications/running-tracker.desktop`:

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=Running Tracker
Comment=Running Tracker & Analytics
Exec=python3 /path/to/running-tracker/Run.py
Path=/path/to/running-tracker
Icon=/path/to/running-tracker/running_iconF.png
Terminal=false
Categories=Utility;
StartupNotify=true
```

Then run `update-desktop-database ~/.local/share/applications` and search for "Running Tracker" in your app menu — right-click to pin it to your taskbar/dock.

## Project structure

```
running-tracker/
├── Run.py                  # Main application
├── runs.example.json       # Sample data format (your real runs.json is gitignored)
└── running_iconF.png       # App icon
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
