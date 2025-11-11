"""Utilities for building a Windows executable of the sdaLocal app."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import List


def _pyinstaller_available() -> bool:
    try:
        import PyInstaller  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        return False
    return True


def _run_pyinstaller(args: List[str]) -> int:
    try:
        from PyInstaller.__main__ import run as run_pyinstaller
    except ModuleNotFoundError as exc:  # pragma: no cover - handled by caller
        raise RuntimeError("PyInstaller is not available") from exc

    run_pyinstaller(args)
    return 0


def build(name: str = "sdaLocal", onefile: bool = True) -> Path:
    """Build the executable using PyInstaller and return the output path."""

    project_root = Path(__file__).resolve().parents[1]
    app_entry = project_root / "sda_local" / "app.py"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    if not _pyinstaller_available():
        raise SystemExit(
            "PyInstaller is required to build the executable. Install it with 'pip install pyinstaller'."
        )

    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    add_data_arg = f"{project_root / 'sda_local' / 'data'}{os.pathsep}sda_local/data"

    pyinstaller_args: List[str] = [
        str(app_entry),
        "--name",
        name,
        "--noconfirm",
        "--clean",
        "--windowed",
        "--add-data",
        add_data_arg,
    ]

    if onefile:
        pyinstaller_args.append("--onefile")

    _run_pyinstaller(pyinstaller_args)

    if onefile:
        exe_path = dist_dir / f"{name}.exe"
    else:
        exe_path = dist_dir / name / f"{name}.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"Expected executable not found at {exe_path}")

    return exe_path


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a Windows executable using PyInstaller.")
    parser.add_argument("--name", default="sdaLocal", help="Name of the generated executable.")
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Build a folder-based distribution instead of a single-file executable.",
    )
    parsed = parser.parse_args(argv)

    try:
        exe_path = build(name=parsed.name, onefile=not parsed.onedir)
    except (SystemExit, RuntimeError, FileNotFoundError) as exc:
        print(exc)
        return 1

    print(f"Executable created at: {exe_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
