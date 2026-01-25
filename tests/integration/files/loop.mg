---
task: list-generation
description: Generate a formatted list
---
<<

# Items List

>>
for item in items:
    <<
    - Item: ${item}
    >>

<<

# Summary
Total items listed above.

>>
