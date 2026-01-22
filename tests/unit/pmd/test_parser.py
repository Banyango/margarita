from margarita.parser import (
    ForNode,
    IfNode,
    IncludeNode,
    Parser,
    TextNode,
    VariableNode,
)


class TestParser:
    def setup_method(self):
        self.parser = Parser()

    def test_parse_should_parse_text_when_template_is_plain_text(self):
        template = "Hello, world!"
        metadata, nodes = self.parser.parse(template)

        assert metadata == {}
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert nodes[0].content == "Hello, world!"

    def test_parse_should_extract_metadata_when_template_has_metadata_directives(self):
        template = """@task: summarization
@owner: search-team
@version: 1.0

Content here"""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {"task": "summarization", "owner": "search-team", "version": "1.0"}
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)

    def test_parse_should_parse_variables_when_template_has_variable_placeholders(self):
        template = "Hello, {{name}}!"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 3
        assert isinstance(nodes[0], TextNode)
        assert nodes[0].content == "Hello, "
        assert isinstance(nodes[1], VariableNode)
        assert nodes[1].name == "name"
        assert isinstance(nodes[2], TextNode)
        assert nodes[2].content == "!"

    def test_parse_should_parse_all_variables_when_template_has_multiple_variables(self):
        template = "{{greeting}}, {{name}}! Your age is {{age}}."
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 6
        assert isinstance(nodes[0], VariableNode)
        assert nodes[0].name == "greeting"
        assert isinstance(nodes[2], VariableNode)
        assert nodes[2].name == "name"
        assert isinstance(nodes[4], VariableNode)
        assert nodes[4].name == "age"

    def test_parse_should_parse_if_node_when_template_has_if_conditional(self):
        template = """{% if show_greeting %}
Hello!
{% endif %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert nodes[0].condition == "show_greeting"
        assert len(nodes[0].true_block) == 1
        assert isinstance(nodes[0].true_block[0], TextNode)
        assert nodes[0].false_block is None

    def test_parse_should_parse_if_else_blocks_when_template_has_else(self):
        template = """{% if logged_in %}
