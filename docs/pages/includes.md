# Using Includes in Python API

PMD's include functionality allows you to compose templates from reusable snippets, making it easy to build modular, maintainable prompt libraries. This page covers how to use includes programmatically through the Python API.

## Basic Include Usage

### Setting Up the Renderer

The key to using includes is setting the `base_path` parameter when creating a `PMDRenderer`. This tells PMD where to resolve relative include paths:

```python
from pathlib import Path
from pmd.parser import PMDParser
from pmd.renderer import PMDRenderer

# Define base path for includes
template_dir = Path("./templates")

# Parse your main template
parser = PMDParser()
template_content = """
{% include "header.pmd" %}

Main content here.

{% include "footer.pmd" %}
"""

metadata, nodes = parser.parse(template_content)

# Create renderer with base_path
renderer = PMDRenderer(
    context={"app_name": "MyApp"},
    base_path=template_dir
)

# Render - includes will be resolved relative to base_path
output = renderer.render(nodes)
```

## Creating Reusable Snippets

### Example: Prompt Building Blocks

Create a library of reusable prompt components:

**templates/snippets/system_role.pmd**:
```pmd
You are {{role}}, a helpful AI assistant.
```

**templates/snippets/task_context.pmd**:
```pmd
## Task Context

User: {{user_name}}
Session: {{session_id}}
Timestamp: {{timestamp}}
```

**templates/snippets/output_format.pmd**:
```pmd
## Output Requirements

- Provide responses in {{format}} format
- Keep responses {{length}}
- Use {{tone}} tone
```

### Using the Snippets

```python
from pathlib import Path
from pmd.parser import PMDParser
from pmd.renderer import PMDRenderer

# Main template that composes snippets
main_template = """
{% include "snippets/system_role.pmd" %}

{% include "snippets/task_context.pmd" %}

## User Request

{{user_request}}

{% include "snippets/output_format.pmd" %}
"""

# Parse and render
parser = PMDParser()
_, nodes = parser.parse(main_template)

renderer = PMDRenderer(
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

### Template Manager Pattern

Build a template manager class to handle snippet loading and caching:

```python
from pathlib import Path
from typing import Dict, Optional
from pmd.parser import PMDParser
from pmd.renderer import PMDRenderer


class TemplateManager:
    """Manage PMD templates and snippets with caching."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.parser = PMDParser()
        self._template_cache: Dict[str, tuple] = {}

    def load_template(self, template_path: str) -> tuple:
        """Load and parse a template file with caching."""
        cache_key = str(template_path)

        if cache_key not in self._template_cache:
            full_path = self.template_dir / template_path
            content = full_path.read_text()
            parsed = self.parser.parse(content)
            self._template_cache[cache_key] = parsed

        return self._template_cache[cache_key]

    def render(self, template_path: str, context: dict) -> str:
        """Render a template with the given context."""
        _, nodes = self.load_template(template_path)

        renderer = PMDRenderer(
            context=context,
            base_path=self.template_dir
        )

        return renderer.render(nodes)

    def compose_prompt(
        self,
        snippets: list[str],
        context: dict,
        separator: str = "\n\n"
    ) -> str:
        """Compose a prompt from multiple snippet files."""
        parts = []

        for snippet in snippets:
            rendered = self.render(snippet, context)
            parts.append(rendered)

        return separator.join(parts)


# Usage
manager = TemplateManager(Path("./templates"))

# Compose a complex prompt from multiple snippets
prompt = manager.compose_prompt(
    snippets=[
        "snippets/system_role.pmd",
        "snippets/task_context.pmd",
        "snippets/chain_of_thought.pmd",
        "snippets/output_format.pmd"
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
# Template with conditional includes
template = """
{% include "snippets/system_role.pmd" %}

{% if use_examples %}
{% include "snippets/few_shot_examples.pmd" %}
{% endif %}

## Task

{{task}}

