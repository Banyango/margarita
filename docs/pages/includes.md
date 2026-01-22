# Using Includes in Python API

MARGARITA's include functionality allows you to compose templates from reusable snippets, making it easy to build modular, maintainable prompt libraries. This page covers how to use includes programmatically through the Python API.

## Basic Include Usage

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
{% include "header.marg" %}

Main content here.

{% include "footer.marg" %}
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

## Creating Reusable Snippets

### Example: Prompt Building Blocks

Create a library of reusable prompt components:

**templates/snippets/system_role.marg**:
```margarita
You are {{role}}, a helpful AI assistant.
```

**templates/snippets/task_context.marg**:
```margarita
## Task Context

User: {{user_name}}
Session: {{session_id}}
Timestamp: {{timestamp}}
```

**templates/snippets/output_format.marg**:
```margarita
## Output Requirements

- Provide responses in {{format}} format
- Keep responses {{length}}
- Use {{tone}} tone
```

### Using the Snippets

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer

# Main template that composes snippets
main_template = """
{% include "snippets/system_role.marg" %}

{% include "snippets/task_context.marg" %}

## User Request

{{user_request}}

{% include "snippets/output_format.marg" %}
"""

# Parse and render
parser = Parser()
_, nodes = parser.parse(main_template)

renderer = Renderer(
    context={
        "role": "technical expert",
        "user_name": "Alice",
        "session_id": "sess_123",
        "timestamp": "2024-01-19T10:30:00Z",
        "user_request": "Explain quantum computing",
        "format": "markdown",
        "length": "concise",
        "tone": "professional"
    },
    base_path=Path("./templates")
)

prompt = renderer.render(nodes)
print(prompt)
```

## Dynamic Include Loading

### MargaritaComposer

Include complex prompts dynamically using `Composer`:

```python
from pathlib import Path
from margarita.composer import Composer

# Usage
manager = Composer(Path("./templates"))

# Compose a complex prompt from multiple snippets
prompt = manager.compose_prompt(
    snippets=[
        "snippets/system_role.marg",
        "snippets/task_context.marg",
        "snippets/chain_of_thought.marg",
        "snippets/output_format.marg"
    ],
    context={
        "role": "data scientist",
        "user_name": "Bob",
        "task": "Analyze customer churn",
        "format": "JSON",
        "tone": "analytical"
    }
)
```

## Conditional Snippet Loading

### Using Conditionals with Includes

```python
from margarita.parser import Parser
from margarita.renderer import Renderer
# Template with conditional includes
template = """
{% include "snippets/system_role.marg" %}

{% if use_examples %}
{% include "snippets/few_shot_examples.marg" %}
{% endif %}

## Task

{{task}}

{% if detailed_output %}
{% include "snippets/detailed_format.marg" %}
{% else %}
{% include "snippets/brief_format.marg" %}
{% endif %}
"""

parser = Parser()
_, nodes = parser.parse(template)

# Render with detailed mode
renderer = Renderer(
    context={
        "role": "assistant",
        "use_examples": True,
        "task": "Summarize the article",
        "detailed_output": True
    },
    base_path=Path("./templates")
)

prompt = renderer.render(nodes)
```

## Nested Includes

Includes can reference other includes, creating a hierarchy of snippets. **Important**: All include paths are always resolved relative to the `base_path` set in the renderer, not relative to the file doing the including.

### Understanding Base Path Resolution

Given this directory structure:

```
templates/
  main.marg
  snippets/
    complete_prompt.marg
    header_section.marg
    system_role.marg
    safety_guidelines.marg
    body_section.marg
    footer_section.marg
```

**templates/snippets/complete_prompt.marg**:
```margarita
{% include "snippets/header_section.marg" %}

{% include "snippets/body_section.marg" %}

{% include "snippets/footer_section.marg" %}
```

**templates/snippets/header_section.marg**:
```margarita
{% include "snippets/system_role.marg" %}

{% include "snippets/safety_guidelines.marg" %}
```

Notice that even though `header_section.marg` is in the `snippets/` directory, it **still uses `"snippets/system_role.marg"`** in its include statement, not just `"system_role.marg"`. This is because all paths are resolved from `base_path`.

### Example: Nested Include Rendering

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer

# Parse the main template
parser = Parser()
_, nodes = parser.parse('{% include "snippets/complete_prompt.marg" %}')

# Set base_path to templates/
renderer = Renderer(
    context={"role": "assistant"},
    base_path=Path("./templates")
)

# All includes are resolved from ./templates/
# - snippets/complete_prompt.marg -> ./templates/snippets/complete_prompt.marg
# - snippets/header_section.marg -> ./templates/snippets/header_section.marg
# - snippets/system_role.marg -> ./templates/snippets/system_role.marg
output = renderer.render(nodes)
```

### Deep Nesting Example

You can nest includes as deeply as needed:

**templates/layouts/full_prompt.marg**:
```margarita
{% include "sections/preamble.marg" %}

{% include "sections/main_content.marg" %}

{% include "sections/conclusion.marg" %}
```

**templates/sections/preamble.marg**:
```margarita
{% include "components/header.marg" %}

{% include "components/instructions.marg" %}
```

**templates/components/header.marg**:
```margarita
{% include "atoms/logo.marg" %}

{% include "atoms/title.marg" %}
```

```python
# All paths resolve from base_path, no matter how deep the nesting
parser = Parser()
_, nodes = parser.parse('{% include "layouts/full_prompt.marg" %}')

renderer = Renderer(
    context={"title": "My Prompt"},
    base_path=Path("./templates")
)

output = renderer.render(nodes)
```

