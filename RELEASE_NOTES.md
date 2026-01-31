# Release Notes - Margarita v0.3.0

**Release Date:** January 31, 2026

## 🎉 Overview

Releasing install scripts and some updated documentation.

# Release Notes - Margarita v0.2.0

**Release Date:** January 25, 2026

## 🎉 Overview

Complete overhaul of the syntax.

- Markdown is now contained within << and >> blocks.
- Conditions follow indentation based scoping.
- Loops follow indentation based scoping.
- Includes now can take parameters. ala React. `[[ ComponentName prop1="value1" prop2="value2" ]]`
- Variables are now defined with ${varname} syntax.
- Metadata blocks are now defined with --- yaml --- syntax.


# Release Notes - Margarita v0.1.0

**Release Date:** January 22, 2026

## 🎉 Overview

This is the initial release of **Margarita**, a lightweight markup language and Python library for writing, composing, and rendering structured LLM prompts. Margarita is designed for prompt engineering workflows where clarity, versioning, and correctness matter.

## ✨ Features

### Core Functionality
- **Parser** - Parse `.mg` template files with support for variables, conditionals, loops, and includes
- **Renderer** - Render templates with context data to produce final prompts
- **Composer** - Compose and nest multiple template files together
- **CLI Tool** - Command-line interface for rendering templates from the terminal

### Key Capabilities
- ✨ **Framework Agnostic** - Works with any LLM or API
- 🚀 **Composable** - Prompts can be split, reused, and nested
- 🎯 **Static-First** - Templates are validated before execution
- 📦 **Metadata Support** - Version and provide metadata alongside your prompts
- 🔧 **Type Hints** - Full typing support with `py.typed`

### Template Features
- Variable substitution with `{{variable}}` syntax
- Conditional rendering
- Loop support
- File inclusion and composition
- Context management

## 📦 Installation

```bash
pip install margarita==0.1.0
```

## 🚀 Quick Start

Create a template file `hello.mg`:
```markdown
Hello, {{name}}!
Welcome to Margarita templating.
```

Create a context file `context.json`:
```json
{
    "name": "World"
}
```

Render the template:
```bash
margarita render hello.mg
```

## 🔧 Requirements

- Python >= 3.10
- Dependencies:
  - `click >= 8.0.0`
  - `loguru >= 0.7.3`

## 📚 Documentation

Full documentation is available with examples for:
- Getting Started
- Basic templating
- Conditionals
- Loops
- Include files
- Contexts
- Metadata
- Using with AI agents

## 🛠️ Development

### Optional Dependencies

**Development tools:**
```bash
pip install margarita[dev]
```
Includes: pytest, pytest-cov, pytest-asyncio, ruff, mypy, pre-commit

**Documentation tools:**
```bash
pip install margarita[docs]
```
Includes: mkdocs, mkdocs-material, mkdocstrings

## 📄 License

MIT License - see LICENSE file for details

## 👥 Author

Kyle Reczek (kyle@banyango.com)

## 🔗 Links

- **PyPI:** https://pypi.org/project/margarita/
- **GitHub:** https://github.com/Banyango/margarita
- **Documentation:** https://banyango.github.io/margarita/

## 📝 Known Limitations

- CLI tool requires local installation from source for full functionality (PyPI package in progress)

## 🙏 Acknowledgments

Thank you to all early adopters and contributors who helped shape this initial release!

---

**Full Changelog**: https://github.com/Banyango/margarita/blob/main/CHANGELOG.md

