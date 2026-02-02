"""Confluence API client for Epic's Atlassian Cloud instance."""

from asutils.confluence.api import (
    get_child_pages,
    get_page,
    html_to_markdown,
    list_spaces,
    search,
    search_cql,
    search_parallel,
    verify_auth,
)
from asutils.confluence.config import (
    get_api_token,
    get_config,
    get_confluence_config,
    save_config,
)

__all__ = [
    # API functions
    "search",
    "search_parallel",
    "search_cql",
    "get_page",
    "list_spaces",
    "get_child_pages",
    "html_to_markdown",
    "verify_auth",
    # Config functions
    "get_config",
    "save_config",
    "get_confluence_config",
    "get_api_token",
]
