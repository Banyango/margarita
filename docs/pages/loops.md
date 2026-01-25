# Loops

Render lists and repeat sections using `for` loops.

Syntax

```margarita
<< # Items >>
for item in items
    <<
    - {{item}}
    >>
```

Example context

```json
{ "items": ["apple", "banana", "cherry"] }
```

Rendered result

Using the example context the rendered output will be:

```text
# Items

- apple
- banana
- cherry
```

Notes

- The loop variable (`item` above) is whatever identifier you declare in the `for` statement.
- `items` must be an array in the provided context.
- Nested loops are supported by composing loop blocks.

Tip: Prepare and validate list data in the context rather than trying to transform large datasets inside the template.
