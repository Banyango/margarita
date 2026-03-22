# Getting Started

## Install with uvx (recommended)

If you have [uv](https://docs.astral.sh/uv/) installed, you can run MARGARITA without a permanent install:

```sh
uvx margarita render greeting.mg
```

To install it as a persistent tool:

```sh
uv tool install margarita
```

<br/>
## Walkthrough

### Create a template file `greeting.mg`:

```margarita
<<
Hello, ${name}!
>>
```

### Provide context

Add JSON either inline or in a file `greeting.json`:

```json
{"name": "Batman"}
```

### Render

Render the template with the CLI:

```sh
margarita render greeting.mg -f greeting.json
```

### Rendered result

Using the template and context above the output will be:

```text
Hello, Batman!
```

<br/>
### Alternate options

- Pass context as a JSON string: `-c '{"name": "Bob"}'`
- Render a directory of `.mg` files: `margarita render templates/ -o output/`
- Inspect template metadata before rendering: `margarita render template.mg --show-metadata`

>
> Tip: When rendering a single file, MARGARITA will auto-detect a same-name `.json` file (e.g. `greeting.json`) if no context is supplied.
>
