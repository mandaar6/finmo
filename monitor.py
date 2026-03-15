# monitor.py - real-time file monitoring using watchdog

import os
import platform
import sys
import time
from datetime import datetime, timezone

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import database
import hasher
import alerts
from baseline import is_excluded


def get_hostname():
    """Get the hostname of this machine."""
    return platform.node()


class FileChangeHandler(FileSystemEventHandler):
    """Handles file system events from watchdog."""

    def __init__(self, config, conn):
        self.config = config
        self.conn = conn
        self.hostname = get_hostname()
        self.excluded = config.get("excluded_paths", [])

    def on_created(self, event):
        if event.is_directory:
            return
        self.handle_change(event.src_path, "ADDED")

    def on_modified(self, event):
        if event.is_directory:
            return
        self.handle_change(event.src_path, "MODIFIED")

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.handle_change(event.src_path, "DELETED")

    def handle_change(self, file_path, change_type):
        """Process a file change - check hash, send alerts, save to db."""

        # skip excluded files
        if is_excluded(file_path, self.excluded):
            return

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        old_entry = database.get_baseline(self.conn, file_path)

        if change_type == "DELETED":
            old_hash = old_entry["hash"] if old_entry else "unknown"
            new_hash = None

            print(f"\n[!] DELETED: {file_path}")
            print(f"    Time: {now}")
            print(f"    Last hash: {old_hash[:20]}...")

            # remove from baseline
            database.remove_baseline(self.conn, file_path)

        elif change_type == "ADDED":
            info = hasher.get_file_info(file_path)
            if info is None:
                return

            old_hash = None
            new_hash = info["hash"]

            print(f"\n[!] NEW FILE: {file_path}")
            print(f"    Time: {now}")
            print(f"    Hash: {new_hash[:20]}...")
            print(f"    Size: {info['size']} bytes")
            print(f"    Owner: {info['owner']}")

            # add to baseline
            database.save_baseline(self.conn, file_path, info["hash"], info["size"],
                                   info["modified_at"], info["owner"], info["permissions"])

        else:
            # MODIFIED
            info = hasher.get_file_info(file_path)
            if info is None:
                return

            old_hash = old_entry["hash"] if old_entry else None
            new_hash = info["hash"]

            # if the hash hasn't actually changed, ignore this event
            if old_hash and new_hash == old_hash:
                return

            print(f"\n[!] MODIFIED: {file_path}")
            print(f"    Time: {now}")
            if old_hash:
                print(f"    Old hash: {old_hash[:20]}...")
            print(f"    New hash: {new_hash[:20]}...")
            print(f"    Owner: {info['owner']}  |  Permissions: {info['permissions']}")

            # update baseline with new hash
            database.save_baseline(self.conn, file_path, info["hash"], info["size"],
                                   info["modified_at"], info["owner"], info["permissions"])

        # save change to database
        database.record_change(self.conn, file_path, change_type,
                               old_hash, new_hash, self.hostname)

        # send alerts
        alerts.notify(self.config, change_type, file_path,
                      old_hash or "", new_hash or "", self.hostname, now)


def start_monitor(config):
    """Start watching files for changes. Runs until Ctrl+C."""
    db_path = config.get("database_path", "./data/finmo.db")
    watched = config.get("watched_paths", [])
    hostname = get_hostname()

    conn = database.connect(db_path)
    file_count = database.count_baselines(conn)

    # check alert channels
    tg = config.get("telegram", {})
    em = config.get("email", {})

    print("\n========================================")
    print("  Finmo - File Integrity Monitor")
    print("========================================\n")
    print(f"  Host:     {hostname}")
    print(f"  Watching: {len(watched)} paths")
    print(f"  Baseline: {file_count} files")

    if tg.get("enabled") and tg.get("bot_token") and tg.get("chat_id"):
        print(f"  Telegram: ON")
    else:
        print(f"  Telegram: OFF")

    if em.get("enabled") and em.get("sender") and em.get("password"):
        print(f"  Email:    ON")
    else:
        print(f"  Email:    OFF")

    print(f"\n  Press Ctrl+C to stop.\n")

    if file_count == 0:
        print("[!] No baseline found. Run 'python finmo.py baseline' first.")
        print("    Monitoring will still work but all files will show as new.\n")

    # set up watchdog
    handler = FileChangeHandler(config, conn)
    observer = Observer()

    for path in watched:
        if not os.path.exists(path):
            print(f"[!] Skipping (does not exist): {path}")
            continue
        observer.schedule(handler, path, recursive=True)

    observer.start()
    print("[+] Monitor started. Watching for changes...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Stopping monitor...")
        observer.stop()

    observer.join()
    conn.close()
    print("[+] Monitor stopped.")

