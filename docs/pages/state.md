# State

Margarita supports storing and accessing state during a run.

```mgx
@state count = 0

<< What is the count variable? >>

@effect run
```

The example above defines a state variable named `count`.

To read a value from state, instruct the agent to "use the `count` variable" or "get count from shared state"; the system will return the current value.

> Note that language models can be nondeterministic, so the agent may not always call the state tool.

You can also instruct the agent to set or update state values. For example, asking it to "set count to 5" or "update count to 10" will update the `count` variable in state (again, the agent may not always call the tool due to model nondeterminism).

```mgx
@state count = 0

<< Set the count variable to 5 >>

@effect run
```

The example above sets the `count` variable to 5.
