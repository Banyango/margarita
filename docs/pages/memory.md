# Memory

Margarita supports using memory to persist information to JSON across runs.

Memory variables are stored in a `memory.json` file at the end of a run and loaded back at the beginning of the next run, making them available in the context and in `@effect func` calls.

Use the `@memory var` node to create a memory variable:

```mgx
@memory var favorite_color

<<
If favorite_color is not set, set it to "blue".
Otherwise write a log message saying "The user's favorite color is favorite_color".
>>

@effect run
```

## Immediate effects

These operations on memory variables execute immediately when the agent encounters them in the script, rather than being deferred until `@effect run`.

### Deleting a memory variable

```mgx
@memory delete favorite_color
```

### Clearing all memory

```mgx
@memory clear
```
