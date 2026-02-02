---
allowed-tools: Bash(asutils confluence:*)
description: |
  Reference for asutils confluence CLI commands. Use the confluence-search AGENT for actual searches.
  This skill is a command reference only - invoke the agent for search tasks.
---

# Confluence CLI Reference

Reference for `asutils confluence` commands to search Epic's internal wiki at `epicgames.atlassian.net/wiki`.

## When to Use What

| Scenario | Use |
|----------|-----|
| User asks to search/find internal docs | **confluence-search agent** |
| Complex research needing multiple searches | **confluence-search agent** |
| You need to look up a specific command syntax | This skill (reference) |
| Simple single command you already know | Direct Bash call |

**For most Confluence searches, delegate to the `confluence-search` agent.**

## IMPORTANT: Do NOT use WebSearch for Confluence

Confluence is Epic's **internal** wiki. WebSearch cannot access it. Always use `asutils confluence` commands.

## Quick Reference

| Action | Command |
|--------|---------|
| Search | `asutils confluence search "query"` |
| Multi-search | `asutils confluence search "q1" "q2" --parallel` |
| Get page | `asutils confluence page <id>` |
| List spaces | `asutils confluence spaces` |
| Search in space | `asutils confluence search "query" --space DEV` |
| CQL search | `asutils confluence cql 'text~"term" AND space="KEY"'` |

## Search Commands

### Basic Search
```bash
# Search for pages containing "deployment"
asutils confluence search "deployment"

# Search with limit
asutils confluence search "authentication" --limit 20

# Search within a specific space
asutils confluence search "API design" --space ENG
```

### Parallel Multi-Query Search
For comprehensive results, search with multiple query variations:
```bash
asutils confluence search "authentication" "auth flow" "login" "OAuth" --parallel
```

### CQL Search
Use Confluence Query Language for advanced searches:
```bash
# Text and space filter
asutils confluence cql 'text~"automation" AND space="DEV"'

# Recent pages only
asutils confluence cql 'text~"deployment" AND lastModified >= now("-7d")'

# Title search
asutils confluence cql 'title~"guide" AND type=page'
```

## Page Retrieval

### Get Full Page Content
```bash
# Get page by ID (ID is shown in search results)
asutils confluence page 12345678

# Get raw HTML (not converted to markdown)
asutils confluence page 12345678 --raw

# Output as JSON
asutils confluence page 12345678 --json
```

### Get Child Pages
```bash
asutils confluence children 12345678
```

## Space Navigation

```bash
# List all spaces
asutils confluence spaces

# Limit results
asutils confluence spaces --limit 100
```

## CQL Reference

Confluence Query Language operators:

| Operator | Example | Description |
|----------|---------|-------------|
| `text~` | `text~"search term"` | Full-text search |
| `title~` | `title~"page title"` | Title search |
| `space=` | `space="DEV"` | Limit to space |
| `type=` | `type=page` | Content type (page, blogpost) |
| `creator=` | `creator="username"` | By creator |
| `lastModified` | `lastModified >= now("-7d")` | Recent changes |
| `label=` | `label="important"` | By label |
| `AND/OR` | `text~"A" AND space="B"` | Combine conditions |

## Output Formats

- Default: Rich table with titles, spaces, excerpts
- `--json`: JSON output for programmatic use
- Page content: Markdown format (or `--raw` for HTML)

## Error Handling

- **401 Unauthorized**: Check JIRA_API_TOKEN is set correctly
- **404 Not Found**: Page ID may be incorrect
- **No results**: Try broader search terms or different query variations
