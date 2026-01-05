"""Tree view utility for nested data structures.

This module provides utilities for visualizing nested dicts, lists, and other
data structures with tree-style formatting and syntax highlighting.

Note: Rich imports are deferred until the treeview function is called,
so importing this module won't affect print behavior elsewhere.
"""

from typing import Any


def _get_tree_prefix(depth: int, is_last: bool = False, prefix_chars: str = '') -> str:
    """
    Generate tree-style prefix with proper indentation.

    Args:
        depth: Current depth in the tree
        is_last: Whether this is the last item at this level
        prefix_chars: Existing prefix characters for current line
    """
    if depth == 0:
        return ''

    current = '└── ' if is_last else '├── '
    return prefix_chars + current


def _format_content(content: Any, preview_content: bool, max_length: int) -> str:
    """Format content with truncation."""
    if not preview_content:
        return ''

    content_str = str(content)
    if len(content_str) > max_length:
        content_str = content_str[:max_length] + '...'

    return f' = {content_str}' if content_str else ''


def _build_visualization(
    obj: Any,
    Text: type,
    *,
    preview_content: bool,
    max_length: int,
    depth: int = 0,
    is_last: bool = True,
    key: str = '',
    output: Any = None,
    prefix_chars: str = '',
) -> Any:
    """Build visualization as a single Rich Text object.

    Args:
        obj: The object to visualize
        Text: The rich.text.Text class (passed in to avoid module-level import)
        preview_content: Whether to display values
        max_length: Maximum length for displayed values
        depth: Current depth in the tree
        is_last: Whether this is the last item at this level
        key: Key name for this node
        output: Accumulated Text output
        prefix_chars: Prefix characters for tree rendering
    """
    if output is None:
        output = Text()

    def add_node(label: str, type_name: str, content: str = ''):
        """Add a node to the text output."""
        if output.plain:  # If not first line, add newline
            output.append('\n')

        prefix = _get_tree_prefix(depth, is_last, prefix_chars)
        output.append(prefix, style='tree')
        output.append(label, style='key')
        output.append(': ', style='tree')
        output.append(type_name, style='type')
        if content:
            output.append(content, style='value')

    if isinstance(obj, dict):
        if key:  # Print dict header if this is a nested dict
            add_node(key, 'dict')

        items = list(obj.items())
        next_prefix = prefix_chars + ('    ' if is_last or depth == 0 else '│   ')

        for i, (k, v) in enumerate(items):
            _build_visualization(
                v,
                Text,
                preview_content=preview_content,
                max_length=max_length,
                depth=depth + 1,
                is_last=i == len(items) - 1,
                key=k,
                output=output,
                prefix_chars=next_prefix,
            )

    elif isinstance(obj, list):
        label = key if key else ''
        if not obj:
            add_node(label, 'list', ' (empty)')
            return output

        if all(not isinstance(x, (dict, list)) for x in obj):
            types = {type(x).__name__ for x in obj}
            type_str = f'list of {" or ".join(types)} [{len(obj)} items]'
            add_node(label, type_str)

            if preview_content:
                next_prefix = prefix_chars + (
                    '    ' if is_last or depth == 0 else '│   '
                )
                for i, item in enumerate(obj):
                    _build_visualization(
                        item,
                        Text,
                        preview_content=preview_content,
                        max_length=max_length,
                        depth=depth + 1,
                        is_last=i == len(obj) - 1,
                        key=f'[{i}]',
                        output=output,
                        prefix_chars=next_prefix,
                    )
            return output

        add_node(label, 'list')
        next_prefix = prefix_chars + ('    ' if is_last or depth == 0 else '│   ')

        for i, item in enumerate(obj):
            _build_visualization(
                item,
                Text,
                preview_content=preview_content,
                max_length=max_length,
                depth=depth + 1,
                is_last=i == len(obj) - 1,
                key=f'[{i}]',
                output=output,
                prefix_chars=next_prefix,
            )

    else:
        content = _format_content(obj, preview_content, max_length)
        add_node(key, type(obj).__name__, content)

    return output


def _get_theme():
    """Create the custom theme for JSON visualization."""
    from rich.theme import Theme

    return Theme(
        {
            'key': 'bright_yellow',
            'type': 'bright_cyan',
            'value': 'bright_green',
            'tree': 'dim',
        }
    )


def treeview(
    obj: Any,
    *,
    preview_content: bool = False,
    max_length: int = 100,
    jupyter_mode: bool | None = None,
) -> Any:
    """
    Visualize nested data structure with tree-style indicators and colored output.

    Automatically detects Jupyter environment and adjusts output accordingly.

    Args:
        obj: The object to visualize (dict, list, or nested structure)
        preview_content: Whether to display the actual values (default: False)
        max_length: Maximum length for displayed values before truncation (default: 100)
        jupyter_mode: Force Jupyter mode on/off (default: auto-detect)

    Returns:
        In Jupyter: The Rich renderable object for display
        In terminal/scripts: None (prints to console)

    Example:
        >>> data = {
        ...     'name': 'John Doe',
        ...     'contacts': {'email': 'john@example.com', 'phones': ['+1234567890']},
        ... }
        >>> _ = treeview(data)  # Shows structure only
        >>> _ = treeview(data, preview_content=True)  # Shows values
    """
    # Lazy import rich components only when function is called
    from rich.console import Console
    from rich.text import Text

    custom_theme = _get_theme()
    output = _build_visualization(
        obj, Text, preview_content=preview_content, max_length=max_length
    )

    # Auto-detect Jupyter environment if not specified
    if jupyter_mode is None:
        try:
            from IPython import get_ipython

            jupyter_mode = (
                get_ipython() is not None
                and 'IPython.core.interactiveshell' in str(type(get_ipython()))
            )
        except (ImportError, NameError):
            jupyter_mode = False

    if jupyter_mode:
        jupyter_console = Console(
            theme=custom_theme,
            force_jupyter=True,
            width=None,
            soft_wrap=True,
        )
        jupyter_console.print(output)
        return output
    else:
        terminal_console = Console(theme=custom_theme)
        terminal_console.print(output)
        return None
