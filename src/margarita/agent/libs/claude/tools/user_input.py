from pydantic import BaseModel

from margarita.agent import ContentBlock, ContentBlockType, ExecutionModel
from margarita.agent.core.agents.models import InputRequest


class Option(BaseModel):
    label: str
    description: str


class QuestionRequest(BaseModel):
    question: str
    header: str
    multiSelect: bool
    options: list[Option]


class UserInputTool:
    def __init__(self, execution_model: ExecutionModel):
        self.execution_model = execution_model

    async def ask_question(self, request: QuestionRequest) -> str:
        """Build a human-friendly prompt that includes an optional header, the
        question text, an enumerated list of options (with descriptions), and a
        short usage instruction depending on whether multiple selection is
        allowed.
        """
        parts: list[str] = []

        # Optional header
        if getattr(request, "header", None):
            parts.append(request.header)

        # Main question
        if getattr(request, "question", None):
            parts.append(request.question)

        # Options (support objects with attributes or simple dicts)
        options = getattr(request, "options", None) or []
        if options:
            parts.append("")  # blank line before list
            for idx, opt in enumerate(options, start=1):
                if isinstance(opt, dict):
                    label = opt.get("label", str(opt))
                    desc = opt.get("description", "")
                else:
                    label = getattr(opt, "label", None) or str(opt)
                    desc = getattr(opt, "description", None) or ""

                if desc:
                    parts.append(f"{idx}. {label} — {desc}")
                else:
                    parts.append(f"{idx}. {label}")

        # Instructions for answering
        if getattr(request, "multiSelect", False):
            if options:
                parts.append("")
            parts.append(
                'Select one or more options. Reply with a comma-separated list of numbers or labels (e.g. "1,3" or "apple,banana").'
            )
        elif options:
            parts.append("")
            parts.append(
                'Select one option. Reply with the number or the label (e.g. "1" or "apple").'
            )

        # Fallback to a one-line question if nothing assembled
        if parts:
            response = "[Question]\n" + "\n".join(parts)
        else:
            response = f"[Question] {getattr(request, 'question', '')}"

        # Append content block to the current run so the question is recorded
        self.execution_model.current_run.content_blocks.append(
            ContentBlock(type=ContentBlockType.INPUT, ref="", text=response)
        )

        # Post an InputRequest with full prompt and wait for the UI to resolve it
        input_request = InputRequest(prompt=response)
        await self.execution_model.request_input(input_request)

        return input_request.response or ""
