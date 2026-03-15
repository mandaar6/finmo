# hasher.py - hash files with SHA-256 and grab basic file info

import hashlib
import os
import platform
from datetime import datetime, timezone


def hash_file(file_path):
    """Compute the SHA-256 hash of a file. Returns the hex string or None if unreadable."""
    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None


def get_file_info(file_path):
    """
    Get the hash and basic metadata for a file.
    Returns a dict with hash, size, modified time, owner, and permissions.
    Returns None if the file can't be read.
    """
    file_hash = hash_file(file_path)
    if file_hash is None:
        return None

    try:
        stat = os.stat(file_path)
    except (PermissionError, FileNotFoundError, OSError):
        return None

    size = stat.st_size
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # get owner and permissions based on OS
    if platform.system() in ("Linux", "Darwin"):
        try:
            import pwd
            owner = pwd.getpwuid(stat.st_uid).pw_name
        except (KeyError, ImportError):
            owner = str(stat.st_uid)

        # convert file mode to octal like "644"
        permissions = oct(stat.st_mode)[-3:]
    else:
        # on windows we don't have unix-style owners or permissions
        owner = "N/A"
        permissions = "N/A"

    return {
        "hash": file_hash,
        "size": size,
        "modified_at": modified_at,
        "owner": owner,
        "permissions": permissions,
    }
