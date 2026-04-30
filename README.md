# MARGARITA

[![Discord](https://img.shields.io/discord/1499236997057744986?label=Discord&logo=discord)](https://discord.gg/W9kJWqFnYp)
[![PyPI version](https://badge.fury.io/py/margarita.svg)](https://badge.fury.io/py/margarita)
[![Python Support](https://img.shields.io/pypi/pyversions/margarita.svg)](https://pypi.org/project/margarita/)


www.margarita.run

Margarita aims to make writing Agents as easy as writing Markdown.

It provides two file formats:

- **`.mg`** — A templating language that renders dynamic prompts to Markdown. Extends Markdown with variables, conditionals, loops, and includes.
- **`.mgx`** — An agent scripting language that extends `.mg` with agentic execution: state, memory, tool calls, user input, and more.


## Features

- Agentic execution — run `.mgx` scripts as stateful agents with memory and tool calls in a TUI.
- Composable — .mg files can be split, reused, and nested with `[[ include.mg ]]` syntax.
- Logical structures — conditionals and loops for dynamic prompt generation. `if`, `else`, `elif`, and `for` blocks supported.
- Context management — manage agent context with `@effect context`.
- Memory — persist variables across runs with `@memory`.
- Input — prompt the user for input during a run with `@effect input`.
- Tools — register Python functions as LLM-callable tools with `@effect tools`.
- Function calls — execute Python functions directly and save their result to state with `@effect func`.
- Sub Agents — call other `.mgx` files as sub-agents with `@effect exec`.
- Metadata — attach version and description metadata alongside your prompts. `parameters` field for defining expected context variables.

## Requirements

- A Github Copilot subscription or Ollama installed locally is required to use the agentic features of Margarita (i.e. to run `.mgx` files). We're working on adding more llm backends currently.

# Installation

Run the following command to install Margarita using uv:

```shell
uv tool install margarita

margarita use ollama

margarita run example.mgx
```


---

# `.mg` — Prompt Templates

`.mg` files are Margarita templates. They render to plain Markdown and can be used anywhere Markdown is supported.

## Hello World

```margarita
// file: helloworld.mgx
@state name = "World"

<<
Hello, ${name}!
Welcome to Margarita templating.
>>

@effect run
```


## Conditionals

```margarita
if is_admin:
    << Welcome, Admin ${name}! >>
else:
    << Welcome, User ${name}! >>
```

## Loops

```margarita
<< # Items >>
for item in items:
    <<
    - ${item}
    >>
```

Range loops are also supported:

```margarita
for i in range(3):
    << Step ${i} >>
```

## Includes

Split prompts into reusable fragments and compose them:

```margarita
// file: role.mg
<< You are a ${type} AI assistant. >>
```

```margarita
// file: prompt.mg
[[ role type="helpful" ]]

if output_json:
    [[ json_output_format ]]
```

## Metadata

```margarita
---
title: "Greeting Template"
version: "1.0"
author: "Batman"
---

<<
Hello, ${name}!
Welcome to Margarita templating.
>>
```

## CLI Reference

```shell
# Render a template
margarita render template.mg

# Render with inline JSON context
margarita render template.mg -c '{"name": "Alice"}'

# Render with a context file
margarita render template.mg -f context.json

# Render a directory of .mg files
margarita render templates/ -o output/

# Show metadata
margarita metadata template.mg

# Render and show metadata
margarita render template.mg --show-metadata
```


---

# `.mgx` — Agent Templates

`.mgx` files extend `.mg` templates with agentic capabilities: Python imports, `@state`, `@memory`, `@effect` directives, and agent execution.

Run them with:

```bash
margarita run example.mgx
```

> **Note:** Margarita's agent runner uses [GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli). You will need it installed and configured.

## Hello World Agent

```mgx
---
description: Hello world agent template
---

<<
# Hello World

Tell the user Hello, and welcome them to Margarita!
>>

@effect run
```

The `<< >>` block loads Markdown content into the agent's context. `@effect run` tells the agent to execute with the current context.

## State

Define variables accessible during a run with `@state`:

```mgx
@state count = 0

<< Set the count variable to 5. >>

@effect run
```

## Memory

Persist variables across runs with `@memory`. Values are saved to `memory.json` at the end of each run and loaded at the start of the next:

```mgx
@memory var favorite_color

<<
If favorite_color is not set, set it to "blue".
Otherwise log "The user's favorite color is ${favorite_color}".
>>

@effect run
```

## Custom Tools

Register Python functions as LLM-callable tools with `@effect tools`:

```mgx
from math import add, AddParams

<< Add 3 and 5. >>

@effect tools add(x: AddParams) => result

@effect run
```

> **Note:** Tool params must be a valid Pydantic model.

## Function Calls

Execute Python functions directly (without an LLM tool call) and save their result to state:

```mgx
from my_module import compute

@effect func compute(x) => result
```

## User Input

Prompt the user for input during a run:

```mgx
@effect input "What is your favorite color?" => favorite_color

@effect log "The user's favorite color is ${favorite_color}."
```

## Specify the Model

```mgx
---
model: "gpt-4"
---

<< Your prompt here. >>

@effect run
```


---

# Python Library

Install via pip, poetry, uv, or any package manager:

```bash
pip install margarita
poetry add margarita
uv add margarita
```

## Basic Usage

```python
from margarita.parser import Parser
from margarita.renderer import Renderer

template = """
<<
You are a helpful assistant.

Task: ${task}
>>
if context:
    <<
    Context:
        ${context}
    >>

<< Please provide a detailed response. >>
"""

parser = Parser()
metadata, nodes = parser.parse(template)

renderer = Renderer(
    context={"task": "Summarize the key points", "context": "User is researching AI agents"}
)

prompt = renderer.render(nodes)
print(prompt)
```

## Composer

Use the Composer to build prompts from multiple template fragments:

```python
from margarita.composer import Composer
from pathlib import Path

manager = Composer(Path("./templates"))

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


---

## Documentation

Full documentation is available at https://banyango.github.io/margarita/latest

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Setup

```bash
make install
```

### Tests

```bash
make test
```

### Code Quality

```bash
make format
make lint
```

### Build

```bash
uv build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

<!--
Put [Margarita] at the end of the PR description.
-->

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please make sure to:
- Update tests as appropriate
- Follow the existing code style
- Update documentation for any changed functionality

## Authors

- **Kyle Reczek** - *Initial work* - [Banyango](https://github.com/Banyango)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.

## Support

If you encounter any problems or have questions, please [open an issue](https://github.com/banyango/margarita/issues).
