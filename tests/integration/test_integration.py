"""Integration tests that run .marg files through the parser and renderer.

This module tests the complete pipeline: parsing .marg template files,
render them with test data, and verifying the output matches expected results.
"""

import pathlib

import pytest

from margarita.parser import Parser
from margarita.renderer import Renderer


class TestMargaritaIntegration:
    """Integration tests for parsing and render .marg templates."""

    @pytest.fixture
    def parser(self):
        """Create a fresh parser instance."""
        return Parser()

    @pytest.fixture
    def files_dir(self):
        """Get the files directory path."""
        return pathlib.Path(__file__).parent / "files"

    def test_simple_template(self, parser, files_dir):
        """Test simple.marg with basic variable substitution."""
        template_file = files_dir / "simple.marg"
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
        """Test metadata.marg with metadata and variable substitution."""
        template_file = files_dir / "metadata.marg"
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
        """Test conditional.marg with authenticated user (true branch)."""
        template_file = files_dir / "conditional.marg"
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
            "\n"
            "# Greeting\n\n"
            "Welcome back, Bob!\n\n"
            "Your account status: Premium\n"
            "\n"
            "# Footer\n"
            "Thank you for using our service.\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_template_unauthenticated(self, parser, files_dir):
        """Test conditional.marg with unauthenticated user (false branch)."""
        template_file = files_dir / "conditional.marg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with unauthenticated context
        renderer = Renderer(context={"is_authenticated": False})
        result = renderer.render(nodes)

        # Expected output
        expected = (
            "\n"
            "# Greeting\n\n"
            "Please sign in to continue.\n"
            "\n# Footer\n"
            "Thank you for using our service.\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_loop_template(self, parser, files_dir):
        """Test loop.marg with for loop iteration."""
        template_file = files_dir / "loop.marg"
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
        """Test loop.marg with empty items list."""
        template_file = files_dir / "loop.marg"
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
        """Test complex.marg with nested if/for statements."""
        template_file = files_dir / "complex.marg"
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
            "\n"
            "# System Prompt\n"
            "You are an AI assistant helping with question answering.\n"
            "\n"
            "# Instructions\n"
            "Use the following context to answer:\n"
            "\n"
            "Document {'title': 'Doc1', 'content': 'Available'}:\n"
            "- Title: Doc1\n"
            "- Content: Available\n"
            "Document {'title': 'Doc2', 'content': 'Available'}:\n"
            "- Title: Doc2\n"
            "- Content: Available\n"
            "\n"
            "# User Query\n"
            "What is the capital of France?\n"
            "\n"
            "# Output Format\n"
            "Provide your response in plain text.\n"
            "\n"
            "\n"
            "# Additional Notes\n"
            "- Be concise\n"
            "- Be accurate\n"
            "- Be helpful\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_complex_template_no_context(self, parser, files_dir):
        """Test complex.marg with has_context=False."""
        template_file = files_dir / "complex.marg"
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
            "\n"
            "# System Prompt\n"
            "You are an AI assistant helping with general inquiry.\n\n"
            "# Instructions\n"
            "Answer based on your general knowledge.\n"
            "\n"
            "# User Query\n"
            "Tell me about AI\n\n"
            "# Output Format\n"
            "Provide your response in JSON format.\n"
            "\n"
            "\n"
            "# Additional Notes\n"
            "- Be concise\n"
            "- Be accurate\n"
            "- Be helpful\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_nested_template(self, parser, files_dir):
        """Test nested.marg with deeply nested structures."""
        template_file = files_dir / "nested.marg"
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
            "\n"
            "# Nested Conditionals and Loops\n\n"
            "# Categories\n\n"
            "## Category: Electronics\n\n"
            "Items in this category:\n"
            "  - Item1\n"
            "  - Item2\n"
            "\n"
            "## Category: Books\n\n"
            "Items in this category:\n"
            "  - Item1\n"
            "  - Item2\n"
            "\n"
            "\n# End\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_nested_template_no_items(self, parser, files_dir):
        """Test nested.marg with show_items=False."""
        template_file = files_dir / "nested.marg"
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
            "\n"
            "# Nested Conditionals and Loops\n\n"
            "# Categories\n\n"
            "## Category: Electronics\n\n"
            "No items to display.\n"
            "\n"
            "\n# End\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_include_template(self, parser, files_dir):
        template_file = files_dir / "include.marg"
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
            "\n"
            "This is the header content.\n"
            "Generated by header.prompt file.\n"
            "\n"
            "\n"
            "# Main Content\n"
            "This is the main content section.\n"
            "\n"
            "---\n"
            "This is the footer content.\n"
            "End of document.\n"
            "\n"
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_unicode_template_happy(self, parser, files_dir):
        """Test unicode.marg with unicode characters and emojis (happy=True)."""
        template_file = files_dir / "unicode.marg"
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
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_unicode_template_not_happy(self, parser, files_dir):
        """Test unicode.marg with unicode characters and emojis (happy=False)."""
        template_file = files_dir / "unicode.marg"
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
            "\n"
        )

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_includes_when_conditional_is_true(self, parser, files_dir):
        """Test conditional.marg with include directives in branches."""
        template_file = files_dir / "conditional_include.marg"
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
        expected = "\nTest Conditional Include\nHello Batman!\n"

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_conditional_includes_when_conditional_is_false(self, parser, files_dir):
        """Test conditional.marg with include directives in branches."""
        template_file = files_dir / "conditional_include.marg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with authenticated context
        renderer = Renderer(context={"extra_content": False, "name": "Batman"}, base_path=files_dir)
        result = renderer.render(nodes)

        # Expected output
        expected = "\nTest Conditional Include\n"

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
        template_file = files_dir / "nested_conditional.marg"
        with open(template_file, encoding="utf-8") as f:
            content = f.read()

        # Parse
        metadata, nodes = parser.parse(content)

        # Render with context
        renderer = Renderer(context={"is_authenticated": is_authenticated, "is_admin": is_admin})
        result = renderer.render(nodes)

        assert result == expected, f"Expected:\n{expected}\nGot:\n{result}"

    def test_nested_includes_subdir(self, parser, files_dir):
        template_file = files_dir / "nested_includes.marg"
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
        margarita_files = sorted(files_dir.glob("*.marg"))

        assert len(margarita_files) > 0, "No .marg files found"

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
        assert "simple.marg" in results
        assert "metadata.marg" in results
        assert "conditional.marg" in results
        assert "loop.marg" in results
        assert "complex.marg" in results
        assert "nested.marg" in results
        assert "include.marg" in results
        assert "unicode.marg" in results
