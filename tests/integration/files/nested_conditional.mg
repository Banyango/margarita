if is_authenticated:
    <<
    Welcome back
    >>
    if is_admin:
        <<
        You have administrative privileges.
        >>
    else:
        <<
        You are a regular user.
        >>

