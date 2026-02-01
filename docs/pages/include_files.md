# Include Files

Reuse template fragments using `[[ file ]]`. Includes are resolved relative to the including template's directory.

Example

```margarita
// filename: header.mg
<<This is the header content.>>
```

```margarita
// filename: page.mg
[[ header ]]
<<
# Page Title

Content goes here using the same context.
>>
```

Rendered result

When rendering `page.mg`, the output will include the header content followed by the page body:

```text
This is the header content.

# Page Title

Content goes here using the same context.
```

Behavior

- Included files have access to the same rendering context as the parent template.
- Paths are resolved relative to the parent template's directory (the CLI and renderer set `base_path`).
- Avoid circular includes; they can cause infinite loops or errors.

## Composable Templates

You can pass variables to included templates by defining them in the parent context. For example:

```margarita
// filename: greeting.mg
<<Hello, ${name}!>>
```

```margarita
// filename: main.mg
[[ greeting name="Alice" ]]
```

Rendered result

When rendering `main.mg`, the output will be:

```text
Hello, Alice!
```

## More Examples

See the [Using Includes](includes.md) page for comprehensive examples and patterns.

Tip: Use includes for headers, footers, and small shared components to keep templates DRY and maintainable.
