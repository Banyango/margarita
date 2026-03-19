# Claude Skill

The cli provides a method to automatically install a Claude skill.

To install a skill, run the following command:

```bash
uvx margarita install-claude-skill
```

This will install the margarita skill for Claude in the local `.claude` dir. Once installed restart claude.

## Features
- Render margarita templates directly in Claude.
- Create new templates with the help of Claude.

## Using the skill

### Render templates in Claude

You can use the skill to render margarita templates directly in Claude. For example, you can ask:

```
Can you render the template "templates/greeting.mg" with the context {"name": "Alice"}?
```

### Create new templates with Claude
You can also ask Claude to create new templates for you. For example:

```
Can you create a new margarita template for a product description? I want it to include the product name, features, and a call to action.
```

output:

```
// file: product_description.mg
<<
Product Name: ${product_name}
Features:
- ${feature_1}
- ${feature_2}
- ${feature_3}
Call to Action: ${call_to_action}
>>
```
