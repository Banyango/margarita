---
task: multi-model-agent
version: 1.0.0
---

<<# System Instructions>>

if model == "gpt5":
    [[ chatgpt5/system.mg ]]
else:
    [[ claude/system.mg" ]]

<<## Core Responsibilities>>

if model == "gpt5":
    [[ chatgpt5/responsibilities.mg ]]
else:
    [[ claude/responsibilities.mg" ]]


<<## Available Tools>>

if model == "gpt5":
    [[ "chatgpt5/tools.mg" ]]
else:
    [[ claude/tools.mg ]]

<<## Response Format>>

if model == "gpt5":
    [[ chatgpt5/response_format.mg ]]
else:
    [[ claude/response_format.mg ]]


