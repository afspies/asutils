# Claude Code Instructions

## Publishing

**Always publish to PyPI after completing any change:**

```bash
echo "y" | uv run asutils publish bump patch
echo "y" | uv run asutils publish release
git add -A && git commit -m "Bump version" && git push
```

This ensures the latest version is always available for users.
