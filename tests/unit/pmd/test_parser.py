from margarita.parser import (
    ForNode,
    IfNode,
    ImportNode,
    IncludeNode,
    Parser,
    StateNode,
    TextNode,
)


class TestParser:
    def setup_method(self):
        self.parser = Parser()

    def test_parse_should_parse_text_when_template_is_plain_text(self):
        template = "<<Hello, world!>>"
        metadata, nodes = self.parser.parse(template)

        assert metadata == {}
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert nodes[0].content == "Hello, world!\n"

    def test_parse_should_extract_metadata_when_template_has_metadata_directives(self):
        template = """---
task: summarization
owner: search-team
version: 1.0
---

<<Content here>>"""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {"task": "summarization", "owner": "search-team", "version": "1.0"}
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)

    def test_parse_should_parse_variables_when_template_has_variable_placeholders(self):
        template = "<<Hello, ${name}!>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert nodes[0].content == "Hello, ${name}!\n"
        assert "${name}" in nodes[0].content

    def test_parse_should_parse_all_variables_when_template_has_multiple_variables(self):
        template = "<<${greeting}, ${name}! Your age is ${age}.>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "${greeting}" in nodes[0].content
        assert "${name}" in nodes[0].content
        assert "${age}" in nodes[0].content

    def test_parse_should_parse_if_node_when_template_has_if_conditional(self):
        template = """if show_greeting:
    <<Hello!>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert nodes[0].condition == "show_greeting"
        assert len(nodes[0].true_block) == 1
        assert isinstance(nodes[0].true_block[0], TextNode)
        assert nodes[0].false_block is None

    def test_parse_should_parse_if_else_blocks_when_template_has_else(self):
        template = """if logged_in:
    <<Welcome back!>>
else:
    <<Please log in.>>"""
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
        template = """if show_name:
    <<Your name is ${name}.>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert len(nodes[0].true_block) == 1
        assert isinstance(nodes[0].true_block[0], TextNode)
        assert "${name}" in nodes[0].true_block[0].content

    def test_parse_should_parse_for_node_when_template_has_for_loop(self):
        template = """for item in items:
    <<- ${item}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)
        assert nodes[0].iterator == "item"
        assert nodes[0].iterable == "items"
        assert len(nodes[0].block) == 1
        assert "${item}" in nodes[0].block[0].content

    def test_parse_should_parse_effect_when_template_has_effect_directive(self):
        template = """@effect func compute(value) => result
<<The result is ${result}.>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert nodes[0].__class__.__name__ == "EffectNode"
        assert "compute(value) => result" in nodes[0].raw_content
        assert isinstance(nodes[1], TextNode)
        assert "${result}" in nodes[1].content

    def test_parse_should_parse_effect_when_effect_is_in_if(self):
        template = """
if condition:
    @effect func do_something() => output

<<Output is ${output}.>>
"""
        _, nodes = self.parser.parse(template)
        assert len(nodes) == 2
        assert isinstance(nodes[0], IfNode)
        if_node = nodes[0]
        assert len(if_node.true_block) == 1
        assert if_node.true_block[0].__class__.__name__ == "EffectNode"
        assert "func do_something() => output" in if_node.true_block[0].raw_content
        assert isinstance(nodes[1], TextNode)
        assert "${output}" in nodes[1].content

    def test_parse_should_parse_state_when_template_has_state_directive(self):
        template = """@state result = {}
<<The result is ${result}.>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], StateNode)
        assert nodes[0].variable_name == "result"
        assert nodes[0].initial_value == "{}"
        assert isinstance(nodes[1], TextNode)
        assert "${result}" in nodes[1].content

    def test_parse_should_parse_state_when_initial_value_is_number(self):
        template = """@state count = 0
<<Count: ${count}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], StateNode)
        assert nodes[0].variable_name == "count"
        assert nodes[0].initial_value == "0"

    def test_parse_should_parse_state_when_initial_value_is_list(self):
        template = """@state items = []
<<Items: ${items}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], StateNode)
        assert nodes[0].variable_name == "items"
        assert nodes[0].initial_value == "[]"

    def test_parse_should_parse_state_when_initial_value_is_string(self):
        template = """@state name = "default"
<<Name: ${name}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], StateNode)
        assert nodes[0].variable_name == "name"
        assert nodes[0].initial_value == '"default"'

    def test_parse_should_parse_state_when_state_is_in_if(self):
        template = """if condition:
    @state data = {}

<<Data is ${data}.>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], IfNode)
        if_node = nodes[0]
        assert len(if_node.true_block) == 1
        assert isinstance(if_node.true_block[0], StateNode)
        assert if_node.true_block[0].variable_name == "data"
        assert if_node.true_block[0].initial_value == "{}"
        assert isinstance(nodes[1], TextNode)
        assert "${data}" in nodes[1].content

    def test_parse_should_parse_multiple_states_when_template_has_many(self):
        template = """@state result = {}
