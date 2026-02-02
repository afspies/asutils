"""Configuration management for Epic Atlassian services."""

import os
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".config" / "asutils"
CONFIG_FILE = CONFIG_DIR / "epic.yaml"

# Default configuration
DEFAULT_CONFIG = {
    "confluence": {
        "base_url": "https://epicgames.atlassian.net/wiki",
        "email": "alex.spies@epicgames.com",
    },
    "jira": {
        "base_url": "https://epicgames.atlassian.net",
        "default_project": "EML",
    },
}


def get_config() -> dict:
    """Load Epic configuration from file or return defaults."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or DEFAULT_CONFIG
    return DEFAULT_CONFIG


def save_config(config: dict) -> None:
    """Save Epic configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_confluence_config() -> dict:
    """Get Confluence-specific configuration."""
    return get_config().get("confluence", DEFAULT_CONFIG["confluence"])


def get_jira_config() -> dict:
    """Get JIRA-specific configuration."""
    return get_config().get("jira", DEFAULT_CONFIG["jira"])


def get_api_token() -> str:
    """Get the API token from environment variable."""
    token = os.environ.get("JIRA_API_TOKEN")
    if not token:
        raise ValueError(
            "JIRA_API_TOKEN environment variable not set. "
            "Set it in your shell profile or run: export JIRA_API_TOKEN='your-token'"
        )
    return token
