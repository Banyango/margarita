from pathlib import Path

from margarita.parser import Parser
from margarita.renderer import Renderer


class Composer:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.parser = Parser()
        self._template_cache: dict[str, tuple] = {}

    def load_template(self, template_path: str) -> tuple:
        """Load and parse a template, using cache if available.

        Args:
            template_path (str): Relative path to the template file.

        Returns:
            tuple: Parsed metadata and AST nodes of the template.
        """
        cache_key = str(template_path)

        if cache_key not in self._template_cache:
            full_path = self.template_dir / template_path
            content = full_path.read_text()
            parsed = self.parser.parse(content)
            self._template_cache[cache_key] = parsed

        return self._template_cache[cache_key]

    def render(self, template_path: str, context: dict) -> str:
        """Render a template with the given context.

        Args:
            template_path (str): Relative path to the template file.
            context (dict): Context dictionary for rendering.

        Returns:
            str: Rendered template string.
        """
        _, nodes = self.load_template(template_path)

        renderer = Renderer(context=context, base_path=self.template_dir)

        return renderer.render(nodes)

    def compose_prompt(self, snippets: list[str], context: dict, separator: str = "\n\n") -> str:
        """Compose a prompt from multiple snippet files.

        Args:
            snippets (list[str]): List of snippet template file paths.
            context (dict): Context dictionary for rendering.
            separator (str): Separator string between rendered snippets.

        Returns:
            str: Composed prompt string.
        """
        parts = []

        for snippet in snippets:
            rendered = self.render(snippet, context)
            parts.append(rendered)

        return separator.join(parts)
