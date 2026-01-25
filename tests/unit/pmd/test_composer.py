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
        self._create_template("simple.mg", "<<Hello, ${name}!>>")

        metadata, nodes = self.composer.load_template("simple.mg")

        assert metadata == {}
        assert len(nodes) == 1  # TextNode with interpolation
        assert "simple.mg" in self.composer._template_cache

    def test_load_template_should_load_when_has_metadata(self):
        template_content = """---
name: test-template
version: 1.0.0
---

<<Hello, ${name}!>>"""
        self._create_template("metadata.mg", template_content)

        metadata, nodes = self.composer.load_template("metadata.mg")

        assert metadata == {"name": "test-template", "version": "1.0.0"}
        assert len(nodes) > 0

    def test_load_template_should_use_cache_when_template_already_loaded(self):
        self._create_template("cached.mg", "<<Content>>")

        result1 = self.composer.load_template("cached.mg")

        self._create_template("cached.mg", "<<Modified content>>")

        result2 = self.composer.load_template("cached.mg")

        assert result1 is result2  # Same object from cache
        assert "cached.mg" in self.composer._template_cache

    def test_load_template_should_load_template_when_in_subdirectory(self):
        self._create_template("snippets/header.mg", "<<# Header>>")

        metadata, nodes = self.composer.load_template("snippets/header.mg")

        assert len(nodes) > 0
        assert "snippets/header.mg" in self.composer._template_cache

    def test_render_should_render_template_when_template_is_simple(self):
        self._create_template("greeting.mg", "<<Hello, ${name}!>>")

        result = self.composer.render("greeting.mg", {"name": "Alice"})

        assert result == "Hello, Alice!\n"

    def test_render_should_render_conditionals_when_template_has_if_statements(self):
        template_content = """if show_greeting:
    <<Hello, ${name}!>>"""
        self._create_template("conditional.mg", template_content)

        # Test with condition true
        result1 = self.composer.render("conditional.mg", {"show_greeting": True, "name": "Bob"})
        assert "Hello, Bob!" in result1

        # Test with condition false
        result2 = self.composer.render("conditional.mg", {"show_greeting": False, "name": "Bob"})
        assert "Hello, Bob!" not in result2

    def test_render_should_render_loops_when_template_has_for_statements(self):
        template_content = """<<Items:>>
for item in items:
    <<- ${item}>>"""
        self._create_template("loop.mg", template_content)

        result = self.composer.render("loop.mg", {"items": ["apple", "banana", "cherry"]})

        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result

    def test_render_should_render_includes_when_template_has_include_statements(self):
        self._create_template("header_test.mg", "<<# ${title}>>")
        self._create_template(
            "main.mg",
            """[[ header_test ]]

<<Content here.>>""",
        )

        result = self.composer.render("main.mg", {"title": "My Document"})

        assert "# My Document" in result
        assert "Content here." in result

    def test_render_should_render_nested_includes_when_template_has_nested_includes(self):
        self._create_template("snippets/role.mg", "<<You are a ${role}.>>")
        self._create_template("snippets/header1.mg", "[[ snippets/role.mg ]]")
        self._create_template("main.mg", "[[ snippets/header1 ]]\n\n<<Task: ${task}>>")

        result = self.composer.render("main.mg", {"role": "assistant", "task": "Help the user"})

        assert "You are a assistant." in result
        assert "Task: Help the user" in result

    def test_render_should_render_template_when_context_is_empty(self):
        self._create_template("empty.mg", "<<No variables here.>>")

        result = self.composer.render("empty.mg", {})

        assert result == "No variables here.\n"

    def test_render_should_render_empty_string_when_variable_is_missing(self):
        self._create_template("missing.mg", "<<Hello, ${name}!>>")

        result = self.composer.render("missing.mg", {})

        # Missing variables should render as empty string
        assert result == "Hello, !\n"

    def test_compose_prompt_should_compose_snippets_when_snippets_are_simple(self):
        self._create_template("intro.mg", "<<Introduction: ${topic}>>")
        self._create_template("body.mg", "<<Details about ${topic}>>")
        self._create_template("outro.mg", "<<Conclusion>>")

        result = self.composer.compose_prompt(
            snippets=["intro.mg", "body.mg", "outro.mg"], context={"topic": "testing"}
        )

        assert "Introduction: testing" in result
        assert "Details about testing" in result
        assert "Conclusion" in result
        # Default separator is "\n\n"
        assert "\n\n" in result

    def test_compose_prompt_should_use_separator_when_custom_separator_provided(self):
        self._create_template("part1.mg", "<<Part 1>>")
        self._create_template("part2.mg", "<<Part 2>>")
        self._create_template("part3.mg", "<<Part 3>>")

        result = self.composer.compose_prompt(
            snippets=["part1.mg", "part2.mg", "part3.mg"], context={}, separator=" | "
        )

        assert result == "Part 1\n | Part 2\n | Part 3\n"

    def test_compose_prompt_should_compose_when_single_snippet_provided(self):
        self._create_template("single.mg", "<<Only one: ${value}>>")

        result = self.composer.compose_prompt(snippets=["single.mg"], context={"value": "test"})

        assert result == "Only one: test\n"

    def test_compose_prompt_should_return_empty_string_when_snippets_list_is_empty(self):
        result = self.composer.compose_prompt(snippets=[], context={})

        assert result == ""

    def test_compose_prompt_should_compose_snippets_when_variables_provided(self):
        self._create_template("role.mg", "<<You are a ${role}.>>")
        self._create_template("task.mg", "<<Your task: ${task}>>")
        self._create_template("format.mg", "<<Output format: ${format}>>")

        result = self.composer.compose_prompt(
            snippets=["role.mg", "task.mg", "format.mg"],
            context={"role": "assistant", "task": "summarize", "format": "JSON"},
        )

        assert "You are a assistant." in result
        assert "Your task: summarize" in result
        assert "Output format: JSON" in result

    def test_compose_prompt_should_compose_snippets_when_in_subdirectories(self):
        self._create_template("system/role.mg", "<<Role: ${role}>>")
        self._create_template("tasks/main.mg", "<<Task: ${task}>>")
        self._create_template("output/format.mg", "<<Format: ${format}>>")

        result = self.composer.compose_prompt(
            snippets=["system/role.mg", "tasks/main.mg", "output/format.mg"],
            context={"role": "expert", "task": "analyze", "format": "markdown"},
        )

        assert "Role: expert" in result
        assert "Task: analyze" in result
        assert "Format: markdown" in result

    def test_load_template_should_raise_error_when_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.composer.load_template("nonexistent.mg")

    def test_render_should_raise_error_when_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.composer.render("missing.mg", {})

    def test_compose_prompt_should_raise_error_when_file_not_found(self):
        self._create_template("exists.mg", "Content")

        with pytest.raises(FileNotFoundError):
            self.composer.compose_prompt(snippets=["exists.mg", "missing.mg"], context={})

    def test_multiple_composers_should_have_independent_caches_when_created(self):
        self._create_template("test.mg", "<<Content>>")

        composer1 = Composer(self.template_dir)
        composer2 = Composer(self.template_dir)

        composer1.load_template("test.mg")

        assert "test.mg" in composer1._template_cache
        assert "test.mg" not in composer2._template_cache

    def test_render_should_render_template_when_using_dotted_variables(self):
        self._create_template("dotted.mg", "<<User: ${user.name}, ID: ${user.id}>>")

        result = self.composer.render("dotted.mg", {"user": {"name": "Alice", "id": 42}})

        assert "User: Alice" in result
        assert "ID: 42" in result

    def test_render_should_exclude_metadata_when_rendering_template(self):
        template_content = """---
@version: 1.0.0
---

<<Value: ${value}>>"""
        self._create_template("meta.mg", template_content)

        result = self.composer.render("meta.mg", {"value": "test"})

        assert "Value: test" in result
        assert "version" not in result

    def test_compose_prompt_should_compose_multi_level_structure_when_complex(self):
        # Create a multi-level prompt structure
        self._create_template("components/role.mg", "<<You are a ${role} assistant.>>")
        self._create_template("components/context.mg", "<<Context: ${context}>>")
        self._create_template("components/task.mg", "<<Task: ${task}>>")
        self._create_template(
            "components/constraints.mg",
            """<<Constraints:>>
for constraint in constraints:
    <<- ${constraint}>>""",
        )

        result = self.composer.compose_prompt(
            snippets=[
                "components/role.mg",
                "components/context.mg",
                "components/task.mg",
                "components/constraints.mg",
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
