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
- **Local-only data** — everything is stored in a hidden, obfuscated `.runs.dat` file next to the script; nothing leaves your machine

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

On first run, the app seeds itself with a few sample entries so the table and charts aren't empty, and creates `.runs.dat` (hidden) to store your real data from then on. `runs.example.json` is not read by the app — it's included purely as a reference for the data structure (see **Data format** below).

### Adding a run
Fill in the fields on the left panel (use the 📅 button for a quick date picker) and click **Save Run Log**.

### Editing or deleting a run
Use the **Edit** / **Delete** buttons on any row in the table.

### Viewing analytics
Switch to the **Analytics Dashboard** tab for charts and summary stats. Use the segmented control to switch between All Time / This Month / This Week.

## Running it from your taskbar / dock / Start Menu

One installer, one command, on any of the three platforms:

```bash
python3 install.py
```

It detects your OS automatically and does the right thing:
- **Linux** — installs a launcher to your app menu. Search **"Run Tracker"** in Activities/Start, right-click it, and choose **Add to Favorites** (or your desktop environment's equivalent) to pin it to the taskbar/dock.
- **macOS** — builds a proper `Run Tracker.app` bundle in `~/Applications`. Open it in Finder and drag it onto the Dock to pin it.
- **Windows** — creates shortcuts on your Desktop and in the Start Menu. Right-click either one and choose **Pin to taskbar**. (Requires Python installed from [python.org](https://www.python.org/downloads/) with "Add python.exe to PATH" checked during setup.)

Linux users who'd rather set it up manually: `run-tracker.desktop.template` shows the file format — copy it to `~/.local/share/applications/run-tracker.desktop`, replace the `/path/to/run-tracker` placeholders with your actual clone location, then run `update-desktop-database ~/.local/share/applications`.

## Project structure

```
run-tracker/
├── Run.py                          # Main application
├── runs.example.json               # Reference only — shows the data structure (see Data format below); not read by the app
├── icons/
│   ├── running_icon.png            # App icon (Linux / general use)
│   ├── running_icon.ico            # App icon (Windows)
│   └── running_icon.icns           # App icon (macOS)
├── install.py                      # Launcher installer for Linux, macOS, and Windows (auto-detects OS)
└── run-tracker.desktop.template    # Reference .desktop file for manual Linux setup
```

## Data format

Your actual run data is stored in a hidden file, `.runs.dat`, next to `Run.py`. It's base64-obfuscated on disk — not plain readable text, and not tracked by git — so it won't show up in normal folder browsing and won't accidentally get committed.

`runs.example.json` (tracked in this repo) shows the underlying data structure for reference — each run is logically a simple object like this, even though it isn't stored in this exact plain-text form:

```json
{
  "date": "17 July",
  "distance": "2km",
  "time": "17min 25sec",
  "incline": "1%",
  "calories": "130 kcal"
}
```

> Note: `.runs.dat` obfuscation deters casual viewing (e.g. someone browsing your files), but it is **not encryption** — anyone who knows the format can decode it. If you need real protection, that would require password-based encryption, which isn't implemented here.

## License

Personal project — feel free to fork and adapt for your own use.
