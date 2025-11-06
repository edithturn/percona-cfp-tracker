#!/usr/bin/env python3
"""Entry point that runs all steps in order (stub)."""

from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    print(f"Running pipeline in {project_root}")
    # TODO: orchestrate fetch -> merge -> sync -> notify -> update_readme

if __name__ == "__main__":
    main()