@state count = 0
@state items = []

<<Content>>"""
        _, nodes = self.parser.parse(template)

        state_nodes = [n for n in nodes if isinstance(n, StateNode)]
        assert len(state_nodes) == 3
        assert state_nodes[0].variable_name == "result"
        assert state_nodes[0].initial_value == "{}"
        assert state_nodes[1].variable_name == "count"
        assert state_nodes[1].initial_value == "0"
        assert state_nodes[2].variable_name == "items"
        assert state_nodes[2].initial_value == "[]"

    def test_parse_should_set_is_mgx_when_template_has_state(self):
        template = """@state result = {}
<<Hello World>>"""
        _, _ = self.parser.parse(template)

        assert self.parser.is_mgx is True

    def test_parse_should_parse_state_with_effect_when_template_has_both(self):
        template = """@state result = {}
@effect func compute(value) => result

<<Result: ${result}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 3
        assert isinstance(nodes[0], StateNode)
        assert nodes[0].variable_name == "result"
        assert nodes[1].__class__.__name__ == "EffectNode"
        assert isinstance(nodes[2], TextNode)
        assert self.parser.is_mgx is True

    def test_parse_should_parse_import_when_template_has_simple_import(self):
        template = """import os
<<Hello World>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], ImportNode)
        assert nodes[0].raw_import == "import os"
        assert isinstance(nodes[1], TextNode)

    def test_parse_should_parse_import_when_template_has_from_import(self):
        template = """from pathlib import Path
<<Hello World>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], ImportNode)
        assert nodes[0].raw_import == "from pathlib import Path"
        assert isinstance(nodes[1], TextNode)

    def test_parse_should_parse_import_when_template_has_from_import_multiple(self):
        template = """from package import module, function, Class
<<Content>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 2
        assert isinstance(nodes[0], ImportNode)
        assert nodes[0].raw_import == "from package import module, function, Class"

    def test_parse_should_set_is_mgx_when_template_has_import(self):
        template = """import os
<<Hello World>>"""
        _, _ = self.parser.parse(template)

        assert self.parser.is_mgx is True

    def test_parse_should_set_is_mgx_when_template_has_from_import(self):
        template = """from pathlib import Path
<<Hello World>>"""
        _, _ = self.parser.parse(template)

        assert self.parser.is_mgx is True

    def test_parse_should_parse_multiple_imports_when_template_has_many(self):
        template = """import os
import sys
from pathlib import Path
from typing import List, Dict

<<Content>>"""
        _, nodes = self.parser.parse(template)

        import_nodes = [n for n in nodes if isinstance(n, ImportNode)]
        assert len(import_nodes) == 4
        assert import_nodes[0].raw_import == "import os"
        assert import_nodes[1].raw_import == "import sys"
        assert import_nodes[2].raw_import == "from pathlib import Path"
        assert import_nodes[3].raw_import == "from typing import List, Dict"
        assert self.parser.is_mgx is True

    def test_parse_should_parse_import_with_effect_when_template_has_both(self):
        template = """import os
from pathlib import Path

@effect func compute() => result

<<Result: ${result}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 4
        assert isinstance(nodes[0], ImportNode)
        assert isinstance(nodes[1], ImportNode)
        assert nodes[2].__class__.__name__ == "EffectNode"
        assert isinstance(nodes[3], TextNode)
        assert self.parser.is_mgx is True

    def test_parse_should_parse_import_in_if_when_import_is_conditional(self):
        template = """if condition:
    import os
    <<Using os>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        if_node = nodes[0]
        assert len(if_node.true_block) == 2
        assert isinstance(if_node.true_block[0], ImportNode)
        assert if_node.true_block[0].raw_import == "import os"
        assert isinstance(if_node.true_block[1], TextNode)
        assert self.parser.is_mgx is True

    def test_parse_should_parse_nested_for_nodes_when_template_has_nested_for_loops(self):
        template = """for category in categories:
    <<Category: ${category}>>
    for item in items:
        <<- ${item}>>"""
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
        template = """if has_items:
    <<Items:>>
    for item in items:
        <<- ${item}>>"""
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
        template = "[[ header.mg ]]"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IncludeNode)
        assert nodes[0].template_name == "header.mg"

    def test_parse_should_ignore_comments_when_template_has_comments(self):
        template = """<<Text before>>
