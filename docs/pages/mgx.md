# MGX Agent Templates

`.mgx` files extend `.mg` Margarita templates with agentic capabilities: Python imports, `@state`, `@memory`, `@effect` directives, and agent execution.

Run them with:

```bash
margarita run example.mgx
```

# Features

- All the features of `.mg` Margarita templates: includes, conditionals, loops, and variable interpolation.
- Python imports (`from my_module import fn`).
- `@state` — define variables accessible by the agent during a run.
- `@memory` — persist variables across runs via `memory.json`.
- `@effect` — give commands to the agent: define tools, run the agent, manage context, log output, and more.

# Example

```mgx
---
description: "Example agent template"
---

// Import Python functions
from math import add, subtract, multiply, load_files

// Load context into the agent
<<
You are an expert mathematician.
Your task is to solve addition problems accurately and efficiently.
>>

// Include other Margarita files
[[ create-a-react-component ]]

// Run a Python function and store the result in state
@effect func add(12, test.data) => result

// Conditionally add more context
if result != 24:
    <<
    The addition tool did not return the expected result.
    Expected: 24
    Got: ${result}
    >>

@state result = {}

// Register tools for the agent
@effect tools add(x: int, y: int) => int
@effect tools subtract(x: int, y: int) => int

// Run the agent
@effect run

// Clear context and tools after running
@effect context clear
@effect tools clear

<<
Validate the following:
- The addition tool correctly adds two numbers.
- The subtraction tool correctly subtracts two numbers.
>>

if result.failed:
    <<
    The test failed. Please review the implementation.
    >>
```

See the [Agent](running_the_agent.md) section for full documentation on `@state`, `@memory`, `@effect`, and more.
