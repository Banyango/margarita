# Getting Started

# Installation

Run the following command to install MARGARITA via pip:

Linux:
```sh
curl -fsSL https://raw.githubusercontent.com/Banyango/margarita/main/install-linux.sh | bash -s -- --option
```

MacOS:
```sh
curl -fsSL https://raw.githubusercontent.com/Banyango/margarita/main/install-macos.sh | bash -s -- --option
```

Windows (PowerShell):
```powershell
iwr -useb https://raw.githubusercontent.com/Banyango/margarita/main/install-windows.ps1 | iex
```


A minimal walkthrough to render your first MARGARITA template.

1. Create a template file `greeting.mg`:

```margarita
<<
Hello, ${name}!
>>
```

2. Provide a context (JSON) either inline or in a file `greeting.json`:

```json
{"name": "Batman"}
```

3. Render the template with the CLI:

```sh
margarita render greeting.mg -f greeting.json
```

Rendered result

Using the template and context above the output will be:

```text
Hello, Batman!
```

Alternate options

- Pass context as a JSON string: `-c '{"name": "Bob"}'`
- Render a directory of `.mg` files: `margarita render templates/ -o output/`
- Inspect template metadata before rendering: `margarita render template.mg --show-metadata`

>
> Tip: When rendering a single file, MARGARITA will auto-detect a same-name `.json` file (e.g. `greeting.json`) if no context is supplied.
>
