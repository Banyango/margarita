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
            "# Greeting\n"
            "Please sign in to continue.\n"
            "# Footer\n"
            "Thank you for using our service.\n"
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
            '# System Prompt\n'
             'You are an AI assistant helping with question answering.\n'
             '\n'
             '# Instructions\n'
             'Use the following context to answer:\n'
             '    - Title: Doc1\n'
             '    - Content: Available\n'
             '    - Title: Doc2\n'
             '    - Content: Available\n'
             '# User Query = What is the capital of France?\n'
             '\n'
             '# Output Format\n'
             'Provide your response in plain text.\n'
             '# Additional Notes\n'
             '- Be concise\n'
             '- Be accurate\n'
             '- Be helpful\n'
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
            '# System Prompt\n'
             'You are an AI assistant helping with general inquiry.\n'
             '\n'
             '# Instructions\n'
             'Answer based on your general knowledge.\n'
             '# User Query = Tell me about AI\n'
             '\n'
             '# Output Format\n'
             'Provide your response in JSON format.\n'
             '# Additional Notes\n'
             '- Be concise\n'
             '- Be accurate\n'
             '- Be helpful\n'
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
            '# Nested Conditionals and Loops\n'
            '\n'
            'This shows how to use the new syntax for building marg files.\n'
            '# Categories\n'
            '## Category: Electronics\n'
            'Items in this category:\n'
            '- Item1\n'
            '- Item2\n'
            '## Category: Books\n'
            'Items in this category:\n'
            '- Item1\n'
            '- Item2\n'
            '# End\n'
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
            'This is the header content.\n'
            'Generated by header.prompt file.\n'
            '\n'
            '# Main Content\n'
            'This is the main content section.\n'
            '---\n'
            'This is the footer content.\n'
            'End of document.\n'
            '\n'
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
            "- Item: 1\n"
            "- Item: 2\n"
            "- Item: 3\n"
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
