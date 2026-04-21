"""
Module 5 - Performance Evaluation Menu

Runs module1.py .. module4.py from the SAME directory as this file,
or runs them all sequentially.

Usage (from this folder):
  py module5.py
"""

from __future__ import annotations

import os
import runpy
from dataclasses import dataclass
from typing import Callable

HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class Target:
    name: str
    filename: str
    runner: Callable[[], None]


def _run_local(filename: str) -> None:
    path = os.path.join(HERE, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing file: {filename}")

    cwd = os.getcwd()
    try:
        os.chdir(HERE)  # keep any relative outputs in this folder
        runpy.run_path(path, run_name="__main__")
    finally:
        os.chdir(cwd)


def _targets() -> list[Target]:
    return [
        Target("Module 1", "module1.py", lambda: _run_local("module1.py")),
        Target("Module 2", "module2.py", lambda: _run_local("module2.py")),
        Target("Module 3", "module3.py", lambda: _run_local("module3.py")),
        Target("Module 4", "module4.py", lambda: _run_local("module4.py")),
    ]


def _menu() -> None:
    print("\n" + "=" * 72)
    print("MODULE 5 - Multi-Core Simulation Runner (Performance Evaluation)")
    print("=" * 72)
    print("Instructions: enter a number (0-5) then press Enter.\n")
    print("  1) Run Module 1 (module1.py)")
    print("  2) Run Module 2 (module2.py)")
    print("  3) Run Module 3 (module3.py)")
    print("  4) Run Module 4 (module4.py)")
    print("  5) Run Modules 1-4 sequentially")
    print("  0) Exit")


def main() -> None:
    while True:
        _menu()
        choice = input("Selection: ").strip()
        targets = _targets()

        try:
            if choice == "1":
                targets[0].runner()
            elif choice == "2":
                targets[1].runner()
            elif choice == "3":
                targets[2].runner()
            elif choice == "4":
                targets[3].runner()
            elif choice == "5":
                for t in targets:
                    print("\n" + "-" * 72)
                    print(f"Running {t.name} ({t.filename})...")
                    print("-" * 72)
                    t.runner()
                print("\nAll modules finished.")
            elif choice == "0":
                print("Goodbye.")
                return
            else:
                print("Invalid selection. Please choose 0-5.")

        except KeyboardInterrupt:
            print("\nInterrupted. Returning to menu...")
        except FileNotFoundError as e:
            print(f"\n[Missing file] {e}")
        except Exception as e:
            print(f"\n[Error] {type(e).__name__}: {e}")
            print("Tip: run the module directly to see a full traceback.")

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()