### Why Base Path Matters

This design makes your templates portable and predictable:

```python
# ✅ CORRECT: All paths from base_path
# templates/snippets/section.marg contains:
{% include "snippets/subsection.marg" %}

# ❌ WRONG: Don't use relative paths from the current file
# templates/snippets/section.marg should NOT contain:
{% include "subsection.marg" %}  # This won't work!
```

### Practical Tip: Organizing Nested Structures

Use consistent path prefixes to make nested includes clear:

```
templates/
  prompts/
    agent/
      researcher.marg    -> includes "components/agent/..."
      analyzer.marg      -> includes "components/agent/..."
  components/
    agent/
      role.marg          -> includes "atoms/agent/..."
      tools.marg         -> includes "atoms/agent/..."
  atoms/
    agent/
      identity.marg
      capabilities.marg
```

This structure makes it obvious that all includes use the full path from `templates/`.

## Error Handling

Always handle include errors gracefully:

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer


def safe_render(template_content: str, context: dict, base_path: Path) -> str:
    """Safely render a template with error handling."""
    try:
        parser = Parser()
        _, nodes = parser.parse(template_content)

        renderer = Renderer(context=context, base_path=base_path)
        return renderer.render(nodes)

    except FileNotFoundError as e:
        # Handle missing include files
        print(f"Warning: Include file not found - {e}")
        return template_content  # Return unrendered template

    except Exception as e:
        # Handle other rendering errors
        print(f"Error rendering template: {e}")
        return ""


# Usage
result = safe_render(
    '{% include "optional_snippet.marg" %}\nMain content.',
    context={},
    base_path=Path("./templates")
)
```

## Best Practices

### 1. Organize Snippets by Purpose

```
templates/
  snippets/
    system/
      role_definitions.marg
      safety_guidelines.marg
    formatting/
      json_output.marg
      markdown_output.marg
    examples/
      few_shot_classification.marg
      few_shot_extraction.marg
    sections/
      header.marg
      footer.marg
```

### 2. Use Descriptive Naming

```python
# Good: Clear, descriptive names
{% include "snippets/system/expert_role.marg" %}
{% include "snippets/formatting/structured_json_output.marg" %}

# Avoid: Vague names
{% include "snippets/s1.marg" %}
{% include "snippets/format.marg" %}
```

### 3. Keep Snippets Focused

Each snippet should have a single, clear purpose:

```margarita
# Good: Focused snippet
# file: role_definition.marg
You are a {{role}} with expertise in {{domain}}.
```

```margarita
# Avoid: Mixing multiple concerns
# file: everything.marg
You are a {{role}}.
Task: {{task}}
Output format: {{format}}
```

### 4. Document Snippet Context Requirements

Add metadata to snippets documenting required context variables:

```margarita
---
name: role-definition
version: 1.0.0
required_context:
  - role
  - domain
  - expertise_level
---

You are a {{role}} with {{expertise_level}} expertise in {{domain}}.
```

### 5. Cache Parsed Templates

Parse templates once, render many times:

```python
class OptimizedRenderer:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.parser = Parser()
        self.parsed_cache = {}

    def get_nodes(self, template_content: str):
        cache_key = hash(template_content)

        if cache_key not in self.parsed_cache:
            _, nodes = self.parser.parse(template_content)
            self.parsed_cache[cache_key] = nodes

        return self.parsed_cache[cache_key]

    def render(self, template_content: str, context: dict) -> str:
        nodes = self.get_nodes(template_content)
        renderer = Renderer(context=context, base_path=self.template_dir)
        return renderer.render(nodes)
```

## Real-World Example: Multi-Agent System

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer


class AgentPromptBuilder:
    """Build prompts for different agent types using snippets."""

    def __init__(self, snippets_dir: Path):
        self.snippets_dir = snippets_dir
        self.parser = Parser()

    def build_agent_prompt(
            self,
            agent_type: str,
            task: str,
            context: dict
    ) -> str:
        """Build a prompt for a specific agent type."""

        # Map agent types to snippet combinations
        snippet_map = {
            "researcher": [
                "roles/researcher.marg",
                "capabilities/web_search.marg",
                "output/structured_findings.marg"
            ],
            "analyzer": [
                "roles/analyzer.marg",
                "capabilities/data_analysis.marg",
                "output/insights_report.marg"
            ],
            "writer": [
                "roles/writer.marg",
                "capabilities/content_creation.marg",
                "output/polished_text.marg"
            ]
        }

        snippets = snippet_map.get(agent_type, [])

        # Build the main template
        template = "\n\n".join([
            f'{{% include "{snippet}" %}}'
            for snippet in snippets
        ])

        template += f"\n\n## Current Task\n\n{task}"

        # Render
        _, nodes = self.parser.parse(template)
        renderer = Renderer(
            context=context,
            base_path=self.snippets_dir
        )

        return renderer.render(nodes)


# Usage
builder = AgentPromptBuilder(Path("./agent_snippets"))

# Build a researcher agent prompt
researcher_prompt = builder.build_agent_prompt(
    agent_type="researcher",
    task="Find the latest developments in quantum computing",
    context={
        "expertise": "quantum physics",
        "sources": ["arxiv", "google scholar"],
        "depth": "comprehensive"
    }
)

# Build an analyzer agent prompt
analyzer_prompt = builder.build_agent_prompt(
    agent_type="analyzer",
    task="Analyze customer feedback trends",
    context={
        "data_source": "customer_reviews.json",
        "analysis_type": "sentiment",
        "output_format": "executive_summary"
    }
)
```
