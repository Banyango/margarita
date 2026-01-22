from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from margarita.composer import Composer


class TestMargaritaComposer:
    def setup_method(self):
        self.temp_dir = TemporaryDirectory()
        self.template_dir = Path(self.temp_dir.name)
        self.composer = Composer(self.template_dir)

    def teardown_method(self):
        self.temp_dir.cleanup()

    def _create_template(self, filename: str, content: str):
        template_path = self.template_dir / filename
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(content)

    def test_init_should_initialize_composer_when_created(self):
        assert self.composer.template_dir == self.template_dir
        assert self.composer.parser is not None
        assert isinstance(self.composer._template_cache, dict)
        assert len(self.composer._template_cache) == 0

    def test_load_template_should_parse_template_when_template_valid(self):
        self._create_template("simple.marg", "Hello, {{name}}!")

        metadata, nodes = self.composer.load_template("simple.marg")

        assert metadata == {}
        assert len(nodes) == 3  # TextNode, VariableNode, TextNode
        assert "simple.marg" in self.composer._template_cache

    def test_load_template_should_load_when_has_metadata(self):
        template_content = """---
@name: test-template
@version: 1.0.0
---

Hello, {{name}}!"""
        self._create_template("metadata.marg", template_content)

        metadata, nodes = self.composer.load_template("metadata.marg")

        assert metadata == {"name": "test-template", "version": "1.0.0"}
        assert len(nodes) > 0

    def test_load_template_should_use_cache_when_template_already_loaded(self):
        self._create_template("cached.marg", "Content")

        result1 = self.composer.load_template("cached.marg")

        self._create_template("cached.marg", "Modified content")

        result2 = self.composer.load_template("cached.marg")

        assert result1 is result2  # Same object from cache
        assert "cached.marg" in self.composer._template_cache

    def test_load_template_should_load_template_when_in_subdirectory(self):
        self._create_template("snippets/header.marg", "# Header\n")

        metadata, nodes = self.composer.load_template("snippets/header.marg")

        assert len(nodes) > 0
        assert "snippets/header.marg" in self.composer._template_cache

    def test_render_should_render_template_when_template_is_simple(self):
        self._create_template("greeting.marg", "Hello, {{name}}!")

        result = self.composer.render("greeting.marg", {"name": "Alice"})

        assert result == "Hello, Alice!"

    def test_render_should_render_conditionals_when_template_has_if_statements(self):
        template_content = """{% if show_greeting %}
Hello, {{name}}!
{% endif %}"""
        self._create_template("conditional.marg", template_content)

        # Test with condition true
        result1 = self.composer.render("conditional.marg", {"show_greeting": True, "name": "Bob"})
        assert "Hello, Bob!" in result1

        # Test with condition false
        result2 = self.composer.render("conditional.marg", {"show_greeting": False, "name": "Bob"})
        assert "Hello, Bob!" not in result2

    def test_render_should_render_loops_when_template_has_for_statements(self):
        template_content = """Items:
{% for item in items %}
- {{item}}
{% endfor %}"""
        self._create_template("loop.marg", template_content)

        result = self.composer.render("loop.marg", {"items": ["apple", "banana", "cherry"]})

        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_render_should_render_includes_when_template_has_include_statements(self):
        self._create_template("header.marg", "# {{title}}\n")
        self._create_template(
            "main.marg",
            """{% include "header.marg" %}

Content here.""",
        )

        result = self.composer.render("main.marg", {"title": "My Document"})

        assert "# My Document" in result
        assert "Content here." in result

    def test_render_should_render_nested_includes_when_template_has_nested_includes(self):
        self._create_template("snippets/role.marg", "You are a {{role}}.")
        self._create_template("snippets/header.marg", '{% include "snippets/role.marg" %}\n')
        self._create_template("main.marg", '{% include "snippets/header.marg" %}\n\nTask: {{task}}')

        result = self.composer.render("main.marg", {"role": "assistant", "task": "Help the user"})

        assert "You are a assistant." in result
        assert "Task: Help the user" in result

    def test_render_should_render_template_when_context_is_empty(self):
        self._create_template("empty.marg", "No variables here.")

        result = self.composer.render("empty.marg", {})

        assert result == "No variables here."

    def test_render_should_render_empty_string_when_variable_is_missing(self):
        self._create_template("missing.marg", "Hello, {{name}}!")

        result = self.composer.render("missing.marg", {})

        # Missing variables should render as empty string
        assert result == "Hello, !"

    def test_compose_prompt_should_compose_snippets_when_snippets_are_simple(self):
        self._create_template("intro.marg", "Introduction: {{topic}}")
        self._create_template("body.marg", "Details about {{topic}}")
        self._create_template("outro.marg", "Conclusion")

        result = self.composer.compose_prompt(
            snippets=["intro.marg", "body.marg", "outro.marg"], context={"topic": "testing"}
        )

        assert "Introduction: testing" in result
        assert "Details about testing" in result
        assert "Conclusion" in result
        # Default separator is "\n\n"
        assert "\n\n" in result

    def test_compose_prompt_should_use_separator_when_custom_separator_provided(self):
        self._create_template("part1.marg", "Part 1")
        self._create_template("part2.marg", "Part 2")
        self._create_template("part3.marg", "Part 3")

        result = self.composer.compose_prompt(
            snippets=["part1.marg", "part2.marg", "part3.marg"], context={}, separator=" | "
        )

        assert result == "Part 1 | Part 2 | Part 3"

    def test_compose_prompt_should_compose_when_single_snippet_provided(self):
        self._create_template("single.marg", "Only one: {{value}}")

        result = self.composer.compose_prompt(snippets=["single.marg"], context={"value": "test"})

        assert result == "Only one: test"

    def test_compose_prompt_should_return_empty_string_when_snippets_list_is_empty(self):
        result = self.composer.compose_prompt(snippets=[], context={})

        assert result == ""

    def test_compose_prompt_should_compose_snippets_when_variables_provided(self):
        self._create_template("role.marg", "You are a {{role}}.")
        self._create_template("task.marg", "Your task: {{task}}")
        self._create_template("format.marg", "Output format: {{format}}")

        result = self.composer.compose_prompt(
            snippets=["role.marg", "task.marg", "format.marg"],
            context={"role": "assistant", "task": "summarize", "format": "JSON"},
        )

        assert "You are a assistant." in result
        assert "Your task: summarize" in result
        assert "Output format: JSON" in result

    def test_compose_prompt_should_compose_snippets_when_in_subdirectories(self):
        self._create_template("system/role.marg", "Role: {{role}}")
        self._create_template("tasks/main.marg", "Task: {{task}}")
        self._create_template("output/format.marg", "Format: {{format}}")

        result = self.composer.compose_prompt(
            snippets=["system/role.marg", "tasks/main.marg", "output/format.marg"],
            context={"role": "expert", "task": "analyze", "format": "markdown"},
        )

        assert "Role: expert" in result
        assert "Task: analyze" in result
        assert "Format: markdown" in result

    def test_load_template_should_raise_error_when_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.composer.load_template("nonexistent.marg")

    def test_render_should_raise_error_when_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.composer.render("missing.marg", {})

    def test_compose_prompt_should_raise_error_when_file_not_found(self):
        self._create_template("exists.marg", "Content")

        with pytest.raises(FileNotFoundError):
            self.composer.compose_prompt(snippets=["exists.marg", "missing.marg"], context={})

    def test_multiple_composers_should_have_independent_caches_when_created(self):
        self._create_template("test.marg", "Content")

        composer1 = Composer(self.template_dir)
        composer2 = Composer(self.template_dir)

        composer1.load_template("test.marg")

        assert "test.marg" in composer1._template_cache
        assert "test.marg" not in composer2._template_cache

    def test_render_should_render_template_when_using_dotted_variables(self):
        self._create_template("dotted.marg", "User: {{user.name}}, ID: {{user.id}}")

        result = self.composer.render("dotted.marg", {"user": {"name": "Alice", "id": 42}})

        assert "User: Alice" in result
        assert "ID: 42" in result

    def test_render_should_exclude_metadata_when_rendering_template(self):
        template_content = """---
@version: 1.0.0
---

Value: {{value}}"""
        self._create_template("meta.marg", template_content)

        result = self.composer.render("meta.marg", {"value": "test"})

        assert "Value: test" in result
        assert "version" not in result

    def test_compose_prompt_should_compose_multi_level_structure_when_complex(self):
        # Create a multi-level prompt structure
        self._create_template("components/role.marg", "You are a {{role}} assistant.")
        self._create_template("components/context.marg", "Context: {{context}}")
        self._create_template("components/task.marg", "Task: {{task}}")
        self._create_template(
            "components/constraints.marg",
            """Constraints:
{% for constraint in constraints %}
- {{constraint}}
{% endfor %}""",
        )

        result = self.composer.compose_prompt(
            snippets=[
                "components/role.marg",
                "components/context.marg",
                "components/task.marg",
                "components/constraints.marg",
            ],
            context={
                "role": "helpful",
                "context": "Customer support",
                "task": "Answer questions",
                "constraints": ["Be polite", "Be concise", "Be accurate"],
            },
            separator="\n\n",
        )

        assert "You are a helpful assistant." in result
        assert "Context: Customer support" in result
        assert "Task: Answer questions" in result
        assert "- Be polite" in result
        assert "- Be concise" in result
        assert "- Be accurate" in result
