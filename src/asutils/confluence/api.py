"""Confluence REST API client for Epic's Atlassian Cloud instance."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.auth import HTTPBasicAuth

from asutils.confluence.config import get_api_token, get_confluence_config


def get_auth() -> HTTPBasicAuth:
    """Get HTTP Basic Auth for Confluence API."""
    config = get_confluence_config()
    return HTTPBasicAuth(config["email"], get_api_token())


def get_base_url() -> str:
    """Get Confluence API base URL."""
    config = get_confluence_config()
    return f"{config['base_url']}/rest/api"


def search(query: str, limit: int = 10, space: str | None = None) -> list[dict]:
    """Search Confluence using CQL (Confluence Query Language).

    Args:
        query: Search query text
        limit: Maximum number of results
        space: Optional space key to limit search

    Returns:
        List of search results with title, url, excerpt, page_id, space
    """
    cql = f'text~"{query}"'
    if space:
        cql = f'space="{space}" AND {cql}'

    resp = requests.get(
        f"{get_base_url()}/search",
        auth=get_auth(),
        params={"cql": cql, "limit": limit},
        timeout=30,
    )
    resp.raise_for_status()

    results = []
    config = get_confluence_config()
    wiki_base = config["base_url"]

    for r in resp.json().get("results", []):
        # Clean excerpt of HTML tags
        excerpt = r.get("excerpt", "")
        excerpt = re.sub(r"<[^>]+>", "", excerpt)[:200]

        results.append({
            "title": r.get("title"),
            "url": f"{wiki_base}{r.get('url', '')}",
            "excerpt": excerpt,
            "page_id": r.get("content", {}).get("id"),
            "space": r.get("resultGlobalContainer", {}).get("title"),
        })
    return results


def search_parallel(queries: list[str], limit: int = 10, space: str | None = None) -> list[dict]:
    """Search Confluence with multiple queries in parallel.

    Args:
        queries: List of search queries
        limit: Maximum results per query
        space: Optional space key to limit search

    Returns:
        Combined list of search results (deduplicated by page_id)
    """
    all_results = []
    seen_ids = set()

    with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
        futures = {executor.submit(search, q, limit, space): q for q in queries}
        for future in as_completed(futures):
            try:
                for result in future.result():
                    if result["page_id"] not in seen_ids:
                        seen_ids.add(result["page_id"])
                        all_results.append(result)
            except Exception as e:
                # Log but don't fail the whole search
                query = futures[future]
                print(f"Warning: Search for '{query}' failed: {e}")

    return all_results


def search_cql(cql: str, limit: int = 10) -> list[dict]:
    """Search Confluence using raw CQL query.

    Args:
        cql: Raw CQL query string
        limit: Maximum number of results

    Returns:
        List of search results
    """
    resp = requests.get(
        f"{get_base_url()}/search",
        auth=get_auth(),
        params={"cql": cql, "limit": limit},
        timeout=30,
    )
    resp.raise_for_status()

    results = []
    config = get_confluence_config()
    wiki_base = config["base_url"]

    for r in resp.json().get("results", []):
        excerpt = r.get("excerpt", "")
        excerpt = re.sub(r"<[^>]+>", "", excerpt)[:200]

        results.append({
            "title": r.get("title"),
            "url": f"{wiki_base}{r.get('url', '')}",
            "excerpt": excerpt,
            "page_id": r.get("content", {}).get("id"),
            "space": r.get("resultGlobalContainer", {}).get("title"),
        })
    return results


def get_page(page_id: str, as_markdown: bool = True) -> dict:
    """Get full content of a Confluence page.

    Args:
        page_id: Confluence page ID
        as_markdown: Convert HTML to markdown (default True)

    Returns:
        Dict with id, title, space, body, url
    """
    resp = requests.get(
        f"{get_base_url()}/content/{page_id}",
        auth=get_auth(),
        params={"expand": "body.view,space"},
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()
    body = data.get("body", {}).get("view", {}).get("value", "")

    if as_markdown:
        body = html_to_markdown(body)

    config = get_confluence_config()
    wiki_base = config["base_url"]

    return {
        "id": data.get("id"),
        "title": data.get("title"),
        "space": data.get("space", {}).get("key"),
        "body": body,
        "url": f"{wiki_base}{data.get('_links', {}).get('webui', '')}",
    }


def list_spaces(limit: int = 50) -> list[dict]:
    """List available Confluence spaces.

    Args:
        limit: Maximum number of spaces to return

    Returns:
        List of spaces with key, name, type
    """
    resp = requests.get(
        f"{get_base_url()}/space",
        auth=get_auth(),
        params={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()

    spaces = []
    for s in resp.json().get("results", []):
        spaces.append({
            "key": s.get("key"),
            "name": s.get("name"),
            "type": s.get("type"),
        })
    return spaces


def get_child_pages(parent_id: str, limit: int = 50) -> list[dict]:
    """Get child pages of a parent page.

    Args:
        parent_id: Parent page ID
        limit: Maximum number of children

    Returns:
        List of child pages with id, title
    """
    resp = requests.get(
        f"{get_base_url()}/content/{parent_id}/child/page",
        auth=get_auth(),
        params={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()

    children = []
    for c in resp.json().get("results", []):
        children.append({
            "id": c.get("id"),
            "title": c.get("title"),
        })
    return children


def html_to_markdown(html: str) -> str:
    """Convert HTML to markdown.

    Uses html2text if available, falls back to basic tag stripping.
    """
    try:
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # Don't wrap lines
        return h.handle(html)
    except ImportError:
        # Fallback: strip HTML tags
        return re.sub(r"<[^>]+>", "", html)


def verify_auth() -> bool:
    """Verify that authentication is working.

    Returns:
        True if auth is valid, raises exception otherwise
    """
    try:
        # Try to list spaces as a simple auth check
        resp = requests.get(
            f"{get_base_url()}/space",
            auth=get_auth(),
            params={"limit": 1},
            timeout=10,
        )
        resp.raise_for_status()
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Authentication failed. Check your JIRA_API_TOKEN.") from e
        raise
