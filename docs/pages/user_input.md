# User Input

Margarita supports getting user input during a run with the `@effect input` node.

```mgx
@effect input "What is your favorite color?" => favorite_color

// Use the variable in subsequent context or effects
@effect log "The user's favorite color is ${favorite_color}."
```

The agent will prompt the user with the given question and store the response in the specified variable. That variable can then be used in subsequent context blocks or function effects.
