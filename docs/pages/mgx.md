# MGX

# Overview

.mgx files are a specialized template format used by Lime Agents.

Use them with [Lime](https://github.com/Banyango/lime) to execute workflows using your coding agents.

# Features

- All the features of .mg margarita templates. Such as includes, conditionals, loops, and variable interpolation.
- Adds the ability to import python functions.
- `@effect` give commands to the agent. These can be used to define tools, run the agent, and manage context.

```margaritascript
---
description: "the description of the addition tool"
---
// import python function.
from math import add, subtract, multiply, load_files

// Each markdown block in .mgx files gets evaluated and then loaded into the agent's context.
<<
You are an expert mathematician.
Your task is to solve addition problems accurately and efficiently.

When given a problem, you should:
1. Read the problem carefully.
2. Identify the two numbers to be added.
3. Calculate the sum of the two numbers.
4. Provide the final answer clearly.
>>

// We can load mg files into the context using includes as well
[[ create-a-react-component ]]
[[ create-a-test ]]
[[ validate-test-works ]]

// call the add function with 12 and test.data stored into result
@effect func add(12, test.data) => result

if result != 24:
    <<
    The addition tool did not return the expected result.
    Expected: 24
    Got: ${result}
    >>

@state result = {}

// define a new tool that the agent should use
@effect tool add
@effect tool subtract
@effect tool multiply
@effect tool load_files

// run the agent call
@effect run

// clear the context
@effect context clear

// clear the tool cache
@effect tool clear

// Load new state into the context.
<<
Validate the following:
- The addition tool correctly adds two numbers.
- The subtraction tool correctly subtracts two numbers.
- The multiplication tool correctly multiplies two numbers.
- The load_files function correctly loads and reads files from the specified directory.

Store the result into the variable 'result'.
>>

if result.failed:
    <<
    The test failed. Please review the implementation of the math tools and the
    load_files function for any errors.
    >>


```