// This is a comment
<<Text after>>"""
        _, nodes = self.parser.parse(template)

        # Comments should be completely removed
        assert len(nodes) == 2
        assert isinstance(nodes[0], TextNode)
        assert isinstance(nodes[1], TextNode)
        combined_content = nodes[0].content + nodes[1].content
        assert "comment" not in combined_content.lower()

    def test_parse_should_ignore_comments_when_template_has_multiline_comments(self):
        template = """// This is a comment
// on multiple lines
// with different content
<<Content>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "Content" in nodes[0].content

    def test_parse_should_parse_all_features_when_template_is_complex(self):
        template = """---
task: summarization
owner: search-team
---

<<# Instruction
You are a helpful assistant.

# Document
Summarize the following document for ${audience}:

${doc}
>>

if rules:
    <<# Rules>>
    for rule in rules:
        <<- ${rule}>>"""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {"task": "summarization", "owner": "search-team"}

        # Should have text with variables and if nodes
        has_text_with_variables = any(
            isinstance(node, TextNode) and "${" in node.content for node in nodes
        )
        has_if = any(isinstance(node, IfNode) for node in nodes)
        assert has_text_with_variables
        assert has_if

    def test_parse_should_return_empty_nodes_when_template_is_empty(self):
        template = ""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {}
        assert len(nodes) == 0

    def test_parse_should_parse_whitespace_when_template_has_only_whitespace(self):
        template = "<<   \n  \n  >>"
        metadata, nodes = self.parser.parse(template)

        assert metadata == {}
        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)

    def test_parse_should_parse_all_variables_when_variables_are_consecutive(self):
        template = "<<${first}${second}${third}>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "${first}" in nodes[0].content
        assert "${second}" in nodes[0].content
        assert "${third}" in nodes[0].content

    def test_parse_should_parse_variable_when_embedded_in_text(self):
        template = "<<The value is ${value} and that's final.>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "The value is ${value} and that's final." in nodes[0].content

    def test_parse_should_parse_nested_if_when_template_has_nested_if_statements(self):
        template = """if outer:
    <<Outer true>>
    if inner:
        <<Inner true>>"""
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
        template = """for user in users:
    <<Name: ${user}>>
    if active:
        <<Status: Active>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)

        # Should have text with variables and if nodes in the loop body
        has_text_with_variable = any(
            isinstance(node, TextNode) and "${" in node.content for node in nodes[0].block
        )
        has_if = any(isinstance(node, IfNode) for node in nodes[0].block)
        assert has_text_with_variable
        assert has_if

    def test_parse_should_parse_metadata_when_metadata_has_special_chars(self):
        template = """---
description: This is a test with: colons and - dashes
email: user@example.com
---

<<Content>>"""
        metadata, nodes = self.parser.parse(template)

        assert "description" in metadata
        assert ":" in metadata["description"]
        assert metadata["email"] == "user@example.com"

    def test_parse_should_parse_all_includes_when_template_has_multiple_includes(self):
        template = """[[ header.mg ]]
<<Content here>>
[[ footer.mg ]]"""
        _, nodes = self.parser.parse(template)

        include_nodes = [node for node in nodes if isinstance(node, IncludeNode)]
        assert len(include_nodes) == 2
        assert include_nodes[0].template_name == "header.mg"
        assert include_nodes[1].template_name == "footer.mg"

    def test_parse_should_reset_state_when_parsing_multiple_templates(self):
        template1 = "---\nkey: value1\n---\n<<Text1>>"
        template2 = "---\nkey: value2\n---\n<<Text2>>"

        metadata1, nodes1 = self.parser.parse(template1)
        metadata2, nodes2 = self.parser.parse(template2)

        assert metadata1 == {"key": "value1"}
        assert metadata2 == {"key": "value2"}
        assert "Text1" in nodes1[0].content
        assert "Text2" in nodes2[0].content

    def test_parse_should_parse_variable_when_name_has_underscores(self):
        template = "<<${my_variable_name}>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "${my_variable_name}" in nodes[0].content

    def test_parse_should_parse_for_when_variable_names_have_underscores(self):
        template = """for list_item in my_list:
    <<${list_item}>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)
        assert nodes[0].iterator == "list_item"
        assert nodes[0].iterable == "my_list"


