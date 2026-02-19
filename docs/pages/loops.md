# Loops

Render lists and repeat sections using `for` loops.

Syntax

```margarita
<< # Items >>
for item in items:
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

## Range Loops

Use the `range()` function to iterate a fixed number of times without passing a list in context.

```margarita
for i in range(3):
    << Step ${i} >>
```

Rendered result:

```text
Step 0
Step 1
Step 2
```

- `range(stop)` — iterate from 0 to stop (exclusive)
- `range(start, stop)` — iterate from start to stop (exclusive)
- `range(start, stop, step)` — iterate with a custom step

Example using `range(1, 4)`:

```margarita
for i in range(1, 4):
    << Item ${i} >>
```

Rendered result:

```text
Item 1
Item 2
Item 3
```

Example using `range(0, 10, 2)`:

```margarita
for i in range(0, 10, 2):
    << Even ${i} >>
```

Rendered result:

```text
Even 0
Even 2
Even 4
Even 6
Even 8
```
