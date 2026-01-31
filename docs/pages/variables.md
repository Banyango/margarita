# Variables

You can use variables in your templates to insert dynamic content based on the provided context.

`Syntax ${var_name}`

var_name will need to correspond to a key in the context JSON provided during rendering or a variable that
was passed in from an [include statement](includes.md).

```margarita
You are a AI Farming assistant who has ${count} Tractors.
```