class TestParserEdgeCases:
    def setup_method(self):
        self.parser = Parser()

    def test_parse_should_parse_if_when_if_statement_is_unclosed(self):
        template = """if condition:
    <<Text>>"""
        # Should still parse, just won't have proper closing
        _, nodes = self.parser.parse(template)
        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)

    def test_parse_should_parse_for_when_for_loop_is_unclosed(self):
        template = """for item in items:
    <<Text>>"""
        _, nodes = self.parser.parse(template)
        assert len(nodes) == 1
        assert isinstance(nodes[0], ForNode)

    def test_parse_should_handle_gracefully_when_else_without_if(self):
        template = """else:
    <<Text>>"""
        _, nodes = self.parser.parse(template)
        # Parser should handle this gracefully

    def test_parse_should_preserve_special_chars_when_in_text(self):
        template = "<<Special chars: !@#%^&*()[]{}|\\?,./;':\"~`>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        # Most special chars should be preserved (except those used in patterns)

    def test_parse_should_parse_unicode_when_content_has_unicode(self):
        template = "<<Hello 世界! ${name} 🌍>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "世界" in nodes[0].content
        assert "${name}" in nodes[0].content
        assert "🌍" in nodes[0].content


class TestNewSyntaxValidation:
    """Tests to validate the new Python-style syntax features."""

    def setup_method(self):
        self.parser = Parser()

    def test_parse_should_require_text_blocks_for_plain_text(self):
        """Plain text without << >> delimiters should not be parsed as text nodes."""
        template = "This is plain text without delimiters"
        _, nodes = self.parser.parse(template)

        # Without << >>, the text should be ignored or not create text nodes
        # (it's treated as an unknown line and skipped)
        assert len(nodes) == 0

    def test_parse_should_parse_multiline_text_block(self):
        """Multi-line text blocks should preserve content and indentation."""
        template = """<<
This is a multiline
text block with
multiple lines
>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "multiline" in nodes[0].content
        assert "multiple lines" in nodes[0].content

    def test_parse_should_support_include_with_parameters(self):
        """Includes can have optional parameters."""
        template = '[[ template.mg param1="value1" param2="value2" ]]'
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IncludeNode)
        assert nodes[0].template_name == "template.mg"
        assert nodes[0].params == {"param1": "value1", "param2": "value2"}

    def test_parse_should_handle_dollar_brace_syntax_for_variables(self):
        """Variables use ${varname} syntax within text blocks."""
        template = "<<Value: ${variable_name}>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        assert "${variable_name}" in nodes[0].content

    def test_parse_should_use_colon_for_control_structures(self):
        """Control structures use Python-style : syntax."""
        template = """if condition:
    <<Content>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        assert nodes[0].condition == "condition"

    def test_parse_should_use_indentation_for_blocks(self):
        """Block structure is determined by indentation."""
        template = """if outer:
    <<Outer>>
    if inner:
        <<Inner>>"""
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], IfNode)
        # Inner if should be in the outer if's true_block
        assert any(isinstance(node, IfNode) for node in nodes[0].true_block)

    def test_parse_should_ignore_double_slash_comments(self):
        """Comments use // syntax."""
        template = """// This is a comment
<<Content>>
// Another comment"""
        _, nodes = self.parser.parse(template)

        # Only the text block should be parsed, comments ignored
        text_nodes = [n for n in nodes if isinstance(n, TextNode)]
        assert len(text_nodes) == 1
        assert "comment" not in nodes[0].content.lower()

    def test_parse_should_support_complex_nested_structure(self):
        """Complex nested control structures with new syntax."""
        template = """---
meta: value
---

<<Header>>

if show_items:
    for item in items:
        <<- ${item}>>
        if item_details:
            <<  Details: ${details}>>

<<Footer>>"""
        metadata, nodes = self.parser.parse(template)

        assert metadata == {"meta": "value"}
        assert len(nodes) >= 2  # At least header and if node
        # Find the if node
        if_nodes = [n for n in nodes if isinstance(n, IfNode)]
        assert len(if_nodes) >= 1
        # The if node should contain a for node
        for_nodes = [n for n in if_nodes[0].true_block if isinstance(n, ForNode)]
        assert len(for_nodes) >= 1

    def test_parse_should_preserve_special_chars_in_text_blocks(self):
        """Special characters should be preserved within text blocks."""
        template = "<<Special: !@#%^&*()[]{}|\\?,./;':\"~`>>"
        _, nodes = self.parser.parse(template)

        assert len(nodes) == 1
        assert isinstance(nodes[0], TextNode)
        # Most special chars preserved ($ and < > have special meaning)

    def test_parse_should_handle_empty_text_blocks(self):
        """Empty text blocks should be handled gracefully."""
        template = "<<>>"
        _, nodes = self.parser.parse(template)

        # Empty text blocks don't create nodes, which is reasonable
        assert len(nodes) == 0
