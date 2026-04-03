"""
MkDocs hooks to register custom Pygments lexers.
"""

import sys
from pathlib import Path


def _register_margarita_lexer():
    # Ensure docs/ is on the import path so local lexers resolve reliably.
    docs_dir = str(Path(__file__).resolve().parent)
    if docs_dir not in sys.path:
        sys.path.insert(0, docs_dir)

    # Import the lexer from the local docs package first, then fall back to the package
    try:
        from lexers.margarita_lexer import MargaritaLexer
    except ImportError:
        from margarita.pygments_lexer import MargaritaLexer

    from pygments.lexers import _mapping

    # Register the Margarita lexer in Pygments' internal mapping
    if "MargaritaLexer" not in _mapping.LEXERS:
        module_path = MargaritaLexer.__module__
        _mapping.LEXERS["MargaritaLexer"] = (
            module_path,
            "Margarita",
            ("margarita", "marg", "mg"),
            ("*.mg", "*.margarita"),
            ("text/x-margarita",),
        )
        print("✓ Registered MARGARITA syntax highlighter")


def on_startup(**_kwargs):
    """
    Register custom Pygments lexers when MkDocs starts.

    This hook is called once at the start of mkdocs serve or build.
    """
    try:
        _register_margarita_lexer()
    except ImportError as e:
        print(f"Note: MARGARITA lexer not available: {e}")
        print("      Install with: pip install -e .")
    except Exception as e:
        print(f"Warning: Could not register MARGARITA lexer: {e}")


def on_config(config, **_kwargs):
    """Register lexers before MkDocs config is finalized."""
    try:
        _register_margarita_lexer()
    except ImportError as e:
        print(f"Note: MARGARITA lexer not available: {e}")
        print("      Install with: pip install -e .")
    except Exception as e:
        print(f"Warning: Could not register MARGARITA lexer: {e}")
    return config
