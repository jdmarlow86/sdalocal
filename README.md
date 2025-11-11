# sdaLocal Desktop Application

sdaLocal is a Windows-friendly desktop application that supports ministry
and church administration tasks. The graphical interface is built with
Python's Tkinter toolkit so it can run on Windows without additional
frameworks.

## Features

- **Bulletin event creation** – capture event title, date, and details,
  then review the upcoming bulletin through an interactive list.
- **Income and expense management** – log financial transactions,
  categorize funds, and view real-time income, expense, and balance
  summaries.
- **Media and chat hub** – quickly launch livestream or prerecorded video
  content and maintain an internal chat log for team collaboration.
- **Building project management** – add, update, and track project
  progress, budgets, and descriptions for church building initiatives.

All information is stored locally in JSON so reopening the app restores
previous activity.

## Getting started

1. Ensure Python 3.9+ is installed on Windows.
2. (Optional) Create and activate a virtual environment so the project
   runs in isolation:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. Clone the repository and open a terminal in the project folder.
4. Install project dependencies if a `requirements.txt` file is
   available. The application only relies on the Python standard library
   today, so there is nothing additional to install on a fresh clone.

5. Launch the application:

   ```bash
   python -m sda_local.app
   ```

The application window will open with dedicated tabs for each functional
area. Data is automatically saved when the window closes.

## Building a Windows executable

An installer script is provided to bundle the application into a
Windows-friendly `.exe` file using [PyInstaller](https://pyinstaller.org/).

1. Install PyInstaller in your environment:

   ```bash
   pip install pyinstaller
   ```

2. Run the build helper from the project root:

   ```bash
   python installer/build_exe.py
   ```

   The script removes any previous `build/` and `dist/` folders before
   invoking PyInstaller in one-file, windowed mode. When it finishes an
   executable named `sdaLocal.exe` will be available in `dist/`.

3. (Optional) To create a folder-based distribution instead of a single
   executable, add the `--onedir` flag:

   ```bash
   python installer/build_exe.py --onedir
   ```

The generated executable stores its data under the user's application
data directory (for example `%APPDATA%\sdaLocal` on Windows) so state is
preserved across launches.

## Development notes

- The code lives in `sda_local/app.py` with supporting models and
  widgets grouped by feature.
- No external dependencies are required beyond the Python standard
  library.
- Data is saved under `sda_local/data/sdalocal_data.json`. Delete this
  file to reset the application state.
