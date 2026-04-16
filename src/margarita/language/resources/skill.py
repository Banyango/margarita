skill = """---
name: margarita
description: Work with Margarita (.mg) templates — creating, editing, rendering, and debugging them. Use this skill whenever the user mentions .mg files, Margarita templates, margarita render, uvx margarita, prompt templates with variables/conditionals/loops, or wants to compose LLM prompts from template files. Also trigger when the user wants to render a template, pass context to a template, use the margarita Python library, or asks how any Margarita syntax works.
---

# Margarita Skill

Margarita is a lightweight markup language for writing, composing, and rendering structured LLM prompts. Templates (`.mg` files) extend Markdown with variables, conditionals, loops, and includes, and render to plain Markdown.

## CLI Quick Reference

```bash
# Render a template (context auto-detected from same-name .json file)
uvx margarita render template.mg

# Render with inline JSON context
uvx margarita render template.mg -c '{"name": "Alice"}'

# Render with a context file
uvx margarita render template.mg -f context.json

# Show metadata
uvx margarita metadata template.mg

# Render and show metadata
uvx margarita render template.mg --show-metadata
```

## Template Syntax

Read `references/syntax.md` for the full syntax reference — markdown blocks, variables, conditionals, loops, includes, metadata, context format, template patterns, and troubleshooting tips.

## Rendering Workflow

1. Identify what variables the template needs (look for `${...}` references).
2. Build a JSON context object satisfying all required variables.
3. Render: `uvx margarita render template.mg -c '{"key": "value"}'`
4. Use the rendered Markdown output as the prompt.

If a `.json` file with the same base name as the template exists in the same directory, Margarita will use it automatically — no `-c` flag needed.
"""
