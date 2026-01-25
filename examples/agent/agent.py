"""
Simple Agent Example using MARGARITA Templates

This example demonstrates a basic conversational agent that tracks an internal context.

And how to we can use margarita to react differently based on that context.
"""

from pathlib import Path
from typing import Literal

import openai

from margarita.composer import Composer


class SimpleAgent:
    def __init__(self, template_dir: Path = None):
        """Initialize the agent.

        Args:
            template_dir: Directory containing .mg template files
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = template_dir
        self.composer = Composer(template_dir)

        # This could be persisted externally to maintain state across sessions.
        self.context = {
            "mood": "neutral",
        }

    def set_mood_level(self, level: Literal["helpful", "neutral", "sarcastic"]):
        # Using an internal state we can modify how prompts react to conversations.
        self.context["mood"] = level

    async def process_message(self, query: str) -> str:
        """Process a user message and generate a response prompt.

        Args:
            query: User input message
        """
        response = await openai.responses.create(
            {
                "model": "gpt-4o",
                "tools": [{type: "set_mood_level"}],
                "input": self.composer.render("set_mood.mg", {"query": query}),
            }
        )

        # ... Handle the tool call response where set mood level is invoked ...

        prompt = self.composer.compose_prompt(["system_prompt.mg", "mood.mg"], self.context)

        return prompt
