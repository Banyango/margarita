---
description: Task Breakdown - Converts use cases into actionable implementation tasks
parameters: input (string) - Use case to break down into tasks
---
<<
Your task is to expand the following ask into a more detailed set of requirements/ task breakdown.

- The output should be a more detailed description of the task, without implementation details.
- Consult AGENTS.md for code standards and best practices for writing clear, actionable tasks.
- Ask any follow up questions to reduce ambiguity and ensure the task is well defined.
- Keep the number of tasks to a small amount ideally 1-3.
- We should follow Red, Green, Refactor where possible.

Create a list to store the task breakdown. Each task should have the following structure:
{
    "task": "The refined feature description",
    "acceptanceCriteria": [
        "A specific, measurable outcome that indicates the task is successfully implemented.",
        "Another specific, measurable outcome that indicates the task is successfully implemented.",
        "Additional criteria as needed to fully capture the requirements."
    ]
}

Store the list of tasks in the `tasks` state variable.

## This is the use case that should be broken down:
${input}
>>

