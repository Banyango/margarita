# Sub Runs

You can execute other .mgx files from within the agent by using the `@effect exec` directive. This allows you to break down complex tasks into smaller, modular templates.


# Example

```mgx
@effect exec gather_requirements.mgx => requirements

<< Create a PRD that meets the following requirements:
${requirements}
>>
@effect run
```

This will Run the `gather_requirements.mgx` template and grab the variable `requirements` from it's context, which can then be used in the main template to create a PRD (Product Requirements Document) that meets the specified requirements.

Any variable that's set in the sub-run's context can be returned to the main run by using the `=> variable_name` syntax after the `@effect exec` directive. You can return as many variables as you want from the sub-run by separating them with commas, like this: `@effect exec gather_requirements.mgx => requirements, sources, deadline`.

# Permission and Input

Permission and input dialogs are supported in sub-runs. If a sub-run contains a permission or input dialog, the agent will execute the sub-run until it reaches the dialog, then return control to the main run to handle the dialog before resuming the sub-run.

Note that the colour of the dialog will match the colour of the sub run that triggerd it.
