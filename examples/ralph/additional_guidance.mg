---
description: "Additional guidance for custom Ralph, the AI assistant based on feedback."
---

<<
Here are some things to keep in mind:
- There is no SQL involved in the task list, so don't do any SQL queries or database interactions.
- We should not commit to git or do any version control operations as part of the task list.
- don't add any temp files to docs. If you absolutely need to create a temp file do it in the ./temp directory.
- If you get into a scenario where a criterion is not met but the guidance forbids it just set the task to done, but make a note to the user.
- Use `make test` to run tests
>>
