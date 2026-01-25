@task: multi-model-agent
@version: 1.0.0

# System Instructions

{% if model == "gpt5" %}
{% include "chatgpt5/system.mg" %}
{% else %}
{% include "claude/system.mg" %}
{% endif %}

## Core Responsibilities

{% if model == "gpt5" %}
{% include "chatgpt5/responsibilities.mg" %}
{% else %}
{% include "claude/responsibilities.mg" %}
{% endif %}

## Available Tools

{% if model == "gpt5" %}
{% include "chatgpt5/tools.mg" %}
{% else %}
{% include "claude/tools.mg" %}
{% endif %}

## Response Format

{% if model == "gpt5" %}
{% include "chatgpt5/response_format.mg" %}
{% else %}
{% include "claude/response_format.mg" %}
{% endif %}

