"""
Margarita vs Jinja2 — Side-by-Side Comparison
==============================================

This example builds the same customer support prompt two ways:
once with Jinja2, and once with Margarita. Both produce identical output.

The goal: show how Margarita removes Jinja2's template noise while keeping
all the power of conditionals, loops, and composition.

Key contrasts:

1. Nested for loops:

   Jinja2:    Stacked {% endfor %} tags — you have to count them to know
              what closes what. The text content gets buried in the noise.

              {% for category in tool_categories %}
              {{ category.name }}:
              {% for tool in category.tools %}
                - {{ tool }}
              {% endfor %}
              {% endfor %}

   Margarita: Improved readability.

              for category in tool_categories:
                  <<${category.name}:>>
                  for tool in category.tools:
                      <<  - ${tool}>>

2. Passing variables to includes:

   Jinja2:    {% include %} cannot pass variables — the included template
              just inherits the outer context. To scope variables, you must
              switch to macros: define {% macro %} in one file, then
              {% from "x.j2" import y %} in the other. A completely
              different mental model just to parameterize a snippet.

              {% from "system_macro.j2" import render as render_system %}
              {{ render_system(company_name, "formal" if tier == "premium" else "friendly") }}

   Margarita: Pass key=value pairs directly in the include syntax. They
              are scoped to that include and don't leak to the outer context.

              if tier == "premium":
                  [[ system tone="formal" ]]
              else:
                  [[ system tone="friendly" ]]
"""

from pathlib import Path

# ─── JINJA2 VERSION ───────────────────────────────────────────────────────────
# pip install jinja2
#
# To use {% include %} in Jinja2, you must:
#   1. Write every template to disk as a .j2 file
#   2. Point a FileSystemLoader at that directory
#   3. Create an Environment to wire them together
#   4. Load templates by filename — you can no longer use Template(string)
#
# See templates/system.j2 and templates/support_prompt.j2

from jinja2 import Environment, FileSystemLoader


def build_prompt_jinja(context: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("support_prompt.j2")
    return template.render(**context)


# ─── MARGARITA VERSION ────────────────────────────────────────────────────────

from margarita.composer import Composer


def build_prompt_margarita(context: dict) -> str:
    composer = Composer(Path(__file__).parent / "templates")
    return composer.render("support_prompt.mg", context)


# ─── RUN BOTH ─────────────────────────────────────────────────────────────────

context = {
    "company_name": "Acme Corp",
    "tier": "premium",
    "history": "User asked about billing on Monday.",
    "message": "Why was I charged twice this month?",
    "tool_categories": [
        {"name": "Account", "tools": ["lookup_invoice", "update_billing"]},
        {"name": "Resolution", "tools": ["issue_refund", "apply_credit"]},
        {"name": "Escalation", "tools": ["escalate_to_human", "create_ticket"]},
    ],
}

print("=" * 60)
print("JINJA2 OUTPUT")
print("=" * 60)
print(build_prompt_jinja(context))

print()
print("=" * 60)
print("MARGARITA OUTPUT")
print("=" * 60)
print(build_prompt_margarita(context))
