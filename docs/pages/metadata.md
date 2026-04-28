# Metadata

Templates may declare metadata at the top using `key: value` lines. This metadata can hold task information, ownership, or any other small key/value pairs that help describe the template's purpose.

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
