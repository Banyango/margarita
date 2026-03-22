# Template Packages

Margarita supports using python virtual environments to add additional includes in your templates.

---

## How it works

When you render a template, MARGARITA finds the nearest `.venv/` and finds installed packages that expose a `templates/` directory.

```shell
my-project/
  .venv/              ← virtual environment
    ...
      example-package/
        templates/
          tone.mg
          style.mg
  src/
    article.mg
```

When rendering `article.mg`, MARGARITA detects the `.venv/`, finds installed packages with templates, and allows you to include them:

```
// filename: src/article.mg
[[ example-package/tone ]]
```

---

## Creating a template package

A template package is a normal Python package. The only convention is that `.mg` files live under a `templates/` subdirectory inside the top-level package directory.

### Directory layout

```
writing-templates/
  pyproject.toml
  writing_templates/
    __init__.py
    templates/
      tone.mg
      style.mg
      techniques/
        show_dont_tell.mg
```

### `pyproject.toml`

```toml
[project]
name = "writing-templates"
version = "0.1.0"

[tool.setuptools.package-data]
"writing_templates" = ["templates/*.mg", "templates/**/*.mg"]
```

The `package-data` entry ensures `.mg` files are included when the package is built and installed.

---

## Installing a template package

From your project directory:

```sh
uv add writing-templates
```

Or from a local path during development:

```sh
uv add --editable ../writing-templates
```

MARGARITA automatically picks up any package installed in the project's `.venv` — no extra configuration needed.

---

## Using package includes in templates

Reference an installed package's templates with the `[[ package-name/path ]]` syntax, where `path` is relative to that package's `templates/` directory (no `.mg` extension needed).

```margarita
// filename: src/article.mg
<<
# Article Draft
>>

[[ writing-templates/tone ]]

[[ writing-templates/techniques/show_dont_tell ]]
```

Subdirectory paths work the same way:

```margarita

[[ writing-templates/techniques/show_dont_tell ]]

```

## Multiple packages

You can install as many template packages as you like. Each is namespaced by its distribution name, so files with the same name in different packages never conflict:

```margarita
[[ writing-templates/tone ]]
[[ editing-templates/tone ]]
```

If two installed packages share the same distribution name, MARGARITA skips the duplicate and prints a warning to stderr.
