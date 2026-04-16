# Function Calls

Execute Python functions and save their results to state using `@effect func`. This avoids consuming LLM tokens for tool calls and lets you invoke deterministic logic directly instead of relying on the model to select the correct tool.

> Note: The Python module must be available in the activated Python environment and the import path must be correct.

```mgx
from my_module import compute

@effect func compute(x) => result
```

The example above calls `compute(x)` and stores its return value in the `result` state variable. You can reference this value in subsequent prompts using `${result}`.
