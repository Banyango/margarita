# Logging

Margarita supports logging output while scripts are running. This is useful for debugging and monitoring progress.

Use the `@effect log` node to log a message:

```mgx
@effect log "This is a log message."
```

Output:
```
[INFO]: This is a log message.
```

You can also include variables in log messages using `${var}` interpolation:

```mgx
@state count = 0

@effect log "The current count is ${count}."
```

Output:
```
[INFO]: The current count is 0.
```
