# Basic Python Usage

First, import the necessary components:

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer
```

Render a template programmatically:

```python
# Define your template
template = """
<<
You are a helpful assistant.

### This is markdown like syntax and supports markdown features.
I'm a list of things:
- Item 1
- Item 2
- Item 3

You can insert variables with the dollar sign
Task: ${task}
>>

<< Markdown can be in a single line like this too >>

// Comments are supported like this and ignored during rendering
// Conditional blocks are supported
if context:
    <<
    Context:
        ${context}
    >>

// Loops are supported
for item in items:
    << Item=${item} >>
"""

# Parse the template
parser = Parser()
metadata, nodes = parser.parse(template)

# Create a renderer with context
renderer = Renderer(context={
    "task": "Summarize the key points",
    "context": "User is researching AI agents"
})

# Render the output
prompt = renderer.render(nodes)
print(prompt)
```
