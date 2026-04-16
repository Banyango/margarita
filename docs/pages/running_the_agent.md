# Running the Agent

## Installation

Run the following command to run a `.mgx` file without a permanent install:

```sh
uvx margarita run hello.mgx
```

To install as a persistent tool:

```sh
uv tool install margarita
```

## Requirements

Margarita's agent runner uses GitHub Copilot. You will need the [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli) installed and configured.

## Your first agent template

Create a file named `hello.mgx`:

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

Run it with:

```bash
margarita run hello.mgx
```

The `<< >>` block loads markdown content into the agent's context. `@effect run` tells the agent to execute with the current context.

## Specify the model

Add a `model` field to the template metadata:

```mgx
---
model: "gpt-4"
---

<< test >>

@effect run
```
