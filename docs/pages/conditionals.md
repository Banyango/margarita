# Conditionals

Use conditionals to render sections conditionally based on context values.

Syntax

```margarita
if subscribed:
    << Thanks for subscribing, ${name}! >>
else:
    <<< Please consider subscribing. >>
```

Rendered results

- When `subscribed` is true and `name` is `Dana`:

```text
Thanks for subscribing, Dana!
```

- When `subscribed` is false or missing:

```text
Please consider subscribing.
```

## elif

Use `elif` to add additional branches without nesting:

```margarita
if status == "premium":
    << Premium user >>
elif status == "standard":
    << Standard user >>
elif status == "trial":
    << Trial user >>
else:
    << Unknown status >>
```

Any number of `elif` branches can follow an `if`. An optional `else` branch at the end catches all remaining cases.

Notes

- Conditions evaluate truthiness: missing, false, empty, or null values are treated as false.
- You can reference nested values with dotted paths, e.g. `user.active`.
- `elif` is syntactic sugar for a nested `if` in the false branch; no additional AST nodes are needed.

Tip: Use `margarita metadata` or a dry render to ensure required context keys are present before running in production.
