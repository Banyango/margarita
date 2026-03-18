# Template Packages

MARGARITA integrates with your .venv [uv](https://docs.astral.sh/uv/) to let you share and reuse `.mg` templates as ordinary Python packages. Install a template package once with `uv add` and reference its templates from any `.mg` file in your project.

---

## How it works

When you render a template, MARGARITA walks up the directory tree from the template file, finds the nearest `.venv/`, and scans its `site-packages` for installed packages that expose a `templates/` directory. Each package is registered under its distribution name (e.g. `writing-templates`), and you reference its templates with the `[[ package-name/file ]]` include syntax.

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

---

## Rendering a template directory

When your project has a `src/` directory of templates alongside a `.venv/`, render them all at once:

```
my-project/
  .venv/              ← uv-managed virtual environment
  src/
    article.mg
    article.json      ← auto-detected context
    brief.mg
    brief.json
```

Render a single file:

```sh
margarita render src/article.mg
# Output written to: src/article.md
```

Render the whole directory:

```sh
margarita render src/ -o output/
# Output written to: output/article.md
# Output written to: output/brief.md
```

MARGARITA walks up from `src/` to find `.venv/` and resolves all `[[ writing-templates/... ]]` includes automatically.

---

## Local files take priority

A local `.mg` file always shadows a package template with the same path. This lets you override individual templates without forking the package:

```
src/
  writing-templates/
    tone.mg       ← this takes priority over the installed package's tone.mg
  article.mg
```

```margarita
// filename: src/article.mg
[[ writing-templates/tone ]]   ← resolves to src/writing-templates/tone.mg
```

---

## Multiple packages

You can install as many template packages as you like. Each is namespaced by its distribution name, so files with the same name in different packages never conflict:

```margarita
[[ writing-templates/tone ]]
[[ editing-templates/tone ]]
```

If two installed packages share the same distribution name, MARGARITA skips the duplicate and prints a warning to stderr.
