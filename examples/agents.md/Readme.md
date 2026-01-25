# Multi-Model Agent Prompts with Margarita

## The Problem: Model-Specific Prompt Guidelines

Different LLM providers have different prompt engineering guidelines that can significantly impact performance:

- **GPT-5 Guidelines** explicitly recommend **avoiding ALL CAPS words** in prompts, as the model may interpret them as shouting or overemphasis
- **Claude Guidelines** do not have this restriction and in some cases ALL CAPS can be effective for emphasis

This creates a challenge: if you maintain a single `Agents.md` file for your agent system, you cannot optimize for both models simultaneously. Using ALL CAPS might hurt GPT-5 performance, while avoiding them might reduce clarity for Claude.

## The Solution: Model-Specific Templates with Margarita

Margarita allows you to maintain **separate template files** for each model and use **conditionals** to render the appropriate version based on your target model.

## Example Setup

Let's create an agent system that adapts to different models by keeping model-specific prompts in separate files:

### Directory Structure

```
agents/
├── agents.mg          # Main template with conditional includes
└── chatgpt5/
    ├── system.mg
    ├── responsibilities.mg
    ├── tools.mg
    └── response_format.mg
└── claude/
    ├── system.mg
    ├── responsibilities.mg
    ├── tools.mg
    └── response_format.mg
```
 ### Usage

`margarita render agents/agents.mg -c '{"model": "gpt5"}'`

This command will render the agent prompts optimized for GPT-5, avoiding ALL CAPS words as per its guidelines. To switch to Claude, simply change the context:

`margarita render agents/agents.mg -c '{"model": "claude"}'`
