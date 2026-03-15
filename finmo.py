# finmo.py - main entry point for the File Integrity Monitor
# Run this with: python finmo.py <command>

import argparse
import sys

from config_loader import load_config
import baseline
import monitor


def main():
    parser = argparse.ArgumentParser(
        description="Finmo - File Integrity Monitor"
    )

    parser.add_argument("--config", default="config/config.yaml",
                        help="path to config file")

    subparsers = parser.add_subparsers(dest="command", help="available commands")

    # baseline command
    subparsers.add_parser("baseline", help="create a new baseline of all watched files")

    # monitor command
    subparsers.add_parser("monitor", help="start real-time file monitoring")

    # diff command
    subparsers.add_parser("diff", help="compare current files against the baseline")

    # reset command
    reset_parser = subparsers.add_parser("reset", help="reset baseline (all or one file)")
    reset_parser.add_argument("--path", help="reset only this file (optional)")

    # changes command
    changes_parser = subparsers.add_parser("changes", help="show recent detected changes")
    changes_parser.add_argument("--limit", type=int, default=20, help="number of changes to show")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # load config
    config = load_config(args.config)
    if config is None:
        sys.exit(1)

    # run the right command
    if args.command == "baseline":
        print("\n[*] Creating baseline...\n")
        baseline.create_baseline(config)

    elif args.command == "monitor":
        monitor.start_monitor(config)

    elif args.command == "diff":
        print("\n[*] Comparing files against baseline...\n")
        baseline.show_diff(config)

    elif args.command == "reset":
        baseline.reset_baseline(config, file_path=args.path)

    elif args.command == "changes":
        baseline.show_recent_changes(config, limit=args.limit)


main()
