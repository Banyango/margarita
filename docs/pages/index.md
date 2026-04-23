# MARGARITA

> What if you could write agents as easily as you write Markdown?

Margarita is a simple scripting language that lets you compose, use logic, and build agents all with simple syntax that's as easy to use as Markdown is.

Key features

- Support Composable templates that can be split, reused, and nested
- Support Logic with conditionals and loops for dynamic sections
- Requires GitHub Copilot for agentic capabilities (coming soon: support for other LLMs and local execution)

## Quick Start

Create `hello.mgx` containing:

```margarita
@state name = "Margarita"

<<
Hello, ${name}!
>>

@effect run
```

then run `margarita run hello.mgx` to see the output:

```text
Hello, Margarita!
```

Congrats you've just run your first agent!

Get started with the [Templating Language](mg.md)
or the [Running the Agent](mgx.md)
