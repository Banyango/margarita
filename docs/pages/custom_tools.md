# Custom Tools

Register Python functions as LLM-callable tools with `@effect tools`.

```mgx
from math import add

<< Add 3 and 5 >>

@effect tools add(x: int, y: int) => result

@effect run
```

This registers the `add` function as a tool the LLM can call during the run.

Standard prompt engineering techniques can be used to encourage the LLM to call the tool with the correct arguments.

> **Note:** The LLM may not always call the tool, so design your prompts in a way that encourages tool use when appropriate.
