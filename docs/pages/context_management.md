# Context Management

Keep the context small by using `@effect context clear` to reset it between runs.

### Example

This example:

1. Gets 50 books and summarizes them, storing the summary in a state variable.
2. Clears the context.
3. Gets 50 more books and summarizes them.
4. Contrasts the new summary with the previous one from state.

```mgx
// file: context_management_example.mgx

@state summary = ""

<<
You are a helpful assistant.

I've loaded 50 books into your context so your context is quite large now.

Give a summary of the books.

Store the summary in a variable called "summary" for later use.
>>

@effect run

// Use @effect context clear to reset the context while retaining state variables.
@effect context clear

// All state variables are retained
<<
Load 50 more books and summarize.

Contrast with Previous Summary: ${summary}
>>

@effect run
```
