---
task: complex-template
owner: ai-team
version: 1.5
---

<<
# System Prompt
You are an AI assistant helping with ${task_type}.

# Instructions
>>

if has_context:
    <<Use the following context to answer:>>
    for doc in documents:
        <<
            - Title: ${doc.title}
            - Content: Available
        >>
else:
    << Answer based on your general knowledge. >>

<<
# User Query = ${query}

# Output Format
>>

if format_json:
    << Provide your response in JSON format. >>
else:
    << Provide your response in plain text. >>

// This is a comment that should be ignored

<<
# Additional Notes
- Be concise
- Be accurate
- Be helpful
>>
