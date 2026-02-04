"""Configuration management for Perforce connections."""

import os
import subprocess
from pathlib import Path

# Epic-specific server options
SERVERS = {
    "internal": "perforce:1666",
    "vpn": "perforce-proxy-vpn.epicgames.net:1666",
}

# Quick path aliases for Epic depot structure
DEPOT_ALIASES = {
    # Main development
    "fortnite": "//Fortnite/Main",
    "fn": "//Fortnite/Main",  # Short alias
    "fortnite-release": "//Fortnite/Release-*",
    "ue5": "//UE5/Main",
    "ue4": "//UE4/Main",
    "eos": "//EOSSDK/Main",
    # Support areas
    "3rdparty": "//depot/3rdParty",
    "thirdparty": "//depot/3rdParty",
    "tools": "//depot/InternalTools",
    "plugins": "//GamePlugins",
}


def resolve_depot_path(path: str) -> str:
    """Resolve alias or relative path to full depot path.

    Args:
        path: Depot path, alias, or relative path

    Returns:
        Normalized depot path starting with //

    Examples:
        >>> resolve_depot_path("fortnite")
        '//Fortnite/Main'
        >>> resolve_depot_path("//UE5/Main/Engine")
        '//UE5/Main/Engine'
        >>> resolve_depot_path("Fortnite/Main")
        '//Fortnite/Main'
    """
    # Check if path is an alias
    lower_path = path.lower()
    if lower_path in DEPOT_ALIASES:
        return DEPOT_ALIASES[lower_path]

    # Ensure depot path format
    if not path.startswith("//"):
        path = f"//{path}"

    return path


def get_p4_config() -> dict:
    """Get P4 configuration from environment or p4 set.

    Returns:
        Dict with P4PORT, P4USER, P4CLIENT if available
    """
    config = {}

    # Check environment variables first
    for var in ["P4PORT", "P4USER", "P4CLIENT", "P4CONFIG"]:
        if value := os.environ.get(var):
            config[var] = value

    # If we have a P4CONFIG, try to read from p4 set
    if not config:
        try:
            result = subprocess.run(
                ["p4", "set", "-q"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        # Remove any trailing " (set)" or "(config)"
                        value = value.split("(")[0].strip()
                        config[key] = value
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return config


def verify_connection() -> tuple[bool, str]:
    """Verify P4 connection is working.

    Returns:
        Tuple of (success, message)
    """
    try:
        result = subprocess.run(
            ["p4", "info"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Extract server info from output
            lines = result.stdout.strip().split("\n")
            server = ""
            user = ""
            for line in lines:
                if line.startswith("Server address:"):
                    server = line.split(":", 1)[1].strip()
                elif line.startswith("User name:"):
                    user = line.split(":", 1)[1].strip()
            return True, f"Connected as {user} to {server}"
        else:
            return False, f"Connection failed: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "Connection timed out"
    except FileNotFoundError:
        return False, "p4 command not found. Is Perforce installed?"


def get_server_suggestion() -> str:
    """Get helpful server suggestion based on common issues."""
    return (
        "If not connected, try:\n"
        f"  Internal network: export P4PORT={SERVERS['internal']}\n"
        f"  VPN connection:   export P4PORT={SERVERS['vpn']}"
    )
