"""sdaLocal Windows desktop style application built with Tkinter.

The application provides the following features:

* Bulletin event management with quick entry and detail view.
* Income and expense tracking with summaries of balances.
* Lightweight video launching and internal chat logging to support
  ministry communication.
* Building project management for keeping an eye on construction
  progress.
"""

from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any, Dict, List
import webbrowser

from tkinter import ttk



def _determine_data_dir() -> Path:
    """Return the directory where persistent application data is stored."""

    if getattr(sys, "frozen", False):  # Running from a bundled executable.
        app_folder = "sdaLocal"
        if sys.platform.startswith("win"):
            base_dir = Path(os.environ.get("APPDATA", Path.home()))
        elif sys.platform == "darwin":
            base_dir = Path.home() / "Library" / "Application Support"
        else:
            base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        return base_dir / app_folder

    return Path(__file__).resolve().parent / "data"


DATA_DIR = _determine_data_dir()
DATA_FILE = DATA_DIR / "sdalocal_data.json"


@dataclass
class Event:
    """Data model representing a bulletin event."""

    title: str
    date: str
    description: str


@dataclass
class FinanceEntry:
    """Data model representing a financial record."""

    entry_type: str
    amount: float
    category: str
    note: str
    created_at: str


@dataclass
class Project:
    """Data model representing a church building project."""

    name: str
    manager: str
    start_date: str
    end_date: str
    budget: float
    status: str
    description: str


