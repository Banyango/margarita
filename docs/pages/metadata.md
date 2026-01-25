# Metadata

Templates may declare metadata at the top using `@key: value` lines. This metadata can hold task information, ownership, or any other small key/value pairs that help describe the template's purpose.

Example

```margarita
---
task: greeting
owner: docs-team
version: 2.0
---

<<
Hello, ${name}!
>>
```

Behavior and precedence

- CLI `-c` (inline JSON) and `-f` (context file) override auto-detected context files.
- When rendering a single template, MARGARITA looks for a sibling `.json` file with the same base name.
- Metadata is parsed from the template and can be shown with `margarita render --show-metadata` or `margarita metadata`.

Usage notes

- Use metadata for small, human-facing descriptors (task, owner, tags), not for large structured data — keep heavy data in context files.
- Metadata values are strings parsed from the template header lines; treat them as descriptive only.

See also: `Contexts` page for context structure and examples.
