# baseline.py - create, reset, and diff the file baseline

import os
import fnmatch

import database
import hasher


def is_excluded(file_path, excluded_paths):
    """Check if a file matches any exclusion pattern."""
    for pattern in excluded_paths:
        # glob patterns like *.log
        if pattern.startswith("*"):
            if fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        # directory prefixes like /proc/
        if os.path.normpath(file_path).startswith(os.path.normpath(pattern)):
            return True

    return False


def walk_files(watched_paths, excluded_paths):
    """Walk all watched paths and yield every file not excluded."""
    for path in watched_paths:
        path = os.path.normpath(path)

        # single file
        if os.path.isfile(path):
            if not is_excluded(path, excluded_paths):
                yield path
            continue

        # directory - walk recursively
        if not os.path.isdir(path):
            print(f"    [!] Path does not exist: {path}")
            continue

        for root, dirs, files in os.walk(path):
            # skip excluded directories
            dirs[:] = [d for d in dirs if not is_excluded(os.path.join(root, d), excluded_paths)]

            for filename in files:
                full_path = os.path.join(root, filename)
                if not is_excluded(full_path, excluded_paths):
                    yield full_path


def create_baseline(config):
    """Scan all watched paths, hash every file, save to database."""
    db_path = config.get("database_path", "./data/finmo.db")
    watched = config.get("watched_paths", [])
    excluded = config.get("excluded_paths", [])

    conn = database.connect(db_path)

    # clear old baselines before creating a new one
    database.clear_baselines(conn)

    count = 0
    current_dir = ""

    for file_path in walk_files(watched, excluded):
        # show which directory we are scanning
        file_dir = os.path.dirname(file_path)
        if file_dir != current_dir:
            current_dir = file_dir
            print(f"    Scanning {current_dir}/ ...")

        info = hasher.get_file_info(file_path)
        if info is None:
            continue

        database.save_baseline(conn, file_path, info["hash"], info["size"],
                               info["modified_at"], info["owner"], info["permissions"])
        count += 1

    conn.close()
    print(f"\n[+] Baseline created: {count} files hashed and saved")


def reset_baseline(config, file_path=None):
    """
    Reset the baseline. If a file path is given, just update that one file.
    If no path is given, recreate the entire baseline from scratch.
    """
    if file_path:
        # update just one file
        db_path = config.get("database_path", "./data/finmo.db")
        conn = database.connect(db_path)

        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            conn.close()
            return

        info = hasher.get_file_info(file_path)
        if info is None:
            print(f"[!] Cannot read file: {file_path}")
            conn.close()
            return

        database.save_baseline(conn, file_path, info["hash"], info["size"],
                               info["modified_at"], info["owner"], info["permissions"])
        conn.close()
        print(f"[+] Baseline updated for: {file_path}")
    else:
        # recreate the whole baseline
        print("[*] Resetting entire baseline...")
        create_baseline(config)


def show_diff(config):
    """Compare current filesystem against the saved baseline."""
    db_path = config.get("database_path", "./data/finmo.db")
    watched = config.get("watched_paths", [])
    excluded = config.get("excluded_paths", [])

    conn = database.connect(db_path)
    baselines = database.get_all_baselines(conn)

    if not baselines:
        print("[!] No baseline found. Run 'python finmo.py baseline' first.")
        conn.close()
        return

    modified = []
    added = []
    seen = set()

    for file_path in walk_files(watched, excluded):
        seen.add(file_path)
        info = hasher.get_file_info(file_path)
        if info is None:
            continue

        if file_path in baselines:
            old = baselines[file_path]
            if info["hash"] != old["hash"]:
                modified.append((file_path, old["hash"], info["hash"]))
        else:
            added.append((file_path, info["hash"]))

    # check for deleted files
    deleted = []
    for path in baselines:
        if path not in seen:
            deleted.append((path, baselines[path]["hash"]))

    conn.close()

    # print results
    if not modified and not added and not deleted:
        print("[+] No changes found. Everything matches the baseline.")
        return

    if modified:
        print(f"\n[!] Modified files ({len(modified)}):")
        for path, old_h, new_h in modified:
            print(f"    {path}")
            print(f"      old: {old_h[:20]}...")
            print(f"      new: {new_h[:20]}...")

    if added:
        print(f"\n[!] New files ({len(added)}):")
        for path, h in added:
            print(f"    {path}")

    if deleted:
        print(f"\n[!] Deleted files ({len(deleted)}):")
        for path, h in deleted:
            print(f"    {path}")

    total = len(modified) + len(added) + len(deleted)
    print(f"\n[*] Total changes: {total}")


def show_recent_changes(config, limit=20):
    """Show the most recent changes from the database."""
    db_path = config.get("database_path", "./data/finmo.db")
    conn = database.connect(db_path)
    changes = database.get_recent_changes(conn, limit)
    conn.close()

    if not changes:
        print("[*] No changes recorded yet.")
        return

    print(f"\n[*] Last {len(changes)} changes:\n")
    print(f"    {'Time':<22} {'Event':<12} {'File'}")
    print(f"    {'-'*22} {'-'*12} {'-'*40}")

    for c in changes:
        print(f"    {c['timestamp']:<22} {c['change_type']:<12} {c['file_path']}")
        if c.get("old_hash") and c.get("new_hash"):
            print(f"    {'':>22} old: {c['old_hash'][:20]}...")
            print(f"    {'':>22} new: {c['new_hash'][:20]}...")

    print("")
