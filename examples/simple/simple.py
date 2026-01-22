from margarita.parser import Parser
from margarita.renderer import Renderer

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
parser = Parser()
metadata, nodes = parser.parse(template)

# Create a renderer with context
renderer = Renderer(
    context={"task": "Summarize the key points", "context": "User is researching AI agents"}
)

# Render the output
prompt = renderer.render(nodes)
print(prompt)
