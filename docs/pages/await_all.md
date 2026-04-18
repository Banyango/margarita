# Await All

.mgx files contain an @await_all directive that allows you to await multiple `exec` runs in parallel and use their results together in the template.


# Example

```mgx
@await-all
    @effect exec gather_requirements.mgx => requirements
    @effect exec gather_standards.mgx => standards

<<
Create a PRD that meets the following requirements:
${requirements}
and adheres to the following standards:
${standards}
>>

@effect run
```

In this example, the `@await_all` directive allows the agent to execute both `gather_requirements.mgx` and `gather_standards.mgx` in parallel. The results of these executions are stored in the `requirements` and `standards` variables, which can then be used together in the template to create a PRD (Product Requirements Document) that meets the specified requirements and standards.



