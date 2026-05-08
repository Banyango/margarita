# MGX Agent Templates

`.mgx` files extend `.mg` Margarita templates with agentic capabilities: Python imports, `@state`, `@memory`, `@effect` directives, and agent execution.

Run them with:

```bash
margarita run example.mgx
```

# Features

- Includes, conditionals, loops, and variable interpolation.
- `@state` — Define variables accessible by the agent during a run or fill them into the context before a run.
- `${var}` — Syntax to access state variables in the template.
- `@memory` — Persist variables to disk.
- `@effect` — Give commands to the agent: define tools, run the agent, collect input, manage context, log output, and more.
- Python imports (`from my_module import fn`).


See the [Agent](running_the_agent.md) section for full documentation on `@state`, `@memory`, `@effect`, and more.

# Supported Backends

- Ollama (local)
- GitHub Copilot
- Claude API
- OpenAI API