class SDALocalApp(tk.Tk):
    """Main application window for the sdaLocal desktop experience."""

    def __init__(self) -> None:
        super().__init__()
        self.title("sdaLocal")
        self.geometry("1000x700")
        self.minsize(900, 600)

        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")
        self.dark_mode = tk.BooleanVar(value=False)
        self._text_widgets: List[tk.Text] = []
        self._light_palette = {
            "background": "#f0f0f0",
            "frame": "#ffffff",
            "foreground": "#202020",
            "input": "#ffffff",
            "input_fg": "#202020",
            "accent": "#2c6bed",
            "tree_background": "#ffffff",
            "tree_field": "#f5f5f5",
            "tree_foreground": "#202020",
            "border": "#cccccc",
        }
        self._dark_palette = {
            "background": "#1e1e1e",
            "frame": "#2b2b2b",
            "foreground": "#f5f5f5",
            "input": "#3c3c3c",
            "input_fg": "#f5f5f5",
            "accent": "#3b82f6",
            "tree_background": "#2b2b2b",
            "tree_field": "#1f1f1f",
            "tree_foreground": "#f5f5f5",
            "border": "#4a4a4a",
        }

        self._setup_custom_themes()

        self.data: Dict[str, List[Dict[str, Any]]] = {
            "events": [],
            "finance": [],
            "projects": [],
            "chat": [],
        }
        self._load_data()

        self._create_menubar()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._build_events_tab()
        self._build_finance_tab()
        self._build_media_tab()
        self._build_projects_tab()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._apply_theme()

    # ------------------------------------------------------------------
    # Data handling
    # ------------------------------------------------------------------
    def _load_data(self) -> None:
        if DATA_FILE.exists():
            try:
                self.data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                messagebox.showwarning(
                    "Data error",
                    "Existing data file is corrupted. Starting with a fresh set of records.",
                )
                self.data = {"events": [], "finance": [], "projects": [], "chat": []}

    def _save_data(self) -> None:
        DATA_FILE.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def _on_close(self) -> None:
        self._save_data()
        self.destroy()

    # ------------------------------------------------------------------
    # Bulletin events tab
    # ------------------------------------------------------------------
    def _build_events_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Bulletin Events")

        form_frame = ttk.LabelFrame(tab, text="Create Event")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form_frame, text="Title").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.event_title = ttk.Entry(form_frame)
        self.event_title.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(form_frame, text="Date (YYYY-MM-DD)").grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        self.event_date = ttk.Entry(form_frame)
        self.event_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.event_date.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(form_frame, text="Description").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)
        self.event_description = tk.Text(form_frame, height=4)
        self._register_text_widget(self.event_description)
        self.event_description.grid(row=1, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=5)

        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=2, column=0, columnspan=4, sticky=tk.E, padx=5, pady=5)
        ttk.Button(button_frame, text="Add Event", command=self._add_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Selected", command=self._delete_event).pack(
            side=tk.LEFT, padx=5
        )

        list_frame = ttk.LabelFrame(tab, text="Upcoming Bulletin")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("date", "title")
        self.events_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.events_tree.heading("date", text="Date")
        self.events_tree.heading("title", text="Title")
        self.events_tree.column("date", width=120)
        self.events_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.events_tree.bind("<<TreeviewSelect>>", self._show_event_details)

        self.event_details = tk.Text(list_frame, height=6, state=tk.DISABLED)
        self._register_text_widget(self.event_details)
        self.event_details.pack(fill=tk.X, padx=5, pady=5)

        for event in self.data.get("events", []):
            self._insert_event_row(event)

    def _add_event(self) -> None:
        title = self.event_title.get().strip()
        date_text = self.event_date.get().strip()
        description = self.event_description.get("1.0", tk.END).strip()

        if not title or not date_text:
            messagebox.showerror("Missing Information", "Please provide both title and date for the event.")
            return

        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Date must be in YYYY-MM-DD format.")
            return

        event = asdict(Event(title=title, date=date_text, description=description))
        self.data.setdefault("events", []).append(event)
        self._insert_event_row(event)
        self.event_title.delete(0, tk.END)
        self.event_description.delete("1.0", tk.END)
        self.event_date.delete(0, tk.END)
        self.event_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._save_data()

    def _insert_event_row(self, event: Dict[str, Any]) -> None:
        self.events_tree.insert("", tk.END, values=(event["date"], event["title"]), iid=event["title"] + event["date"])

    def _delete_event(self) -> None:
        selected = self.events_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Please choose an event to delete.")
            return
        iid = selected[0]
        values = self.events_tree.item(iid)["values"]
        self.events_tree.delete(iid)
        self.data["events"] = [event for event in self.data["events"] if not (event["date"] == values[0] and event["title"] == values[1])]
        self.event_details.configure(state=tk.NORMAL)
        self.event_details.delete("1.0", tk.END)
        self.event_details.configure(state=tk.DISABLED)
        self._save_data()

    def _show_event_details(self, _: tk.Event) -> None:
        selected = self.events_tree.selection()
        if not selected:
            return
        iid = selected[0]
        values = self.events_tree.item(iid)["values"]
        for event in self.data.get("events", []):
            if event["date"] == values[0] and event["title"] == values[1]:
                self.event_details.configure(state=tk.NORMAL)
                self.event_details.delete("1.0", tk.END)
                self.event_details.insert(tk.END, f"Title: {event['title']}\nDate: {event['date']}\n\n{event['description']}")
                self.event_details.configure(state=tk.DISABLED)
                break

    # ------------------------------------------------------------------
    # Finance tab
    # ------------------------------------------------------------------
    def _build_finance_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Income & Expenses")

        form_frame = ttk.LabelFrame(tab, text="Log Transaction")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form_frame, text="Type").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.finance_type = ttk.Combobox(form_frame, values=["Income", "Expense"], state="readonly")
        self.finance_type.current(0)
        self.finance_type.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Amount").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.finance_amount = ttk.Entry(form_frame)
        self.finance_amount.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Category").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        categories = ["Tithe", "Offering", "Operations", "Community", "Other"]
        self.finance_category = ttk.Combobox(form_frame, values=categories)
        self.finance_category.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Note").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.finance_note = ttk.Entry(form_frame)
        self.finance_note.grid(row=1, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Button(form_frame, text="Add Entry", command=self._add_finance_entry).grid(
            row=0, column=4, rowspan=2, padx=10, pady=5
        )

        for i in range(4):
            form_frame.columnconfigure(i, weight=1)

        list_frame = ttk.LabelFrame(tab, text="Ledger")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("created_at", "entry_type", "amount", "category", "note")
        self.finance_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        for column, title in zip(columns, ["Date", "Type", "Amount", "Category", "Note"]):
            self.finance_tree.heading(column, text=title)
            self.finance_tree.column(column, width=120 if column != "note" else 200)
        self.finance_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.finance_summary = ttk.Label(tab, text="")
        self.finance_summary.pack(anchor=tk.E, padx=15, pady=(0, 10))

        for entry in self.data.get("finance", []):
            self._insert_finance_row(entry)
        self._update_finance_summary()

    def _add_finance_entry(self) -> None:
        entry_type = self.finance_type.get()
        amount_text = self.finance_amount.get().strip()
        category = self.finance_category.get().strip() or "Uncategorized"
        note = self.finance_note.get().strip()

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showerror("Invalid amount", "Please enter a numeric value for the amount.")
            return

        if amount <= 0:
            messagebox.showerror("Invalid amount", "Amount must be greater than zero.")
            return

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = asdict(
            FinanceEntry(
                entry_type=entry_type,
                amount=amount,
                category=category,
                note=note,
                created_at=created_at,
            )
        )
        self.data.setdefault("finance", []).append(entry)
        self._insert_finance_row(entry)
        self._update_finance_summary()

        self.finance_amount.delete(0, tk.END)
        self.finance_note.delete(0, tk.END)
        self._save_data()

    def _insert_finance_row(self, entry: Dict[str, Any]) -> None:
        display_amount = f"${entry['amount']:.2f}"
        if entry["entry_type"].lower() == "expense":
            display_amount = f"-${entry['amount']:.2f}"
        self.finance_tree.insert(
            "",
            tk.END,
            values=(entry["created_at"], entry["entry_type"], display_amount, entry["category"], entry["note"]),
        )

    def _update_finance_summary(self) -> None:
        income = sum(entry["amount"] for entry in self.data.get("finance", []) if entry["entry_type"] == "Income")
        expenses = sum(
            entry["amount"] for entry in self.data.get("finance", []) if entry["entry_type"].lower() == "expense"
        )
        balance = income - expenses
        summary = f"Income: ${income:.2f}   Expenses: ${expenses:.2f}   Balance: ${balance:.2f}"
        self.finance_summary.configure(text=summary)

    # ------------------------------------------------------------------
    # Media and chat tab
    # ------------------------------------------------------------------
    def _build_media_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Media & Chat")

        media_frame = ttk.LabelFrame(tab, text="Video Broadcast")
        media_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(media_frame, text="Video URL or file path").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.video_entry = ttk.Entry(media_frame)
        self.video_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Button(media_frame, text="Open Video", command=self._open_video).grid(row=0, column=2, padx=5, pady=5)
        media_frame.columnconfigure(1, weight=1)

        chat_frame = ttk.LabelFrame(tab, text="Team Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.chat_display = tk.Text(chat_frame, state=tk.DISABLED, height=12)
        self._register_text_widget(self.chat_display)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        entry_frame = ttk.Frame(chat_frame)
        entry_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.chat_entry = ttk.Entry(entry_frame)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(entry_frame, text="Send", command=self._send_chat_message).pack(side=tk.RIGHT)

        for message in self.data.get("chat", []):
            self._append_chat(message["sender"], message["message"], save=False)

    def _open_video(self) -> None:
        url = self.video_entry.get().strip()
        if not url:
            messagebox.showinfo("Missing information", "Enter a video URL or file path to open.")
            return
        webbrowser.open(url)

    def _send_chat_message(self) -> None:
        message = self.chat_entry.get().strip()
        if not message:
            return
        self._append_chat("You", message)
        self.chat_entry.delete(0, tk.END)
        self.after(300, lambda: self._append_chat("Auto-reply", "Message received. We'll follow up soon!"))

    def _append_chat(self, sender: str, message: str, save: bool = True) -> None:
        timestamp = datetime.now().strftime("%H:%M")
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)
        if save:
            self.data.setdefault("chat", []).append({"sender": sender, "message": message, "timestamp": timestamp})
            self._save_data()

    # ------------------------------------------------------------------
    # Projects tab
    # ------------------------------------------------------------------
    def _build_projects_tab(self) -> None:
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Building Projects")

        form_frame = ttk.LabelFrame(tab, text="Project Details")
        form_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(form_frame, text="Project Name").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.project_name = ttk.Entry(form_frame)
        self.project_name.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Project Manager").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.project_manager = ttk.Entry(form_frame)
        self.project_manager.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Start Date").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.project_start = ttk.Entry(form_frame)
        self.project_start.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.project_start.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="End Date").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.project_end = ttk.Entry(form_frame)
        self.project_end.grid(row=1, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Budget ($)").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.project_budget = ttk.Entry(form_frame)
        self.project_budget.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Status").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        statuses = ["Planned", "In Progress", "On Hold", "Completed"]
        self.project_status = ttk.Combobox(form_frame, values=statuses, state="readonly")
        self.project_status.current(0)
        self.project_status.grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(form_frame, text="Description").grid(row=3, column=0, padx=5, pady=5, sticky=tk.NW)
        self.project_description = tk.Text(form_frame, height=4)
        self._register_text_widget(self.project_description)
        self.project_description.grid(row=3, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=4, column=0, columnspan=4, sticky=tk.E, padx=5, pady=5)
        ttk.Button(button_frame, text="Add Project", command=self._add_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Status", command=self._update_project_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Project", command=self._delete_project).pack(side=tk.LEFT, padx=5)

        for i in range(4):
            form_frame.columnconfigure(i, weight=1)

        list_frame = ttk.LabelFrame(tab, text="Projects Overview")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("name", "status", "start_date", "end_date", "budget")
        self.projects_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        headings = ["Name", "Status", "Start", "End", "Budget"]
        widths = [200, 120, 110, 110, 100]
        for column, heading, width in zip(columns, headings, widths):
            self.projects_tree.heading(column, text=heading)
            self.projects_tree.column(column, width=width)
        self.projects_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.project_details = tk.Text(list_frame, height=6, state=tk.DISABLED)
        self._register_text_widget(self.project_details)
        self.project_details.pack(fill=tk.X, padx=5, pady=5)
        self.projects_tree.bind("<<TreeviewSelect>>", self._show_project_details)

        for project in self.data.get("projects", []):
            self._insert_project_row(project)

    def _add_project(self) -> None:
        name = self.project_name.get().strip()
        manager = self.project_manager.get().strip()
        start_date = self.project_start.get().strip()
        end_date = self.project_end.get().strip()
        budget_text = self.project_budget.get().strip() or "0"
        status = self.project_status.get()
        description = self.project_description.get("1.0", tk.END).strip()

        if not name:
            messagebox.showerror("Missing information", "Project name is required.")
            return

        try:
            budget = float(budget_text)
        except ValueError:
            messagebox.showerror("Invalid budget", "Budget must be a number.")
            return

        project = asdict(
            Project(
                name=name,
                manager=manager,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                status=status,
                description=description,
            )
        )
        self.data.setdefault("projects", []).append(project)
        self._insert_project_row(project)
        self._save_data()

        self.project_name.delete(0, tk.END)
        self.project_manager.delete(0, tk.END)
        self.project_start.delete(0, tk.END)
        self.project_end.delete(0, tk.END)
        self.project_budget.delete(0, tk.END)
        self.project_description.delete("1.0", tk.END)
        self.project_status.current(0)
        self.project_start.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def _insert_project_row(self, project: Dict[str, Any]) -> None:
        self.projects_tree.insert(
            "",
            tk.END,
            iid=project["name"],
            values=(
                project["name"],
                project["status"],
                project["start_date"],
                project.get("end_date", ""),
                f"${project['budget']:.2f}",
            ),
        )

    def _show_project_details(self, _: tk.Event) -> None:
        selected = self.projects_tree.selection()
        if not selected:
            return
        iid = selected[0]
        project = next((p for p in self.data.get("projects", []) if p["name"] == iid), None)
        if not project:
            return
        self.project_details.configure(state=tk.NORMAL)
        self.project_details.delete("1.0", tk.END)
        details = (
            f"Project: {project['name']}\n"
            f"Manager: {project['manager']}\n"
            f"Timeline: {project['start_date']} - {project.get('end_date', '')}\n"
            f"Budget: ${project['budget']:.2f}\n"
            f"Status: {project['status']}\n\n"
            f"{project['description']}"
        )
        self.project_details.insert(tk.END, details)
        self.project_details.configure(state=tk.DISABLED)

    def _update_project_status(self) -> None:
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a project to update.")
            return
        iid = selected[0]
        project = next((p for p in self.data.get("projects", []) if p["name"] == iid), None)
        if not project:
            messagebox.showerror("Missing project", "Selected project could not be found.")
            return
        new_status = self.project_status.get()
        project["status"] = new_status
        self.projects_tree.item(iid, values=(
            project["name"],
            project["status"],
            project["start_date"],
            project.get("end_date", ""),
            f"${project['budget']:.2f}",
        ))
        self._save_data()
        self._show_project_details(None)

    def _delete_project(self) -> None:
        selected = self.projects_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a project to delete.")
            return
        iid = selected[0]
        if not messagebox.askyesno("Confirm delete", "Are you sure you want to remove this project?"):
            return
        self.projects_tree.delete(iid)
        self.data["projects"] = [p for p in self.data.get("projects", []) if p["name"] != iid]
        self.project_details.configure(state=tk.NORMAL)
        self.project_details.delete("1.0", tk.END)
        self.project_details.configure(state=tk.DISABLED)
        self._save_data()


    def _create_menubar(self) -> None:
        menubar = tk.Menu(self)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(
            label="Dark mode",
            variable=self.dark_mode,
            command=self._toggle_dark_mode,
        )
        menubar.add_cascade(label="View", menu=view_menu)
        self.config(menu=menubar)
        self._menubar = menubar

    def _register_text_widget(self, widget: tk.Text) -> None:
        self._text_widgets.append(widget)

    def _style_text_widget(self, widget: tk.Text, palette: Dict[str, str]) -> None:
        widget.configure(
            bg=palette["input"],
            fg=palette["input_fg"],
            insertbackground=palette["input_fg"],
            highlightbackground=palette["border"],
            highlightcolor=palette["border"],
            selectbackground=palette["accent"],
            selectforeground=palette["foreground"],
        )

    def _apply_theme(self) -> None:
        palette = self._dark_palette if self.dark_mode.get() else self._light_palette
        theme_name = "sdalocal-dark" if self.dark_mode.get() else "sdalocal-light"

        self.style.theme_use(theme_name)

        self.configure(bg=palette["background"])
        self.tk_setPalette(
            background=palette["frame"],
            foreground=palette["foreground"],
            activeBackground=palette["accent"],
            activeForeground=palette["foreground"],
            highlightColor=palette["border"],
            selectBackground=palette["accent"],
            selectForeground=palette["foreground"],
            insertBackground=palette["input_fg"],
        )

        for text_widget in self._text_widgets:
            self._style_text_widget(text_widget, palette)

        if hasattr(self, "_menubar"):
            self._style_menu(self._menubar, palette)

    def _toggle_dark_mode(self) -> None:
        self._apply_theme()

    def _setup_custom_themes(self) -> None:
        base_theme = "clam" if "clam" in self.style.theme_names() else self.style.theme_use()
        for theme_name, palette in (
            ("sdalocal-light", self._light_palette),
            ("sdalocal-dark", self._dark_palette),
        ):
            if theme_name in self.style.theme_names():
                self.style.theme_delete(theme_name)
            self.style.theme_create(
                theme_name,
                parent=base_theme,
                settings={
                    "TFrame": {"configure": {"background": palette["frame"], "foreground": palette["foreground"]}},
                    "TLabelframe": {"configure": {"background": palette["frame"], "foreground": palette["foreground"], "bordercolor": palette["border"]}},
                    "TLabelframe.Label": {"configure": {"background": palette["frame"], "foreground": palette["foreground"]}},
                    "TLabel": {"configure": {"background": palette["frame"], "foreground": palette["foreground"]}},
                    "TButton": {
                        "configure": {"background": palette["frame"], "foreground": palette["foreground"]},
                        "map": {
                            "background": [("active", palette["accent"])],
                            "foreground": [("active", palette["foreground"])],
                        },
                    },
                    "TNotebook": {"configure": {"background": palette["background"], "bordercolor": palette["border"]}},
                    "TNotebook.Tab": {
                        "configure": {
                            "background": palette["frame"],
                            "foreground": palette["foreground"],
                            "padding": (10, 5),
                        },
                        "map": {
                            "background": [("selected", palette["accent"])],
                            "foreground": [("selected", palette["foreground"])],
                        },
                    },
                    "TEntry": {
                        "configure": {
                            "fieldbackground": palette["input"],
                            "foreground": palette["input_fg"],
                            "background": palette["frame"],
                            "insertcolor": palette["input_fg"],
                        }
                    },
                    "TCombobox": {
                        "configure": {
                            "fieldbackground": palette["input"],
                            "foreground": palette["input_fg"],
                            "background": palette["frame"],
                        },
                        "map": {
                            "fieldbackground": [
                                ("readonly", palette["input"]),
                                ("!disabled", palette["input"]),
                            ],
                            "foreground": [
                                ("readonly", palette["input_fg"]),
                                ("!disabled", palette["input_fg"]),
                            ],
                        },
                    },
                    "Treeview": {
                        "configure": {
                            "background": palette["tree_background"],
                            "fieldbackground": palette["tree_field"],
                            "foreground": palette["tree_foreground"],
                            "bordercolor": palette["border"],
                        },
                        "map": {
                            "background": [("selected", palette["accent"])],
                            "foreground": [("selected", palette["foreground"])],
                        },
                    },
                    "Treeview.Heading": {
                        "configure": {"background": palette["frame"], "foreground": palette["foreground"]}
                    },
                },
            )

    def _style_menu(self, menu: tk.Menu, palette: Dict[str, str]) -> None:
        menu.configure(
            background=palette["frame"],
            foreground=palette["foreground"],
            activebackground=palette["accent"],
            activeforeground=palette["foreground"],
            bd=0,
            relief=tk.FLAT,
        )
        last_index = menu.index("end")
        if last_index is None:
            return
        for index in range(last_index + 1):
            if menu.type(index) == "cascade":
                submenu = menu.nametowidget(menu.entrycget(index, "menu"))
                self._style_menu(submenu, palette)

def main() -> None:
    """Launch the sdaLocal desktop application."""

    app = SDALocalApp()
    app.mainloop()


if __name__ == "__main__":
    main()
