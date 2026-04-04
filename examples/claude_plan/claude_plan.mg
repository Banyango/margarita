---
name: claude-plan
version: 1.0.0
description: Describes an implementation plan for Claude Code to execute
---

<<# Plan: ${title}>>

<<## Goal>>

<<${goal}>>

if context:
    <<## Background>>

    <<${context}>>

<<## Steps>>

for step in steps:
    <<### ${step.number}. ${step.title}>>

    <<${step.description}>>

    if step.files:
        <<**Files:** ${step.files}>>

if constraints:
    <<## Constraints>>

    <<${constraints}>>

if acceptance_criteria:
    <<## Acceptance Criteria>>

    <<${acceptance_criteria}>>
