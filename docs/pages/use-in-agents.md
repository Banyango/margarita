# Using MARGARITA in Agentic Loops

MARGARITA's dynamic rendering capabilities make it ideal for use in agentic AI workflows where prompts need to be generated, modified, and refined through multiple iterations.

## Why MARGARITA for Agents?

Agentic systems often need to:

- Generate prompts dynamically based on changing context
- Iterate through multiple LLM calls with evolving state
- Maintain structured, versioned prompt templates
- Compose complex prompts from reusable components


## Agentic Loop Example

Here's a practical example of using MARGARITA in a multi-step agent workflow:

```python
from pathlib import Path
from margarita.parser import Parser
from margarita.renderer import Renderer


class ResearchAgent:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.parser = Parser()
        self.conversation_history = []

    def render_prompt(self, template_name: str, context: dict) -> str:
        """Render a template with the given context."""
        template_path = self.template_dir / template_name
        template_content = template_path.read_text()

        _, nodes = self.parser.parse(template_content)
        renderer = Renderer(
            context=context,
            base_path=self.template_dir
        )
        return renderer.render(nodes)

    def research_loop(self, topic: str, max_iterations: int = 3):
        """Execute a research loop with iterative refinement."""
        findings = []

        for iteration in range(max_iterations):
            # Render the research prompt
            prompt = self.render_prompt("research.mg", {
                "topic": topic,
                "iteration": iteration + 1,
                "previous_findings": findings,
                "history": self.conversation_history
            })

            # Call your LLM (pseudo-code)
            response = self.call_llm(prompt)

            # Store findings
            findings.append({
                "iteration": iteration + 1,
                "query": topic,
                "result": response
            })

            # Update conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            # Check if we should continue
            if self.should_stop(response):
                break

        # Generate final summary
        summary_prompt = self.render_prompt("summary.mg", {
            "topic": topic,
            "findings": findings,
            "total_iterations": len(findings)
        })

        return self.call_llm(summary_prompt)

    def call_llm(self, prompt: str) -> str:
        """Call your LLM API (implement with your preferred provider)."""
        # Example: OpenAI, Anthropic, local model, etc.
        pass

    def should_stop(self, response: str) -> bool:
        """Determine if the research loop should stop."""
        # Implement your stopping logic
        return "COMPLETE" in response
```

## Template Examples

### research.mg

```margarita
---
name: research-prompt
version: 1.0.0
description: Iterative research prompt for agent loops
---
<<
You are a research assistant conducting iteration ${iteration} of your research.

Topic: ${topic}
>>

if previous_findings:
    <<
    ## Previous Findings
    >>
    for finding in previous_findings:
        <<
        ### Iteration ${finding.iteration}
        ${finding.result}
        >>

if history:
    <<## Conversation History>>
    for message in history:
        <<
        **${message.role}**: ${message.content}
        >>
<< ## Your Task >>

Continue researching this topic. Build upon previous findings and provide new insights.
When your research is complete, include the word COMPLETE in your response.
```

### summary.mg

```margarita
---
name: summary-prompt
version: 1.0.0
description: Generate final summary from research findings
---
<<
# Research Summary

Topic: ${topic}
Total Iterations: ${total_iterations}

## All Findings
>>

for finding in findings
    <<
    ### Research Phase ${finding.iteration}

    **Query**: ${finding.query}

    **Results**:
    ${finding.result}
    >>
<<
## Your Task

Synthesize all the above findings into a coherent, comprehensive summary.
Highlight key insights and actionable takeaways.
>>
```

## Dynamic Context Updates

MARGARITA's renderer allows you to update context dynamically within your agent loop:

```python
# Initial context
context = {
    "user_query": "Explain quantum computing",
    "difficulty": "intermediate",
    "previous_attempts": []
}

# Parse template once
parser = Parser()
_, nodes = parser.parse(template_content)

# Agent loop with evolving context
for i in range(5):
    # Create renderer with current context
    renderer = Renderer(context=context, base_path=Path("."))
    prompt = renderer.render(nodes)

    # Get LLM response
    response = call_llm(prompt)

    # Update context for next iteration
    context["previous_attempts"].append({
        "attempt": i + 1,
        "response": response
    })

    # Adjust difficulty based on response quality
    if "too simple" in response.lower():
        context["difficulty"] = "advanced"
    elif "too complex" in response.lower():
        context["difficulty"] = "beginner"
```
