# Include Files

Reuse template fragments using `{% include "file.marg" %}`. Includes are resolved relative to the including template's directory.

Example

`header.marg`:

```margarita
This is the header content.
```

`page.marg`:

```margarita
{% include "header.marg" %}

# Page Title

Content goes here using the same context.
```

Rendered result

When rendering `page.marg`, the output will include the header content followed by the page body:

```text
This is the header content.

# Page Title

Content goes here using the same context.
```

Behavior

- Included files have access to the same rendering context as the parent template.
- Paths are resolved relative to the parent template's directory (the CLI and renderer set `base_path`).
- Avoid circular includes; they can cause infinite loops or errors.

## Using Includes in Python API

When using MARGARITA programmatically, you must set the `base_path` when creating the renderer. **All include paths are resolved relative to this base path**, not relative to the file doing the including.

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer

# Parse your template
parser = Parser()
template = '{% include "header.marg" %}\n\nMain content here.'
_, nodes = parser.parse(template)

# Set base_path - all includes resolve from here
renderer = Renderer(
    context={"title": "My Page"},
    base_path=Path("./templates")  # header.marg will be loaded from ./templates/header.marg
)

output = renderer.render(nodes)
```

**Important**: Even in nested includes, all paths are from `base_path`. If `snippets/section.marg` includes another file, it must use the full path from `base_path`:

```margarita
{# Inside templates/snippets/section.marg #}
{% include "snippets/subsection.marg" %}  {# NOT just "subsection.marg" #}
```

See the [Using Includes](includes.md) page for comprehensive examples and patterns.

Tip: Use includes for headers, footers, and small shared components to keep templates DRY and maintainable.
