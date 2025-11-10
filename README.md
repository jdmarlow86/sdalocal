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
2. Clone the repository and open a terminal in the project folder.
3. Launch the application:

   ```bash
   python -m sda_local.app
   ```

The application window will open with dedicated tabs for each functional
area. Data is automatically saved when the window closes.

## Development notes

- The code lives in `sda_local/app.py` with supporting models and
  widgets grouped by feature.
- No external dependencies are required beyond the Python standard
  library.
- Data is saved under `sda_local/data/sdalocal_data.json`. Delete this
  file to reset the application state.
