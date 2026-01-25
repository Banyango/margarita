---
task: nested-structures
---

// This is a comment - testing new comment syntax

<<
# Nested Conditionals and Loops

This shows how to use the new syntax for building marg files.
>>

if show_categories:
    << # Categories >>

    for category in categories:
        << ## Category: ${category} >>

        if show_items:
            << Items in this category: >>
            for item in items:
                << - ${item} >>
        else:
            << No items to display.>>

<< # End >>

