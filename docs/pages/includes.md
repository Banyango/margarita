# Using Includes in Python API

MARGARITA's include functionality allows you to compose templates from reusable snippets, making it easy to build modular, maintainable prompt libraries.

## Basic Include Usage

Margarita supports including other template files using the `[[ filename ]]` syntax.
When the renderer encounters this directive, it loads and renders the specified file,
inserting its content into the current template.

You can also pass parameters to the included template by specifying them as key-value pairs:

```margarita
//filename: main.mg
Welcome to the system!
[[ header is_admin=True show_menu=False ]]
```

```margarita
//filename: header.mg
User Admin Status: ${is_admin}
Menu Visible: ${show_menu}
```

This will render as:

```markdown
Welcome to the system!
User Admin Status: True
Menu Visible: False
```

#### Supported Parameter Types

>
> Currently, we only support string or boolean parameters.
>

### Setting Up the Renderer

The key to using includes is setting the `base_path` parameter when creating a `Renderer`. This tells MARGARITA where to resolve relative include paths:

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer

# Define base path for includes
template_dir = Path("./templates")

# Parse your main template
parser = Parser()
template_content = """
[[ header ]]

Main content here.

[[ footer ]]
"""

metadata, nodes = parser.parse(template_content)

# Create renderer with base_path
renderer = Renderer(
    context={"app_name": "MyApp"},
    base_path=template_dir
)

# Render - includes will be resolved relative to base_path
output = renderer.render(nodes)
```


## Nested Includes

Includes can reference other includes, creating a hierarchy of snippets. **Important**: All include paths are always resolved relative to the `base_path` set in the renderer, not relative to the file doing the including.

### Understanding Base Path Resolution

Given this directory structure:

```
templates/
  main.mg
  snippets/
    complete_prompt.mg
    header_section.mg
    system_role.mg
    safety_guidelines.mg
    body_section.mg
    footer_section.mg
```

**templates/snippets/complete_prompt.mg**:
```margarita
[[ snippets/header_section ]]

[[ snippets/body_section ]]

[[ snippets/footer_section ]]
```

**templates/snippets/header_section.mg**:
```margarita
[[ snippets/system_role ]]

[[ snippets/safety_guidelines ]]
```

Notice that even though `header_section.mg` is in the `snippets/` directory, it **still uses
`"snippets/system_role.mg"`** in its include statement, not just `"system_role.mg"`.
This is because all paths are resolved from `base_path`.


### Practical Tip: Organizing Nested Structures

Use consistent path prefixes to make nested includes clear:

```
templates/
  prompts/
    agent/
      researcher.mg    -> includes "components/agent/..."
      analyzer.mg      -> includes "components/agent/..."
  components/
    agent/
      role.mg          -> includes "atoms/agent/..."
      tools.mg         -> includes "atoms/agent/..."
  atoms/
    agent/
      identity.mg
      capabilities.mg
```

This structure makes it obvious that all includes use the full path from `templates/`.



## Real-World Example: Multi-Agent System

```margarita
//filename: prompts/agent/researcher.mg
You are a Researcher Agent.

You have access to the following tools:
- Web Search
- Database Query

Output your findings in a structured report.
```

```margarita
//filename: prompts/agent/analyzer.mg
You are an Analyzer Agent. You analyze data provided by other agents.

Use statistical methods and visualization tools to derive insights.
```

```margarita
//filename: agent_router.mg

if type == "researcher":
    [[ prompts/agent/researcher ]]
elif type == "analyzer":
    [[ prompts/agent/analyzer ]]
else:
    <<You are a General Agent. Adapt to any task given.>>

```

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer

# Define base path for includes
template_dir = Path("./templates")

# Parse your main template
parser = Parser()
template_content = """[[ agent_router ]]"""
metadata, nodes = parser.parse(template_content)

# Create renderer with base_path
renderer = Renderer(
    context={"type": "researcher"},
    base_path=template_dir
)

```
