"""
Pygments lexer for MARGARITA templating language.
"""

from pygments.lexer import RegexLexer, bygroups, using
from pygments.lexers.markup import MarkdownLexer
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)

__all__ = ["MargaritaLexer"]


class MargaritaLexer(RegexLexer):
    """
    Lexer for MARGARITA templating language.

    MARGARITA syntax includes:
    - Variables: ${var_name}
    - Output blocks: << content >>
    - Conditionals: if/elif/else
    - Loops: for item in items
    - Includes: [[ file ]]
    - Comments: // comment
    - Metadata: --- YAML front matter ---
    """

    name = "Margarita"
    aliases = ["margarita", "marg", "mg"]
    filenames = ["*.mg", "*.margarita"]
    mimetypes = ["text/x-margarita"]

    tokens = {
        "root": [
            # YAML front matter
            (r"^---\s*$", Punctuation, "frontmatter"),

            # Comments
            (r"//.*?$", Comment.Single),

            # Else blocks
            (r"^(\s*)(else)(\s*)(:)", bygroups(Whitespace, Keyword, Whitespace, Punctuation)),

            # Control structures
            (r"^(\s*)(if|elif|else|for)(\s+)", bygroups(Whitespace, Keyword, Whitespace), "control"),

            # Include statements
            (r"\[\[\s*", Punctuation, "include"),

            # Output blocks (double chevrons)
            (r"<<", String.Delimiter, "output-block"),

            # Variables
            (r"\$\{", Name.Variable, "variable"),
            (r"\{\{", Name.Variable, "variable"),

            # Plain text
            (r".", Text),
            (r"\n", Whitespace),
        ],

        "frontmatter": [
            # End of front matter
            (r"^---\s*$", Punctuation, "#pop"),

            # YAML keys
            (r"^(\s*)([a-zA-Z_][\w]*?)(\s*)(:)", bygroups(Whitespace, Name.Attribute, Whitespace, Punctuation)),

            # Strings
            (r"\"[^\"]*\"", String.Double),
            (r"'[^']*'", String.Single),

            # Numbers
            (r"\d+\.?\d*", Number),

            # Everything else
            (r".", Text),
            (r"\n", Whitespace),
        ],

        "control": [
            # Keywords in control statements
            (r"\b(in|and|or|not)\b", Keyword.Operator),

            # Function calls
            (r"\b(range)(\s*)(\()", bygroups(Name.Builtin, Whitespace, Punctuation), "function-args"),

            # Operators
            (r"==|!=|<=|>=|<|>", Operator),

            # Variables/identifiers
            (r"[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)*", Name.Variable),

            # Strings
            (r"\"[^\"]*\"", String.Double),
            (r"'[^']*'", String.Single),

            # Numbers
            (r"\d+", Number.Integer),

            # Colon ends control statement
            (r":", Punctuation, "#pop"),

            # Whitespace
            (r"\s+", Whitespace),
        ],

        "function-args": [
            # Numbers
            (r"\d+", Number.Integer),

            # Comma
            (r",", Punctuation),

            # Closing paren
            (r"\)", Punctuation, "#pop"),

            # Whitespace
            (r"\s+", Whitespace),
        ],

        "include": [
            # Filename
            (r"[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)*", Name.Namespace),

            # Closing brackets
            (r"\s*\]\]", Punctuation, "#pop"),

            # Whitespace
            (r"\s+", Whitespace),
        ],

        "output-block": [
            # Variables inside output blocks
            (r"(\$\{)([a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)*)(\})", bygroups(Name.Variable, Name.Variable, Name.Variable)),
            (r"\$\{", Name.Variable, "variable"),
            (r"\{\{", Name.Variable, "variable"),

            # Closing triple chevrons
            (r">>>", String.Delimiter, "#pop"),

            # Closing double chevrons
            (r">>", String.Delimiter, "#pop"),

            # Content
            (r"[^>$\{]+", using(MarkdownLexer)),
            (r".", using(MarkdownLexer)),
        ],

        "variable": [
            # Variable name with dot notation
            (r"[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)*", Name.Variable),

            # Closing for ${...}
            (r"\}", Name.Variable, "#pop"),

            # Closing for {{...}}
            (r"\}\}", Name.Variable, "#pop"),

            # Whitespace
            (r"\s+", Whitespace),
        ],
    }
