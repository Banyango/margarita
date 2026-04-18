# MGX Agent Templates

`.mgx` files extend `.mg` Margarita templates with agentic capabilities: Python imports, `@state`, `@memory`, `@effect` directives, and agent execution.

Run them with:

```bash
margarita run example.mgx
```

# Features

- All the features of `.mg` Margarita templates: includes, conditionals, loops, and variable interpolation.
- Python imports (`from my_module import fn`).
- `${var}` syntax to access Python variables in the template.
- `@state` — define variables accessible by the agent during a run.
- `@memory` — persist variables across runs via `memory.json`.
- `@effect` — give commands to the agent: define tools, run the agent, collect input, manage context, log output, and more.


See the [Agent](running_the_agent.md) section for full documentation on `@state`, `@memory`, `@effect`, and more.
