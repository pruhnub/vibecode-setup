from __future__ import annotations

import argparse
from pathlib import Path

from .core import doctor, init_project, status
from . import __version__


def main() -> None:
    parser = argparse.ArgumentParser(prog="vibecode", description="Project context infrastructure for AI coding agents.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")
    init = sub.add_parser("init", help="Scan and initialize VibeCode context in a project")
    init.add_argument("--force", action="store_true", help="Overwrite generated files")
    init.add_argument("--name", help="Project name (defaults to folder name)")
    sub.add_parser("doctor", help="Check VibeCode project context")
    sub.add_parser("status", help="Detect the project stack")
    args = parser.parse_args()
    root = Path.cwd()

    if args.command == "init":
        created, skipped, profile = init_project(root, args.name, args.force)
        print(f"\nVibeCode Init — {profile.name}\n")
        print(f"  Stack: {profile.stack}")
        print(f"  Git: {'detected' if profile.git else 'not detected'}")
        for item in created:
            print(f"  ✓ {item}")
        for item in skipped:
            print(f"  • skipped {item} (already exists)")
        print("\nProject context initialized. Review .vibecode/current-state.md and .vibecode/tasks.md before coding.\n")
    elif args.command == "doctor":
        result = doctor(root)
        print(f"\nVibeCode Doctor — {root.name}\n")
        for ok, message in result:
            print(f"  {'✓' if ok else '⚠'} {message}")
        print()
    elif args.command == "status":
        info = status(root)
        print(f"\nVibeCode Status — {root.name}\n")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
