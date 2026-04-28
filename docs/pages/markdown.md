# Markdown

Anything between `<<` and `>>` gets sent to the agent.
This content can include any valid Markdown syntax, such as headings, lists, links, images, etc.

Each time the agent encounters a `<< >>` block, it will add the content to the context and send it to the model.

```shell
<<
# This is a heading

Body text

- This is a list item
[This is a link](https://www.example.com)

>>
```
