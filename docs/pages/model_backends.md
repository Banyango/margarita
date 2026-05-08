# Model Backends

## Overview
Margarita supports multiple model backends, allowing you to choose the one that best fits your needs. The available backends include:

> Note: We're adding more backends all the time! If you have a specific model or provider you'd like to see supported, please let us know by creating an issue in our GitHub repository.

- **Ollama**: A local model backend that runs on your machine.
- **GitHub Copilot**: A cloud-based model backend that integrates with GitHub's
- **Claude API**: A cloud-based model backend that integrates with the Claude API.
- **OpenAI API**: A cloud-based model backend that integrates with the OpenAI API.

## Switching Between Backends

Use the following command to switch between model backends:

`margarita use <backend_name>`

> Some models require the model name to be in the metadata section. You will get an error if you are missing this.

To specify the model name, add it to the metadata section of your `.mgx` file:

```margarita
---
model: ollama:your_model_name
---
```

## Ollama
Ollama is a local model backend that allows you to run language models on your machine.

`margarita use ollama`

ollama requires that you have the Ollama software installed and set up on your machine. You can find installation instructions in the [Ollama documentation](https://ollama.com/docs/installation).


## GitHub Copilot

`margarita use copilot`

To use GitHub Copilot download the Copilot CLI and log in to the cli then you should be able to use Margarita.

## Claude API

`margarita use claude`

set your `CLAUDE_CODE_OAUTH_TOKEN` environment variable to your Claude API key

## OpenAI API

`margarita use openai`

set your `OPENAI_API_KEY` environment variable to your OpenAI API key
