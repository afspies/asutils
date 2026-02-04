"""Core Perforce operations wrapper."""

import subprocess
from typing import Any

from asutils.p4.config import DEPOT_ROOTS, resolve_depot_path


def run_p4(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run p4 command and return (returncode, stdout, stderr).

    Args:
        args: Command arguments (without 'p4' prefix)
        timeout: Command timeout in seconds

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["p4"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", "p4 command not found"


def run_p4_checked(args: list[str], timeout: int = 30) -> str:
    """Run p4 command and return stdout, raising on error.

    Args:
        args: Command arguments
        timeout: Command timeout

    Returns:
        Command stdout

    Raises:
        RuntimeError: If command fails
    """
    code, stdout, stderr = run_p4(args, timeout)
    if code != 0:
        raise RuntimeError(f"p4 {args[0]} failed: {stderr or stdout}")
    return stdout


def list_dirs(depot_path: str) -> list[dict]:
    """List directories at depot path.

    Args:
        depot_path: Depot path or alias

    Returns:
        List of dicts with 'path' key
    """
    path = resolve_depot_path(depot_path)
    # Ensure path ends with /* for dirs command
    if not path.endswith("/*") and not path.endswith("/..."):
        path = f"{path.rstrip('/')}/*"

    stdout = run_p4_checked(["dirs", path])

    dirs = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("error"):
            dirs.append({"path": line, "type": "dir"})

    return dirs


def list_files(depot_path: str, limit: int = 100) -> list[dict]:
    """List files at depot path.

    Args:
        depot_path: Depot path or alias
        limit: Maximum files to return

    Returns:
        List of dicts with path, revision, change, action, type
    """
    path = resolve_depot_path(depot_path)
    # Ensure path ends with pattern
    if not path.endswith("/*") and not path.endswith("/..."):
        path = f"{path.rstrip('/')}/*"

    # Use -m for max results
    stdout = run_p4_checked(["files", "-m", str(limit), path])

    files = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("error") or " - no such file" in line:
            continue
        # Parse: //path/file#rev - action change type
        # Example: //Fortnite/Main/Build.cs#5 - edit change 12345 (text)
        if "#" in line:
            parts = line.split("#", 1)
            file_path = parts[0]
            rest = parts[1] if len(parts) > 1 else ""

            # Extract revision
            rev_parts = rest.split(" - ", 1)
            rev = rev_parts[0] if rev_parts else ""

            files.append({
                "path": file_path,
                "revision": rev,
                "type": "file",
            })

    return files


def search_files(pattern: str, scope: str = "//...", limit: int = 50) -> list[dict]:
    """Search for files matching pattern.

    Args:
        pattern: File pattern (can include wildcards)
        scope: Search scope (depot path or alias)
        limit: Maximum results

    Returns:
        List of matching files
    """
    scope_path = resolve_depot_path(scope)

    # Build search path
    # P4 file patterns:
    #   //path/... = all files recursively
    #   //path/*.ext = files matching pattern in directory
    #   //path/.../*.ext = files matching pattern in any subdirectory
    if pattern.startswith("//"):
        search_path = pattern
    elif "/" in pattern:
        # Pattern has directory components, append to scope
        search_path = f"{scope_path.rstrip('/')}/{pattern}"
    else:
        # Simple filename pattern - search recursively
        # //Fortnite/Main + *.Build.cs -> //Fortnite/Main/.../*.Build.cs
        base = scope_path.rstrip("/")
        search_path = f"{base}/.../{pattern}"

    stdout = run_p4_checked(["files", "-m", str(limit), search_path])

    files = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("error") or " - no such file" in line:
            continue
        if "#" in line:
            file_path = line.split("#")[0]
            files.append({"path": file_path, "type": "file"})

    return files


def get_file_info(depot_path: str) -> dict:
    """Get detailed info about a file (fstat).

    Args:
        depot_path: Full depot path to file

    Returns:
        Dict with file info
    """
    path = resolve_depot_path(depot_path)
    stdout = run_p4_checked(["fstat", path])

    info = {"path": path}
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if line.startswith("..."):
            parts = line[3:].split(" ", 1)
            if len(parts) == 2:
                key, value = parts
                info[key] = value

    return info


def get_file_history(depot_path: str, limit: int = 10) -> list[dict]:
    """Get file change history (filelog).

    Args:
        depot_path: Full depot path to file
        limit: Maximum history entries

    Returns:
        List of history entries
    """
    path = resolve_depot_path(depot_path)
    stdout = run_p4_checked(["filelog", "-m", str(limit), path])

    history = []
    current = None

    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # New revision line: ... #5 change 12345 edit on 2024/01/15 by user@workspace
        if line.startswith("... #"):
            if current:
                history.append(current)

            # Parse the revision line
            parts = line[5:].split()
            current = {
                "revision": parts[0] if parts else "",
                "change": "",
                "action": "",
                "date": "",
                "user": "",
                "description": "",
            }

            # Extract fields
            for i, part in enumerate(parts):
                if part == "change" and i + 1 < len(parts):
                    current["change"] = parts[i + 1]
                elif part in ("edit", "add", "delete", "branch", "integrate"):
                    current["action"] = part
                elif part == "on" and i + 1 < len(parts):
                    current["date"] = parts[i + 1]
                elif part == "by" and i + 1 < len(parts):
                    current["user"] = parts[i + 1]

        # Description line (indented)
        elif current and line.startswith("\t"):
            if current["description"]:
                current["description"] += " "
            current["description"] += line.strip()

    if current:
        history.append(current)

    return history


def get_changelist(cl: int) -> dict:
    """Get changelist details (describe).

    Args:
        cl: Changelist number

    Returns:
        Dict with changelist info
    """
    stdout = run_p4_checked(["describe", "-s", str(cl)])

    lines = stdout.strip().split("\n")
    info = {
        "changelist": cl,
        "user": "",
        "date": "",
        "description": "",
        "files": [],
    }

    # First line: Change 12345 by user@workspace on 2024/01/15
    if lines:
        first = lines[0]
        parts = first.split()
        for i, part in enumerate(parts):
            if part == "by" and i + 1 < len(parts):
                info["user"] = parts[i + 1]
            elif part == "on" and i + 1 < len(parts):
                info["date"] = parts[i + 1]

    # Description and files
    in_description = False
    for line in lines[1:]:
        if line.startswith("\t"):
            if not info["files"]:  # Still in description
                if info["description"]:
                    info["description"] += "\n"
                info["description"] += line.strip()
        elif line.startswith("..."):
            # File line: ... //path#rev action
            file_info = line[4:].strip()
            info["files"].append(file_info)

    return info


def where(depot_path: str) -> dict:
    """Show local workspace mapping for depot path.

    Args:
        depot_path: Depot path

    Returns:
        Dict with depot, client, and local paths
    """
    path = resolve_depot_path(depot_path)
    stdout = run_p4_checked(["where", path])

    # Output: //depot/path //client/path /local/path
    parts = stdout.strip().split()
    result = {"depot": path, "client": "", "local": ""}

    if len(parts) >= 3:
        result["depot"] = parts[0]
        result["client"] = parts[1]
        result["local"] = parts[2]
    elif len(parts) == 1 and parts[0].startswith("-"):
        # Not mapped
        result["error"] = "Path not mapped in current workspace"

    return result


def print_file(depot_path: str, revision: int | None = None) -> str:
    """Get file contents (print).

    Args:
        depot_path: Depot path to file
        revision: Optional specific revision

    Returns:
        File contents as string
    """
    path = resolve_depot_path(depot_path)
    if revision:
        path = f"{path}@{revision}"

    stdout = run_p4_checked(["print", "-q", path], timeout=60)
    return stdout


def list_branches(depot: str, filter_pattern: str | None = None) -> list[dict]:
    """List branches/streams for a depot.

    Args:
        depot: Depot name or alias (e.g., 'fortnite', 'ue5')
        filter_pattern: Optional filter (e.g., 'Dev-*', 'Release-*', '*Valkyrie*')

    Returns:
        List of dicts with 'name', 'path', and 'type' (Main/Dev/Release)
    """
    # Resolve depot root
    depot_lower = depot.lower()
    if depot_lower in DEPOT_ROOTS:
        root = DEPOT_ROOTS[depot_lower]
    elif depot.startswith("//"):
        # Extract root from full path
        parts = depot.rstrip("/").split("/")
        root = f"//{parts[2]}" if len(parts) > 2 else depot
    else:
        root = f"//{depot}"

    stdout = run_p4_checked(["dirs", f"{root}/*"])

    branches = []
    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("error"):
            continue

        # Extract branch name from path
        name = line.rsplit("/", 1)[-1]

        # Apply filter if specified
        if filter_pattern:
            import fnmatch
            if not fnmatch.fnmatch(name, filter_pattern):
                continue

        # Determine branch type
        if name == "Main":
            branch_type = "main"
        elif name.startswith("Dev-"):
            branch_type = "dev"
        elif name.startswith("Release-"):
            branch_type = "release"
        else:
            branch_type = "other"

        branches.append({
            "name": name,
            "path": line,
            "type": branch_type,
        })

    return branches
