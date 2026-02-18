from margarita.parser import Parser
from margarita.renderer import Renderer


class TestRenderer:
    def setup_method(self):
        self.parser = Parser()

    def test_render_should_output_text_when_template_is_plain_text(self):
        template = "<<Hello, world!>>"
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={})
        result = renderer.render(nodes)

        assert result == "Hello, world!\n"

    def test_render_should_substitute_variable_when_template_has_variable(self):
        template = "<<Hello, ${name}!>>"
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"name": "Alice"})
        result = renderer.render(nodes)

        assert result == "Hello, Alice!\n"

    def test_render_should_substitute_multiple_variables_when_template_has_many(self):
        template = "<<${greeting}, ${name}! Your age is ${age}.>>"
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"greeting": "Hi", "name": "Bob", "age": 25})
        result = renderer.render(nodes)

        assert result == "Hi, Bob! Your age is 25.\n"

    def test_render_should_render_true_block_when_simple_condition_is_truthy(self):
        template = """if show_greeting:
    <<Hello!>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"show_greeting": True})
        result = renderer.render(nodes)

        assert "Hello!" in result

    def test_render_should_render_false_block_when_simple_condition_is_falsy(self):
        template = """if logged_in:
    <<Welcome back!>>
else:
    <<Please log in.>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"logged_in": False})
        result = renderer.render(nodes)

        assert "Please log in." in result
        assert "Welcome back!" not in result

    def test_render_should_render_true_block_when_string_equals_comparison_is_true(self):
        template = """if node == "formal":
    <<This is formal mode>>
else:
    <<This is not formal mode>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"node": "formal"})
        result = renderer.render(nodes)

        assert "This is formal mode" in result
        assert "This is not formal mode" not in result

    def test_render_should_render_false_block_when_string_equals_comparison_is_false(self):
        template = """if node == "formal":
    <<This is formal mode>>
else:
    <<This is not formal mode>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"node": "informal"})
        result = renderer.render(nodes)

        assert "This is not formal mode" in result
        assert "This is formal mode" not in result

    def test_render_should_evaluate_not_equal_when_condition_has_inequality(self):
        template = """if status != "active":
    <<Status is not active>>
else:
    <<Status is active>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"status": "inactive"})
        result = renderer.render(nodes)

        assert "Status is not active" in result

    def test_render_should_evaluate_greater_than_when_condition_has_comparison(self):
        template = """if count > 5:
    <<Many items>>
else:
    <<Few items>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"count": 10})
        result = renderer.render(nodes)

        assert "Many items" in result
        assert "Few items" not in result

    def test_render_should_evaluate_less_than_when_condition_has_comparison(self):
        template = """if age < 18:
    <<Minor>>
else:
    <<Adult>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"age": 15})
        result = renderer.render(nodes)

        assert "Minor" in result
        assert "Adult" not in result

    def test_render_should_evaluate_greater_equal_when_condition_has_comparison(self):
        template = """if score >= 90:
    <<Grade A>>
else:
    <<Grade B or lower>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"score": 95})
        result = renderer.render(nodes)

        assert "Grade A" in result

    def test_render_should_evaluate_less_equal_when_condition_has_comparison(self):
        template = """if temperature <= 32:
    <<Freezing>>
else:
    <<Not freezing>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"temperature": 25})
        result = renderer.render(nodes)

        assert "Freezing" in result

    def test_render_should_compare_with_string_literal_when_using_double_quotes(self):
        template = """if mode == "debug":
    <<Debug mode active>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"mode": "debug"})
        result = renderer.render(nodes)

        assert "Debug mode active" in result

    def test_render_should_compare_with_string_literal_when_using_single_quotes(self):
        template = """if mode == 'production':
    <<Production mode active>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"mode": "production"})
        result = renderer.render(nodes)

        assert "Production mode active" in result

    def test_render_should_compare_with_integer_literal_when_comparing_numbers(self):
        template = """if level == 5:
    <<Level five reached>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"level": 5})
        result = renderer.render(nodes)

        assert "Level five reached" in result

    def test_render_should_compare_with_float_literal_when_comparing_decimals(self):
        template = """if price > 9.99:
    <<Premium item>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"price": 19.99})
        result = renderer.render(nodes)

        assert "Premium item" in result

    def test_render_should_handle_dotted_variable_in_comparison(self):
        template = """if user.role == "admin":
    <<Admin access granted>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"user": {"role": "admin"}})
        result = renderer.render(nodes)

        assert "Admin access granted" in result

    def test_render_should_iterate_when_template_has_for_loop(self):
        template = """for item in items:
    <<- ${item}>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"items": ["apple", "banana", "cherry"]})
        result = renderer.render(nodes)

        assert "apple" in result
        assert "banana" in result
        assert "cherry" in result

    def test_render_should_handle_nested_if_when_conditions_are_nested(self):
        template = """if outer:
    <<Outer true>>
    if inner:
        <<Inner true>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"outer": True, "inner": True})
        result = renderer.render(nodes)

        assert "Outer true" in result
        assert "Inner true" in result

    def test_render_should_handle_empty_context_when_no_variables_needed(self):
        template = "<<Static text>>"
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={})
        result = renderer.render(nodes)

        assert result == "Static text\n"

    def test_render_should_handle_missing_variable_gracefully(self):
        template = "<<Hello, ${name}!>>"
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={})
        result = renderer.render(nodes)

        # Should render with empty string or None for missing variables
        assert "Hello," in result

    def test_render_should_evaluate_comparison_when_both_sides_are_variables(self):
        template = """if current_user == admin_user:
    <<You are the admin>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"current_user": "alice", "admin_user": "alice"})
        result = renderer.render(nodes)

        assert "You are the admin" in result

    def test_render_should_handle_boolean_true_literal_in_comparison(self):
        template = """if enabled == true:
    <<Feature is enabled>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"enabled": True})
        result = renderer.render(nodes)

        assert "Feature is enabled" in result

    def test_render_should_handle_boolean_false_literal_in_comparison(self):
        template = """if disabled == false:
    <<Feature is not disabled>>"""
        _, nodes = self.parser.parse(template)
        renderer = Renderer(context={"disabled": False})
        result = renderer.render(nodes)

        assert "Feature is not disabled" in result

