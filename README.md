# MARGARITA

[![PyPI version](https://badge.fury.io/py/margarita.svg)](https://badge.fury.io/py/margarita)
[![Python Support](https://img.shields.io/pypi/pyversions/margarita.svg)](https://pypi.org/project/margarita/)

Margarita is a lightweight markup language and Python library for writing, composing, and rendering structured LLM prompts.

It renders out to Markdown format by default so you can use this anywhere Markdown is supported.

Margarita extends Markdown with templating features like variables, conditionals, loops, and includes, making it easy to create dynamic prompts for large language models (LLMs).

| FOR NOW! CLI tool is WIP you will need to download the source and install it locally to use the `margarita` command. |

## Features

- ✨ Framework agnostic — works with any LLM or API
- 🚀 Composable — prompts can be split, reused, and nested
- 🎯 Static-first — templates are validated before execution
- 📦 Metadata — version, and provide metadata alongside your prompts.

## Get Started

Here's a Hello World example. helloworld.mg contains the template, and helloworld.json contains the data.

```markdown:helloworld.mg
// file:helloworld.mg
<<
Hello, {{name}}!
Welcome to Margarita templating.
>>
```

```json:helloworld.json
// file:helloworld.json

{
    "name": "World"
}
```

**Run the following command:**
```shell
margarita render helloworld.mg
```

**Output:**

```markdown
Hello, World!
Welcome to Margarita templating.
```

## Conditionals Example

```markdown:conditional_example.mg
// file:conditional_example.mg

if is_admin:
    <<Welcome, Admin ${name}>>
else:
    <<Welcome, User {{name}}!>>
```

## Includes

```margarita
// file: role_example.mg
You are a fancy AI assistant.
```

```margarita
// files:json_output_format_template.mg
<<
Output the response in the following JSON format:
{
    "response": "<your response here>"
}
>>
```

```margarita
// file:include_example.mg
[[ role ]]

if output_json:
    [[ json_output_format_template ]]
```

### Passing Context
You can pass context variables to your templates to make them dynamic.

```margarita
// file:role.mg
You are a ${ type } AI assistant.
```

```margarita
// file:context_example.mg
[[ role type="fancy" ]]
```

## Metadata

Organize your templates with metadata headers.

```margarita
// file:metadata_example.mg
---
title: "Greeting Template"
version: "1.0"
author: "Batman"
---
<<
Hello, {{name}}!
Welcome to Margarita templating.
>>
```

## Python Library

Install the package via pip/poetry/uv/etc or whatever package manager you prefer:

```bash
pip install margarita
poetry add margarita
uv add margarita
```

Use the library in your Python code:

```python
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
```

Use the Composer to manage multiple templates:

```python
from margarita.composer import Composer
from pathlib import Path

manager = Composer(Path("./templates"))

# Compose a complex prompt from multiple snippets
prompt = manager.compose_prompt(
    snippets=[
        "snippets/system_role.mg",
        "snippets/task_context.mg",
        "snippets/chain_of_thought.mg",
        "snippets/output_format.mg"
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

## Documentation

Full documentation is available at https://banyango.mgithub.io/margarita/latest

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Setup Development Environment

```bash
uv sync # Install dependencies
```

### Running Tests

```bash
# Run tests with pytest
uv run pytest

# Run tests with coverage
uv run pytest --cov=margarita --cov-report=html
```

### Code Quality

```bash
# Format code with ruff
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking with mypy
uv run mypy src/margarita
```

### Building the Package

```bash
# Build the package
uv build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to:
- Update tests as appropriate
- Follow the existing code style
- Update documentation for any changed functionality

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **Kyle Reczek** - *Initial work* - [Banyango](https://github.com/Banyango)

## Acknowledgments

- Markdown

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.

## Support

If you encounter any problems or have questions, please [open an issue](https://github.com/yourusername/margarita/issues).