Welcome back!
{% else %}
Please log in.
{% endif %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert nodes[0].condition == "logged_in"
        assert len(nodes[0].true_block) == 1
        assert "Welcome back!" in nodes[0].true_block[0].content
        assert nodes[0].false_block is not None
        assert len(nodes[0].false_block) == 1
        assert "Please log in." in nodes[0].false_block[0].content

    def test_parse_should_parse_variables_in_if_when_if_contains_variables(self):
        template = """{% if show_name %}
Your name is {{name}}.
{% endif %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert len(nodes[0].true_block) == 3
        assert isinstance(nodes[0].true_block[1], VariableNode)
        assert nodes[0].true_block[1].name == "name"

    def test_parse_should_parse_for_node_when_template_has_for_loop(self):
        template = """{% for item in items %}
- {{item}}
{% endfor %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)
        assert nodes[0].iterator == "item"
        assert nodes[0].iterable == "items"
        assert len(nodes[0].block) == 3

    def test_parse_should_parse_nested_for_nodes_when_template_has_nested_for_loops(self):
        template = """{% for category in categories %}
Category: {{category}}
{% for item in items %}
  - {{item}}
{% endfor %}
{% endfor %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)
        assert nodes[0].iterator == "category"
        inner_nodes = nodes[0].block
        # Find the nested for loop
        nested_for = None
        for node in inner_nodes:
            if isinstance(node, ForNode):
                nested_for = node
                break
        assert nested_for is not None
        assert nested_for.iterator == "item"

    def test_parse_should_parse_for_in_if_when_if_contains_for_loop(self):
        template = """{% if has_items %}
Items:
{% for item in items %}
- {{item}}
{% endfor %}
{% endif %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        # Find the for loop in the true block
        for_node = None
        for node in nodes[0].true_block:
            if isinstance(node, ForNode):
                for_node = node
                break
        assert for_node is not None
        assert for_node.iterator == "item"

    def test_parse_should_parse_include_when_template_has_include_directive(self):
        template = '{% include "header.marg" %}'
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IncludeNode)
        assert nodes[0].template_name == "header.marg"

    def test_parse_should_ignore_comments_when_template_has_comments(self):
        template = """Text before
{# This is a comment #}
Text after"""
        _, nodes = self.parser.parse(template)

        # Comments should be completely removed
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "comment" not in nodes[0].content.lower()

    def test_parse_should_ignore_comments_when_template_has_multiline_comments(self):
        template = """{# This is a
multiline
comment #}
Content"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "Content" in nodes[0].content

    def test_parse_should_parse_all_features_when_template_is_complex(self):
        template = """@task: summarization
@owner: search-team

# Instruction
You are a helpful assistant.

# Document
Summarize the following document for {{audience}}:

{{doc}}

{% if rules %}
# Rules
{% for rule in rules %}
- {{rule}}
{% endfor %}
{% endif %}"""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {"task": "summarization", "owner": "search-team"}

        # Should have text, variables, if, and for nodes
        has_variable = any(isinstance(node, VariableNode) for node in nodes)
        has_if = any(isinstance(node, IfNode) for node in nodes)
        assert has_variable
        assert has_if

    def test_parse_should_return_empty_nodes_when_template_is_empty(self):
        template = ""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {}
        assert len(nodes) == 0

    def test_parse_should_parse_whitespace_when_template_has_only_whitespace(self):
        template = "   \n  \n  "
        metadata, nodes = self.parser.parse(template)

        assert metadata == {}
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)

    def test_parse_should_parse_all_variables_when_variables_are_consecutive(self):
        template = "{{first}}{{second}}{{third}}"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 3
        assert all(isinstance(node, VariableNode) for node in nodes)
        assert nodes[0].name == "first"
        assert nodes[1].name == "second"
        assert nodes[2].name == "third"

    def test_parse_should_parse_variable_when_embedded_in_text(self):
        template = "The value is {{value}} and that's final."
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 3
        assert nodes[0].content == "The value is "
        assert nodes[1].name == "value"
        assert nodes[2].content == " and that's final."

    def test_parse_should_parse_nested_if_when_template_has_nested_if_statements(self):
        template = """{% if outer %}
Outer true
{% if inner %}
Inner true
{% endif %}
{% endif %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert nodes[0].condition == "outer"

        # Find nested if in true block
        nested_if = None
        for node in nodes[0].true_block:
            if isinstance(node, IfNode):
                nested_if = node
                break
        assert nested_if is not None
        assert nested_if.condition == "inner"

    def test_parse_should_parse_for_with_if_when_for_loop_has_complex_content(self):
        template = """{% for user in users %}
Name: {{user}}
{% if active %}
Status: Active
{% endif %}
{% endfor %}"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)

        # Should have text, variable, and if nodes in the loop body
        has_variable = any(isinstance(node, VariableNode) for node in nodes[0].block)
        has_if = any(isinstance(node, IfNode) for node in nodes[0].block)
        assert has_variable
        assert has_if

    def test_parse_should_parse_metadata_when_metadata_has_special_chars(self):
        template = """@description: This is a test with: colons and - dashes
@email: user@example.com

Content"""
        metadata, nodes = self.parser.parse(template)

        assert "description" in metadata
        assert ":" in metadata["description"]
        assert metadata["email"] == "user@example.com"

    def test_parse_should_parse_all_includes_when_template_has_multiple_includes(self):
        template = """{% include "header.marg" %}
Content here
{% include "footer.marg" %}"""
        _, nodes = self.parser.parse(template)

        include_nodes = [node for node in nodes if isinstance(node, IncludeNode)]
        assert len(include_nodes) == 2
        assert include_nodes[0].template_name == "header.marg"
        assert include_nodes[1].template_name == "footer.marg"

    def test_parse_should_reset_state_when_parsing_multiple_templates(self):
        template1 = "@key: value1\nText1"
        template2 = "@key: value2\nText2"

        metadata1, nodes1 = self.parser.parse(template1)
        metadata2, nodes2 = self.parser.parse(template2)

        assert metadata1 == {"key": "value1"}
        assert metadata2 == {"key": "value2"}
        assert "Text1" in nodes1[0].content
        assert "Text2" in nodes2[0].content

    def test_parse_should_parse_variable_when_name_has_underscores(self):
        template = "{{my_variable_name}}"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], VariableNode)
        assert nodes[0].name == "my_variable_name"

    def test_parse_should_parse_for_when_variable_names_have_underscores(self):
        template = "{% for list_item in my_list %}{{list_item}}{% endfor %}"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)
        assert nodes[0].iterator == "list_item"
        assert nodes[0].iterable == "my_list"


class TestParserEdgeCases:
    def setup_method(self):
        self.parser = Parser()

    def test_parse_should_parse_if_when_if_statement_is_unclosed(self):
        template = "{% if condition %}Text"
        # Should still parse, just won't have proper closing
        _, nodes = self.parser.parse(template)
        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)

    def test_parse_should_parse_for_when_for_loop_is_unclosed(self):
        template = "{% for item in items %}Text"
        _, nodes = self.parser.parse(template)
        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)

    def test_parse_should_handle_gracefully_when_else_without_if(self):
        template = "{% else %}Text{% endif %}"
        _, nodes = self.parser.parse(template)
        # Parser should handle this gracefully

    def test_parse_should_preserve_special_chars_when_in_text(self):
        template = "Special chars: !@#$%^&*()[]{}|\\<>?,./;':\"~`"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        # Most special chars should be preserved (except those used in patterns)

    def test_parse_should_parse_unicode_when_content_has_unicode(self):
        template = "Hello 世界! {{name}} 🌍"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 3
        assert "世界" in nodes[0].content
        assert isinstance(nodes[1], VariableNode)
        assert "🌍" in nodes[2].content
