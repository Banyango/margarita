syntax = """# Margarita Template Syntax Reference

## Markdown Blocks
**All markdown content MUST be wrapped in `<< >>`.**
Text outside `<< >>` (other than control flow lines and comments) is ignored during rendering.

Single-line and multi-line forms are both supported:
```
<< This is a single-line markdown block. >>

<<
You are a helpful assistant.

Task: ${task}
>>
```

Variables inside `<< >>` are interpolated. Common mistake: placing markdown or variables outside `<< >>` — they will silently produce no output.

## Comments
```
// This is a comment — ignored during rendering
```

## Variables
Use `${var_name}` to inject context values. Supports dotted paths for nested objects.
```
Hello, ${name}!
You have ${user.count} messages.
User active: ${user.active}
```

No spaces around the variable name — `${ var }` will not be replaced.

## Conditionals
Python-inspired `if / elif / else`. Missing, false, null, empty string, and 0 are falsy.
```
if is_admin:
    << Welcome, Admin ${name}! >>
elif status == "premium":
    << Welcome, Premium user ${name}! >>
else:
    << Welcome, ${name}! >>
```

Nested conditionals are supported. Indent each level consistently.

## Loops
```
for item in items:
    <<
    - ${item}
    >>
```

Range loops:
```
for i in range(3):        // 0, 1, 2
for i in range(1, 4):     // 1, 2, 3
for i in range(0, 10, 2): // 0, 2, 4, 6, 8
```

Access the loop variable with `${item}` (or whatever name you choose). Nested loops are supported.

## Includes
Reuse template fragments. Paths are relative to the including template's directory.
```
[[ header ]]                 // includes header.mg
[[ greeting.mg ]]            // explicit extension
[[ greeting name="Alice" ]]  // pass override variables
[[ partials/header ]]        // subdirectory path
```

Included templates only see variables explicitly passed as parameters — they do not inherit the parent's context.
Avoid circular includes — Margarita does not detect them and will loop forever.

## Metadata
Optional YAML-like header between `---` markers at the top of the file:
```
---
title: "My Prompt"
version: "1.0"
author: "Alice"
---

<< Hello, ${name}! >>
```

## Context Format
Context is a JSON object. Keys map to template variables. Supports nested objects and arrays.

```json
{
  "name": "Alice",
  "is_admin": true,
  "status": "premium",
  "user": { "id": 42, "active": true },
  "items": ["apple", "banana", "cherry"]
}
```

## Template Patterns

**Simple prompt:**
```
<<
Hello, ${name}!
Your role is ${role}.
>>
```

**Conditional sections:**
```
<< You are a helpful assistant. >>

if json_output:
    <<
    Respond ONLY with valid JSON. No prose.
    >>
else:
    << Respond in plain English. >>
```

**Composing from includes:**
```
[[ system_role ]]
[[ task_instructions ]]

if include_examples:
    [[ examples ]]
```

**Loop over items:**
```
<<
Review the following items:
>>
for item in items:
    <<
    - ${item}
    >>
```

## Troubleshooting

- **Content missing from output**: Markdown and variables must be inside `<< >>` — text written outside these delimiters is silently ignored.
- **Variable not replaced**: Check spelling matches the context key exactly (case-sensitive). No spaces around the name — `${ var }` will not work.
- **Conditional not triggering**: `0`, `""`, `null`, `false`, and missing keys are all falsy.
- **Include not found**: Path is relative to the template's own directory. Use `[[ partials/header ]]` for files in subdirectories.
- **Circular include**: Margarita does not detect these — it will loop forever. Avoid including files that include each other.
"""
