# Stopping the Agent

Sometimes you might get into a state where you want the agent to cease exeuction of the script.

To stop the agent from running, you can use the `@effect stop` directive in your `.mgx` template.

This will immediately halt the agent's execution when it encounters this directive.

# Example

```mgx
@state count = 0

for i in range(10):
    << Increment the count variable >>
    @effect run

if count >= 5:
    @effect stop
```

In this example, the agent will increment the `count` variable up to 10, but if it reaches a count of 5 or more,
it will execute the `@effect stop` directive, which will halt any further execution of the agent.
