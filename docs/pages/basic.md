# Basic Python Usage

First, import the necessary components:

```python
from pathlib import Path
from pmd.parser import PMDParser
from pmd.renderer import PMDRenderer
```

Render a template programmatically:

```python
# Define your template
template = """
You are a helpful assistant.

Task: {{task}}

{% if context %}
Context:
{{context}}
{% endif %}

Please provide a detailed response.
"""

# Parse the template
parser = PMDParser()
metadata, nodes = parser.parse(template)

# Create a renderer with context
renderer = PMDRenderer(context={
    "task": "Summarize the key points",
    "context": "User is researching AI agents"
})

# Render the output
prompt = renderer.render(nodes)
print(prompt)
```
