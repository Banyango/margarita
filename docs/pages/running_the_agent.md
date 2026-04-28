# Running the Agent

## Requirements

You can choose between the following model backends for running your agents:

- Ollama [installation instructions](https://ollama.com/docs/installation)
- GitHub Copilot. You will need the [Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/install-copilot-cli) installed and configured.

See here for instructions on [switching between backends](model_backends.md)

> **Note:** We're working on adding support for more models and providers in the future. If you have a specific model or provider you'd like to see supported, please let us know by creating an issue in our GitHub repository.

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

# Naming the Runs

If you supply a parameter after `@effect run`, that parameter will be used as the name of the run.


```mgx
---
description: Hello world agent template
---

<<
# Hello World

Tell the user Hello, and welcome them to Margarita!
>>

@effect run Hello World
```
