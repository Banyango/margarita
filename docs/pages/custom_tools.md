# Custom Tools

Register Python functions as LLM-callable tools with `@effect tools`.

```mgx
from math import add, AddParams

<< Add 3 and 5 >>

@effect tools add(x: AddParams) => result

@effect run
```

This registers the `add` function as a tool the LLM can call during the run.

Standard prompt engineering techniques can be used to encourage the LLM to call the tool with the correct arguments.

> **Note:** The params must be a valid pydantic model.
