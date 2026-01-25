---
task: conditional-example
---

<<# Greeting>>

if is_authenticated:
    <<
    Welcome back, ${username}!

    Your account status: ${status}
    >>
else:
    << Please sign in to continue. >>

<< # Footer
Thank you for using our service.
>>
