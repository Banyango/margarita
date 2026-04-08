"""Integration tests that run .mg files through the parser and renderer.

This module tests the complete pipeline: parsing .mg template files,
render them with test data, and verifying the output matches expected results.
"""

import pathlib

import pytest

from margarita.parser import Parser
from margarita.renderer import Renderer


class TestMargaritaIntegration:
    """Integration tests for parsing and render .mg templates."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return Parser()

    @pytest.fixture
    def files_dir(self):
        """Get the files directory path."""
        return pathlib.Path(__file__).parent / "files"

    def test_simple_template(self, parser, files_dir):
        """Test simple.mg with basic variable substitution."""
        template_file = files_dir / "simple.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with context
        renderer = Renderer(context={"name": "Alice"})
        result = renderer.render(nodes)

        # Expected output
        expected = "Hello, Alice!\nWelcome to Margarita templating.\n\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_metadata_template(self, parser, files_dir):
        """Test metadata.mg with metadata and variable substitution."""
        template_file = files_dir / "metadata.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Verify metadata
        assert metadata["task"] == "summarization"
        assert metadata["owner"] == "search-team"
        assert metadata["version"] == "2.0"

        # Render with context
        renderer = Renderer(context={"document": "This is a sample document to summarize."})
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "\n"
            "# Instruction\n"
            "You are a helpful assistant specialized in summarization.\n\n"
            "# Input\n"
            "This is a sample document to summarize.\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_template_authenticated(self, parser, files_dir):
        """Test conditional.mg with authenticated user (true branch)."""
        template_file = files_dir / "conditional.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with authenticated context
        renderer = Renderer(
            context={"is_authenticated": True, "username": "Bob", "status": "Premium"}
        )
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "# Greeting\n"
            "Welcome back, Bob!\n\n"
            "Your account status: Premium\n"
            "# Footer\n"
            "Thank you for using our service.\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_template_unauthenticated(self, parser, files_dir):
        """Test conditional.mg with unauthenticated user (false branch)."""
        template_file = files_dir / "conditional.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with unauthenticated context
        renderer = Renderer(context={"is_authenticated": False})
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "# Greeting\nPlease sign in to continue.\n# Footer\nThank you for using our service.\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_loop_template(self, parser, files_dir):
        """Test loop.mg with for loop iteration."""
        template_file = files_dir / "loop.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with items
        renderer = Renderer(context={"items": ["Apple", "Banana", "Cherry"]})
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "\n"
            "# Items List\n\n"
            "- Item: Apple\n"
            "- Item: Banana\n"
            "- Item: Cherry\n"
            "\n# Summary\n"
            "Total items listed above.\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_loop_template_empty(self, parser, files_dir):
        """Test loop.mg with empty items list."""
        template_file = files_dir / "loop.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with empty items
        renderer = Renderer(context={"items": []})
        result = renderer.render(nodes)

        # Expected output (loop body should not appear)
        expected = "\n# Items List\n\n\n# Summary\nTotal items listed above.\n\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_complex_template_with_context(self, parser, files_dir):
        """Test complex.mg with nested if/for statements."""
        template_file = files_dir / "complex.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Verify metadata
        assert metadata["task"] == "complex-template"
        assert metadata["owner"] == "ai-team"

        # Render with context (has_context=True, format_json=False)
        renderer = Renderer(
            context={
                "task_type": "question answering",
                "has_context": True,
                "documents": [
                    {"title": "Doc1", "content": "Available"},
                    {"title": "Doc2", "content": "Available"},
                ],
                "query": "What is the capital of France?",
                "format_json": False,
            }
        )
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "# System Prompt\n"
            "You are an AI assistant helping with question answering.\n"
            "\n"
            "# Instructions\n"
            "Use the following context to answer:\n"
            "    - Title: Doc1\n"
            "    - Content: Available\n"
            "    - Title: Doc2\n"
            "    - Content: Available\n"
            "# User Query = What is the capital of France?\n"
            "\n"
            "# Output Format\n"
            "Provide your response in plain text.\n"
            "# Additional Notes\n"
            "- Be concise\n"
            "- Be accurate\n"
            "- Be helpful\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_complex_template_no_context(self, parser, files_dir):
        """Test complex.mg with has_context=False."""
        template_file = files_dir / "complex.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with context (has_context=False, format_json=True)
        renderer = Renderer(
            context={
                "task_type": "general inquiry",
                "has_context": False,
                "query": "Tell me about AI",
                "format_json": True,
            }
        )
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "# System Prompt\n"
            "You are an AI assistant helping with general inquiry.\n"
            "\n"
            "# Instructions\n"
            "Answer based on your general knowledge.\n"
            "# User Query = Tell me about AI\n"
            "\n"
            "# Output Format\n"
            "Provide your response in JSON format.\n"
            "# Additional Notes\n"
            "- Be concise\n"
            "- Be accurate\n"
            "- Be helpful\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_nested_template(self, parser, files_dir):
        """Test nested.mg with deeply nested structures."""
        template_file = files_dir / "nested.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with show_categories=True, show_items=True
        renderer = Renderer(
            context={
                "show_categories": True,
                "categories": ["Electronics", "Books"],
                "show_items": True,
                "items": ["Item1", "Item2"],
            }
        )
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "# Nested Conditionals and Loops\n"
            "\n"
            "This shows how to use the new syntax for building marg files.\n"
            "# Categories\n"
            "## Category: Electronics\n"
            "Items in this category:\n"
            "- Item1\n"
            "- Item2\n"
            "## Category: Books\n"
            "Items in this category:\n"
            "- Item1\n"
            "- Item2\n"
            "# End\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_nested_template_no_items(self, parser, files_dir):
        """Test nested.mg with show_items=False."""
        template_file = files_dir / "nested.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with show_categories=True, show_items=False
        renderer = Renderer(
            context={"show_categories": True, "categories": ["Electronics"], "show_items": False}
        )
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "# Nested Conditionals and Loops\n"
            "\n"
            "This shows how to use the new syntax for building marg files.\n"
            "# Categories\n"
            "## Category: Electronics\n"
            "No items to display.\n"
            "# End\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_include_template(self, parser, files_dir):
        template_file = files_dir / "include.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render
        renderer = Renderer(
            context={"content": "This is the main content section."}, base_path=files_dir
        )
        result = renderer.render(nodes)

        # Expected output (includes are rendered as placeholders)
        expected = (
            "This is the header content.\n"
            "Generated by header.prompt file.\n"
            "\n"
            "# Main Content\n"
            "This is the main content section.\n"
            "---\n"
            "This is the footer content.\n"
            "End of document.\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_unicode_template_happy(self, parser, files_dir):
        """Test unicode.mg with unicode characters and emojis (happy=True)."""
        template_file = files_dir / "unicode.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Verify metadata
        assert metadata["task"] == "multilingual"
        assert metadata["language"] == "mixed"

        # Render with happy=True
        renderer = Renderer(context={"name": "World", "happy": True})
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "\n"
            "# Multilingual Template\n\n"
            "Hello, World! 👋\n"
            "Bonjour, World! 🇫🇷\n"
            "こんにちは, World! 🇯🇵\n"
            "你好, World! 🇨🇳\n"
            "Привет, World! 🇷🇺\n\n"
            "# Emoji Support\n"
            "😊 You seem happy!\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_unicode_template_not_happy(self, parser, files_dir):
        """Test unicode.mg with unicode characters and emojis (happy=False)."""
        template_file = files_dir / "unicode.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with happy=False
        renderer = Renderer(context={"name": "世界", "happy": False})
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "\n"
            "# Multilingual Template\n\n"
            "Hello, 世界! 👋\n"
            "Bonjour, 世界! 🇫🇷\n"
            "こんにちは, 世界! 🇯🇵\n"
            "你好, 世界! 🇨🇳\n"
            "Привет, 世界! 🇷🇺\n\n"
            "# Emoji Support\n"
            "😐 Hope you're doing well!\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_includes_when_conditional_is_true(self, parser, files_dir):
        """Test conditional.mg with include directives in branches."""
        template_file = files_dir / "conditional_include.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with authenticated context
        renderer = Renderer(
            context={"include_extra": True, "name": "Batman"},
            base_path=files_dir,
        )
        result = renderer.render(nodes)

        # Expected output
        expected = "Test Conditional Include\nHello Batman!\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_includes_when_conditional_is_false(self, parser, files_dir):
        """Test conditional.mg with include directives in branches."""
        template_file = files_dir / "conditional_include.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with authenticated context
        renderer = Renderer(context={"extra_content": False, "name": "Batman"}, base_path=files_dir)
        result = renderer.render(nodes)

        # Expected output
        expected = "Test Conditional Include\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    @pytest.mark.parametrize(
        "is_authenticated,is_admin,expected",
        [
            (True, True, "Welcome back\nYou have administrative privileges.\n"),
            (True, False, "Welcome back\nYou are a regular user.\n"),
            (False, False, ""),
        ],
    )
    def test_nested_conditionals(self, parser, files_dir, is_authenticated, is_admin, expected):
        template_file = files_dir / "nested_conditional.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with context
        renderer = Renderer(context={"is_authenticated": is_authenticated, "is_admin": is_admin})
        result = renderer.render(nodes)

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_include_parameters(self, parser, files_dir):
        template_file = files_dir / "component_main.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render
        renderer = Renderer(context={}, base_path=files_dir)
        result = renderer.render(nodes)

        # Expected output (includes are rendered as placeholders)
        expected = (
            "Welcome to the system!\n"
            "User Admin Status: True\n"
            "Menu Visible: False\n"
            "Name: Alice\n"
            "Run Count: 1\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_nested_includes_subdir(self, parser, files_dir):
        template_file = files_dir / "nested_includes.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render
        renderer = Renderer(context={}, base_path=files_dir)
        result = renderer.render(nodes)

        # Expected output (includes are rendered as placeholders)
        expected = "\nLevel 1\nLevel 2\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_all_templates_parse_without_error(self, parser, files_dir):
        margarita_files = sorted(files_dir.glob("*.mg"))

        assert len(margarita_files) > 0, "No .mg files found"

        results = {}
        for template_file in margarita_files:
            with open(template_file, encoding="utf-8") as f:
                content = f.read()

            # Parse should not raise an exception
            metadata, nodes = parser.parse(content)
            results[template_file.name] = {
                "metadata_count": len(metadata),
                "node_count": len(nodes),
            }

        # Print summary
        print("\n" + "=" * 60)
        print("All templates parsed successfully:")
        print("=" * 60)
        for filename, info in results.items():
            print(
                f"{filename:20} -> {info['node_count']:2} nodes, {info['metadata_count']:2} metadata"
            )

        # Verify we tested all expected files
        assert "simple.mg" in results
        assert "metadata.mg" in results
        assert "conditional.mg" in results
        assert "loop.mg" in results
        assert "complex.mg" in results
        assert "nested.mg" in results
        assert "include.mg" in results
        assert "unicode.mg" in results

    def test_elif_template_renders_premium_when_status_is_premium(self, parser, files_dir):
        template_file = files_dir / "elif.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        metadata, nodes = parser.parse(content)
        renderer = Renderer(context={"status": "premium"})
        result = renderer.render(nodes)

        assert "Premium user" in result
        assert "Standard user" not in result
        assert "Trial user" not in result
        assert "Unknown status" not in result

    def test_elif_template_renders_standard_when_status_is_standard(self, parser, files_dir):
        template_file = files_dir / "elif.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        metadata, nodes = parser.parse(content)
        renderer = Renderer(context={"status": "standard"})
        result = renderer.render(nodes)

        assert "Standard user" in result
        assert "Premium user" not in result
        assert "Trial user" not in result
        assert "Unknown status" not in result

    def test_elif_template_renders_trial_when_status_is_trial(self, parser, files_dir):
        template_file = files_dir / "elif.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        metadata, nodes = parser.parse(content)
        renderer = Renderer(context={"status": "trial"})
        result = renderer.render(nodes)

        assert "Trial user" in result
        assert "Premium user" not in result
        assert "Standard user" not in result
        assert "Unknown status" not in result

    def test_elif_template_renders_else_when_status_is_unknown(self, parser, files_dir):
        template_file = files_dir / "elif.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        metadata, nodes = parser.parse(content)
        renderer = Renderer(context={"status": "other"})
        result = renderer.render(nodes)

        assert "Unknown status" in result
        assert "Premium user" not in result
        assert "Standard user" not in result
        assert "Trial user" not in result

    def test_conditional_should_parse_properly(self, parser, files_dir):
        """Test conditional_failure.mg a test case that failed in the wild."""
        template_file = files_dir / "conditional_failure.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with authenticated context
        renderer = Renderer(context={"tone": "formal", "text": "ABC"}, base_path=files_dir)
        result = renderer.render(nodes)

        # Expected output
        expected = 'You are a Tone Adjustment Expert. Your task is to rewrite the provided text in a specific tone suitable for the target audience, while maintaining the original meaning and intent. Below are templates for different tones:\n- If the input text is very short, add 1–2 supporting sentences for better rewrites.\n- If length is not specified, keep the rewritten text concise and a similar length to the original.\nTemplate: Rewrite the following text in a formal, professional tone for ; keep it concise and fact-focused and under  words.\nText: ABC\nExample: "To increase product registrations, we should enhance the website\'s call-to-action to improve conversion rates."\n'  # type: ignore  # noqa: RUF001

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_await_all_should_skip_effects_when_rendering(self, parser, files_dir):
        """Test await_all.mg with @await-all to ensure effects are skipped in output."""
        template_file = files_dir / "await_all.mg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render
        renderer = Renderer(context={})
        result = renderer.render(nodes)

        # Expected output (effects are ignored in render output)
        expected = "Before\nAfter\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"


class TestUvPackageIncludes:
    """Tests for resolving includes from a .venv site-packages tree."""

    @pytest.fixture
    def parser(self):
        return Parser()

    @pytest.fixture
    def uv_project(self, tmp_path):
        """Build a project with two uv packages, each with a tone.mg.

        project/
          src/
            main.mg
          .venv/lib/python3.12/site-packages/
            writing_templates/
              templates/
                tone.mg
                sub/
                  deep.mg
            writing_templates-0.1.0.dist-info/
              METADATA          (Name: writing)
              top_level.txt     (writing_templates)
            editing_templates/
              templates/
                tone.mg          (same filename — different package)
            editing_templates-0.1.0.dist-info/
              METADATA          (Name: editing)
              top_level.txt     (editing_templates)
        """
        site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"

        for pkg_name, module_name in (
            ("writing", "writing_templates"),
            ("editing", "editing_templates"),
        ):
            templates_dir = site_packages / module_name / "templates"
            templates_dir.mkdir(parents=True)
            (templates_dir / "tone.mg").write_text(f"<<\nFrom {pkg_name}\n>>\n")

            dist_info = site_packages / f"{module_name}-0.1.0.dist-info"
            dist_info.mkdir()
            (dist_info / "METADATA").write_text(f"Metadata-Version: 2.1\nName: {pkg_name}\n")
            (dist_info / "top_level.txt").write_text(f"{module_name}\n")

        sub_dir = site_packages / "writing_templates" / "templates" / "sub"
        sub_dir.mkdir()
        (sub_dir / "deep.mg").write_text("<<\nFrom deep\n>>\n")

        (tmp_path / "src").mkdir()
        return tmp_path

    def test_namespaced_include_resolves_to_correct_package(self, parser, uv_project):
        site_packages = uv_project / ".venv" / "lib" / "python3.12" / "site-packages"
        (uv_project / "src" / "main.mg").write_text("[[ writing/tone ]]\n[[ editing/tone ]]\n")
        _, nodes = parser.parse((uv_project / "src" / "main.mg").read_text())

        package_paths = {
            "writing": site_packages / "writing_templates" / "templates",
            "editing": site_packages / "editing_templates" / "templates",
        }
        renderer = Renderer(context={}, base_path=uv_project / "src", package_paths=package_paths)
        result = renderer.render(nodes)

        assert result == "From writing\nFrom editing\n"

    def test_namespaced_include_supports_subdirectory_paths(self, parser, uv_project):
        site_packages = uv_project / ".venv" / "lib" / "python3.12" / "site-packages"
        (uv_project / "src" / "main.mg").write_text("[[ writing/sub/deep ]]\n")
        _, nodes = parser.parse((uv_project / "src" / "main.mg").read_text())

        package_paths = {
            "writing": site_packages / "writing_templates" / "templates",
        }
        renderer = Renderer(context={}, base_path=uv_project / "src", package_paths=package_paths)
        result = renderer.render(nodes)

        assert result == "From deep\n"

    def test_base_path_takes_priority_over_package_paths(self, parser, uv_project):
        """A local file shadows a package file even when using the namespaced syntax."""
        site_packages = uv_project / ".venv" / "lib" / "python3.12" / "site-packages"
        (uv_project / "src" / "writing").mkdir()
        (uv_project / "src" / "writing" / "tone.mg").write_text("<<\nLocal tone\n>>\n")

        (uv_project / "src" / "main.mg").write_text("[[ writing/tone ]]\n")
        _, nodes = parser.parse((uv_project / "src" / "main.mg").read_text())

        package_paths = {
            "writing": site_packages / "writing_templates" / "templates",
        }
        renderer = Renderer(context={}, base_path=uv_project / "src", package_paths=package_paths)
        result = renderer.render(nodes)

        assert result == "Local tone\n"

    def test_missing_include_returns_empty_string(self, parser, tmp_path):
        (tmp_path / "main.mg").write_text("[[ nonexistent ]]\n")
        _, nodes = parser.parse((tmp_path / "main.mg").read_text())

        renderer = Renderer(context={}, base_path=tmp_path)
        result = renderer.render(nodes)

        assert result == ""

    def test_build_uv_package_paths_maps_names_to_templates_dirs(self, tmp_path):
        from margarita.cli import _build_uv_package_paths

        site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
        for pkg_name, module_name in (("alpha", "alpha_pkg"), ("beta", "beta_pkg")):
            templates_dir = site_packages / module_name / "templates"
            templates_dir.mkdir(parents=True)
            dist_info = site_packages / f"{module_name}-1.0.dist-info"
            dist_info.mkdir()
            (dist_info / "METADATA").write_text(f"Name: {pkg_name}\n")
            (dist_info / "top_level.txt").write_text(f"{module_name}\n")

        paths = _build_uv_package_paths(tmp_path / "src")

        assert set(paths.keys()) == {"alpha", "beta"}
        assert paths["alpha"] == site_packages / "alpha_pkg" / "templates"
        assert paths["beta"] == site_packages / "beta_pkg" / "templates"

    def test_build_uv_package_paths_walks_up_to_find_venv(self, tmp_path):
        from margarita.cli import _build_uv_package_paths

        site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
        templates_dir = site_packages / "mypkg" / "templates"
        templates_dir.mkdir(parents=True)
        dist_info = site_packages / "mypkg-1.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Name: mypkg\n")
        (dist_info / "top_level.txt").write_text("mypkg\n")

        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        paths = _build_uv_package_paths(nested)

        assert paths == {"mypkg": templates_dir}

    def test_build_uv_package_paths_returns_empty_when_no_venv(self, tmp_path):
        from margarita.cli import _build_uv_package_paths

        assert _build_uv_package_paths(tmp_path) == {}

    def test_build_uv_package_paths_warns_on_duplicate_name(self, tmp_path, capsys):
        from margarita.cli import _build_uv_package_paths

        site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
        for module_name in ("dupe_a", "dupe_b"):
            templates_dir = site_packages / module_name / "templates"
            templates_dir.mkdir(parents=True)
            dist_info = site_packages / f"{module_name}-1.0.dist-info"
            dist_info.mkdir()
            (dist_info / "METADATA").write_text("Name: dupe\n")
            (dist_info / "top_level.txt").write_text(f"{module_name}\n")

        paths = _build_uv_package_paths(tmp_path)

        assert list(paths.keys()) == ["dupe"]
        captured = capsys.readouterr()
        assert "dupe" in captured.err
        assert "duplicate" in captured.err

    def test_build_uv_package_paths_falls_back_when_no_top_level_txt(self, tmp_path):
        from margarita.cli import _build_uv_package_paths

        site_packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
        templates_dir = site_packages / "my_lib" / "templates"
        templates_dir.mkdir(parents=True)
        dist_info = site_packages / "my_lib-2.0.dist-info"
        dist_info.mkdir()
        (dist_info / "METADATA").write_text("Name: my-lib\n")
        # no top_level.txt — fallback: strip version, normalize dashes to underscores

        paths = _build_uv_package_paths(tmp_path)

        assert paths == {"my-lib": templates_dir}
