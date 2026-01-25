# Contexts

Contexts are plain JSON objects that supply variables to templates. Keys map to template variables and can include nested objects and arrays.

Example context

```json
{
  "name": "Batman",
  "user": { "id": 42, "active": true },
  "items": ["a", "b", "c"]
}
```

Rendered result

Given the following template:

```margarita
<<
Hello, ${name}! (id=${user.id}, active=${user.active})
>>
```

Rendering with the example context produces:

```text
Hello, Batman! (id=42, active=True)
```

See also: `Metadata` page for template header metadata and usage.

Behavior and precedence

- CLI `-c` (inline JSON) and `-f` (context file) override auto-detected context files.
- When rendering a single template, MARGARITA looks for a sibling `.json` file with the same base name.
- Metadata is parsed from the template and can be shown with `margarita render --show-metadata` or `margarita metadata`.

Tip: Keep contexts explicit and small; prefer using a context file in CI to ensure reproducible renders.
