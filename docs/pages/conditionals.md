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

Notes

- Conditions evaluate truthiness: missing, false, empty, or null values are treated as false.
- You can reference nested values with dotted paths, e.g. `user.active`.
- There is no support for complex expressions — stick to presence and simple boolean checks.

Tip: Use `margarita metadata` or a dry render to ensure required context keys are present before running in production.