{% if detailed_output %}
{% include "snippets/detailed_format.pmd" %}
{% else %}
{% include "snippets/brief_format.pmd" %}
{% endif %}
"""

parser = PMDParser()
_, nodes = parser.parse(template)

# Render with detailed mode
renderer = PMDRenderer(
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

Includes can reference other includes, creating a hierarchy of snippets:

**templates/snippets/complete_prompt.pmd**:
```pmd
{% include "header_section.pmd" %}

{% include "body_section.pmd" %}

{% include "footer_section.pmd" %}
```

**templates/snippets/header_section.pmd**:
```pmd
{% include "system_role.pmd" %}

{% include "safety_guidelines.pmd" %}
```

```python
# All nested includes are resolved automatically
parser = PMDParser()
_, nodes = parser.parse('{% include "snippets/complete_prompt.pmd" %}')

renderer = PMDRenderer(
    context={"role": "assistant"},
    base_path=Path("./templates")
)

# Renders the complete hierarchy
output = renderer.render(nodes)
```

## Error Handling

Always handle include errors gracefully:

```python
from pathlib import Path
from pmd.parser import PMDParser
from pmd.renderer import PMDRenderer


def safe_render(template_content: str, context: dict, base_path: Path) -> str:
    """Safely render a template with error handling."""
    try:
        parser = PMDParser()
        _, nodes = parser.parse(template_content)

        renderer = PMDRenderer(context=context, base_path=base_path)
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
    '{% include "optional_snippet.pmd" %}\nMain content.',
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
      role_definitions.pmd
      safety_guidelines.pmd
    formatting/
      json_output.pmd
      markdown_output.pmd
    examples/
      few_shot_classification.pmd
      few_shot_extraction.pmd
    sections/
      header.pmd
      footer.pmd
```

### 2. Use Descriptive Naming

```python
# Good: Clear, descriptive names
{% include "snippets/system/expert_role.pmd" %}
{% include "snippets/formatting/structured_json_output.pmd" %}

# Avoid: Vague names
{% include "snippets/s1.pmd" %}
{% include "snippets/format.pmd" %}
```

### 3. Keep Snippets Focused

Each snippet should have a single, clear purpose:

```pmd
# Good: Focused snippet
# file: role_definition.pmd
You are a {{role}} with expertise in {{domain}}.
```

```pmd
# Avoid: Mixing multiple concerns
# file: everything.pmd
You are a {{role}}.
Task: {{task}}
Output format: {{format}}
```

### 4. Document Snippet Context Requirements

Add metadata to snippets documenting required context variables:

```pmd
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
        self.parser = PMDParser()
        self.parsed_cache = {}

    def get_nodes(self, template_content: str):
        cache_key = hash(template_content)

        if cache_key not in self.parsed_cache:
            _, nodes = self.parser.parse(template_content)
            self.parsed_cache[cache_key] = nodes

        return self.parsed_cache[cache_key]

    def render(self, template_content: str, context: dict) -> str:
        nodes = self.get_nodes(template_content)
        renderer = PMDRenderer(context=context, base_path=self.template_dir)
        return renderer.render(nodes)
```

## Real-World Example: Multi-Agent System

```python
from pathlib import Path
from pmd.parser import PMDParser
from pmd.renderer import PMDRenderer


class AgentPromptBuilder:
    """Build prompts for different agent types using snippets."""

    def __init__(self, snippets_dir: Path):
        self.snippets_dir = snippets_dir
        self.parser = PMDParser()

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
                "roles/researcher.pmd",
                "capabilities/web_search.pmd",
                "output/structured_findings.pmd"
            ],
            "analyzer": [
                "roles/analyzer.pmd",
                "capabilities/data_analysis.pmd",
                "output/insights_report.pmd"
            ],
            "writer": [
                "roles/writer.pmd",
                "capabilities/content_creation.pmd",
                "output/polished_text.pmd"
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
        renderer = PMDRenderer(
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
