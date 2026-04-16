"""
Pygments lexer for the Margarita / MGX templating and scripting language.

Covers both .mg template files and .mgx agent files:

    @state var = value              -- agent state variable
    @memory var / delete / clear    -- persistent memory
    @effect run / log / input       -- agent effects
    @effect func / tools            -- function/tool registration
    @effect context clear           -- context management
    from module import func         -- Python-style imports
    if / elif / else / for / in     -- control flow
    << ... >>                       -- output / prompt blocks
    ${var}                          -- variable interpolation
    [[ file params ]]               -- includes
    --- ... ---                     -- YAML front matter
    // ...                          -- single-line comments
"""

from typing import ClassVar

from pygments.lexer import RegexLexer, bygroups, using
from pygments.lexers.markup import MarkdownLexer
from pygments.token import (
    Comment,
    Generic,
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

# Subcommands that follow @effect
_EFFECT_CMDS = r"(run|log|input|func|tools|context)"
# Subcommands that follow @memory
_MEMORY_CMDS = r"(delete|clear|var)"


class MargaritaLexer(RegexLexer):
    """
    Lexer for Margarita / MGX templating and scripting language.

    Handles both .mg template syntax and .mgx agent syntax including
    @state, @memory, @effect decorator nodes.
    """

    name = "Margarita"
    aliases: ClassVar[list[str]] = ["margarita", "marg", "mg", "mgx", "margaritascript"]
    filenames: ClassVar[list[str]] = ["*.mg", "*.mgx", "*.margarita"]
    mimetypes: ClassVar[list[str]] = ["text/x-margarita"]

    tokens: ClassVar[dict] = {
        "root": [
            # YAML front matter
            (r"^---\s*$", Punctuation, "frontmatter"),
            # Single-line comments  (// ...)
            (r"//.*?$", Comment.Single),
            # ----- Agent decorator nodes -----
            # @state var = value
            (
                r"(@state)(\s+)([a-zA-Z_]\w*)(\s*)(=)(\s*)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Name.Variable,
                    Whitespace,
                    Operator,
                    Whitespace,
                ),
                "state-value",
            ),
            # @memory delete/clear/var <name>
            (
                r"(@memory)(\s+)" + _MEMORY_CMDS + r"(\s+)([a-zA-Z_]\w*)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    Name.Variable,
                ),
            ),
            # @memory clear  (no name)
            (
                r"(@memory)(\s+)(clear)\b",
                bygroups(Keyword.Declaration, Whitespace, Keyword),
            ),
            # @memory var_name  (bare — create memory variable)
            (
                r"(@memory)(\s+)([a-zA-Z_]\w*)",
                bygroups(Keyword.Declaration, Whitespace, Name.Variable),
            ),
            # @effect context clear
            (
                r"(@effect)(\s+)(context)(\s+)(clear)\b",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    Keyword,
                ),
            ),
            # @effect run
            (
                r"(@effect)(\s+)(run)\b",
                bygroups(Keyword.Declaration, Whitespace, Keyword),
            ),
            # @effect log "message with optional ${var}"
            (
                r'(@effect)(\s+)(log)(\s+)(")',
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    String.Double,
                ),
                "effect-string",
            ),
            # @effect input "question" => var
            (
                r'(@effect)(\s+)(input)(\s+)(")',
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    String.Double,
                ),
                "effect-string-arrow",
            ),
            # @effect func call(args) => result
            (
                r"(@effect)(\s+)(func)(\s+)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                ),
                "effect-func",
            ),
            # @effect tools func(args) => result
            (
                r"(@effect)(\s+)(tools)(\s+)",
                bygroups(
                    Keyword.Declaration,
                    Whitespace,
                    Keyword,
                    Whitespace,
                ),
                "effect-func",
            ),
            # Generic @effect fallback
            (
                r"(@effect)(\s+)" + _EFFECT_CMDS,
                bygroups(Keyword.Declaration, Whitespace, Keyword),
            ),
            # ----- Python-style imports -----
            (
                r"(from)(\s+)([a-zA-Z_][\w.]*)(\s+)(import)(\s+)([a-zA-Z_]\w*)",
                bygroups(
                    Keyword,
                    Whitespace,
                    Name.Namespace,
                    Whitespace,
                    Keyword,
                    Whitespace,
                    Name.Function,
                ),
            ),
            # ----- Control flow -----
            # else:  (no expression)
            (r"^(\s*)(else)(\s*)(:)", bygroups(Whitespace, Keyword, Whitespace, Punctuation)),
            # if / elif / for  <expression>:
            (
                r"^(\s*)(if|elif|for)(\s+)",
                bygroups(Whitespace, Keyword, Whitespace),
                "control-expr",
            ),
            # ----- Include statements  [[ file params ]] -----
            (r"\[\[\s*", Punctuation, "include"),
            # ----- Output / prompt blocks  << ... >> -----
            (r"<<<", String.Delimiter, "output-block"),
            (r"<<", String.Delimiter, "output-block"),
            # ----- Variable interpolation  ${...} -----
            (r"\$\{", Name.Variable, "variable"),
            # Plain text / whitespace
            (r"[^\n]", Text),
            (r"\n", Whitespace),
        ],
        # ---- YAML front matter ----
        "frontmatter": [
            (r"^---\s*$", Punctuation, "#pop"),
            (
                r"^(\s*)([a-zA-Z_][\w]*?)(\s*)(:)",
                bygroups(Whitespace, Name.Attribute, Whitespace, Punctuation),
            ),
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            (r"\d+\.?\d*", Number),
            (r".", Text),
            (r"\n", Whitespace),
        ],
        # ---- State value: everything after  @state var =  until EOL ----
        "state-value": [
            (r"//.*?$", Comment.Single, "#pop"),
            (r'"[^"]*"', String.Double, "#pop"),
            (r"'[^']*'", String.Single, "#pop"),
            (r"(\[)([^\]]*?)(\])", bygroups(Punctuation, Generic.Output, Punctuation), "#pop"),
            (r"(\{)([^\}]*?)(\})", bygroups(Punctuation, Generic.Output, Punctuation), "#pop"),
            (r"-?\d+\.?\d*", Number, "#pop"),
            (r"\b(True|False|None)\b", Keyword.Constant, "#pop"),
            (r"[a-zA-Z_]\w*", Name.Variable, "#pop"),
            (r"[^\n]+", Text, "#pop"),
            (r"\n", Whitespace, "#pop"),
        ],
        # ---- String for @effect log "..." ----
        "effect-string": [
            (r"\$\{[a-zA-Z_][\w.]*\}", Name.Variable),
            (r'"', String.Double, "#pop"),
            (r'[^"$]+', String.Double),
            (r"\$", String.Double),
        ],
        # ---- String + => var for @effect input "..." => var ----
        "effect-string-arrow": [
            (r"\$\{[a-zA-Z_][\w.]*\}", Name.Variable),
            (
                r'"(\s*)(=>)(\s*)([a-zA-Z_]\w*)',
                bygroups(String.Double, Operator, Whitespace, Name.Variable),
                "#pop",
            ),
            (r'"', String.Double, "#pop"),
            (r'[^"$]+', String.Double),
            (r"\$", String.Double),
        ],
        # ---- @effect func/tools  call(args) => result ----
        "effect-func": [
            (r"[a-zA-Z_]\w*", Name.Function, "effect-func-args"),
            (r"[ \t]+", Whitespace),
            (r"\n", Whitespace, "#pop"),
        ],
        "effect-func-args": [
            (r"\(", Punctuation),
            (r"\)", Punctuation),
            (
                r"([ \t]*)(=>)([ \t]*)([a-zA-Z_]\w*)",
                bygroups(Whitespace, Operator, Whitespace, Name.Variable),
                "#pop",
            ),
            (
                r"([a-zA-Z_]\w*)(\s*:\s*)([a-zA-Z_]\w*)",
                bygroups(Name.Variable, Punctuation, Name.Builtin),
            ),
            (r"[a-zA-Z_]\w*", Name.Variable),
            (r",", Punctuation),
            (r"[ \t]+", Whitespace),
            (r"[^\n]", Text),
            (r"\n", Whitespace, "#pop"),
        ],
        # ---- Control expression (if/elif/for)  ...  : ----
        "control-expr": [
            (r"\b(in|and|or|not|True|False|None)\b", Keyword.Operator),
            (
                r"\b(range)(\s*)(\()",
                bygroups(Name.Builtin, Whitespace, Punctuation),
                "func-args",
            ),
            (r"==|!=|<=|>=|<|>", Operator),
            (r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*", Name.Variable),
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            (r"\d+", Number.Integer),
            (r",", Punctuation),
            (r":", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
        "func-args": [
            (r"\d+", Number.Integer),
            (r",", Punctuation),
            (r"\)", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
        # ---- Include statements  [[ file params ]] ----
        "include": [
            (r"[a-zA-Z_][\w]*(?:[./][a-zA-Z_][\w]*)*", Name.Namespace),
            (r"[a-zA-Z_][\w]*\s*=", Name.Attribute),
            (r'"[^"]*"', String.Double),
            (r"'[^']*'", String.Single),
            (r"\b(True|False)\b", Keyword.Constant),
            (r"\s*\]\]", Punctuation, "#pop"),
            (r"\s+", Whitespace),
        ],
        # ---- Output block  << ... >> ----
        "output-block": [
            (r"\$\{[a-zA-Z_][\w.]*\}", Name.Variable),
            (r"\$\{", Name.Variable, "variable"),
            (r">>>", String.Delimiter, "#pop"),
            (r">>", String.Delimiter, "#pop"),
            (r"[^>$\n]+", using(MarkdownLexer)),
            (r"\n", Whitespace),
            (r".", using(MarkdownLexer)),
        ],
        # ---- Variable  ${...} ----
        "variable": [
            (r"[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*", Name.Variable),
            (r"\}", Name.Variable, "#pop"),
            (r"\s+", Whitespace),
        ],
    }
