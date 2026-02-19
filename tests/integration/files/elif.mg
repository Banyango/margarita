---
task: elif-example
---

if status == "premium":
    << Premium user >>
elif status == "standard":
    << Standard user >>
elif status == "trial":
    << Trial user >>
else:
    << Unknown status >>
