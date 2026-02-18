# AGENTS.md


## Testing

- **Unit tests**: `test/unit/` - Component-level tests
- **Evals**: `test/evals/` - End-to-end `.mgx` file evaluations

Unit tests should be in the same test directory as the code they test, following the structure of `src/`.

### Test Case Naming

tests should follow the pattern `test_[method]_should_[expected_behavior]_when_[condition]`:

```python
def test_handle_should_store_result_in_state_when_func_effect_is_called():
    ...
```

### Test Style

We should prefer to not use pytest Classes. Keep the tests as simple functions.

Do not use fixtures for shared setup if needed, prefer a properly typed `_create_[data]` helper function instead.

Use `@pytest.mark.asyncio` for async tests.

Tests should follow the Arrange-Act-Assert pattern:

```python
def test_example():
    # Arrange: Set up test data and mocks
    input_data = ...
    expected_result = ...
    mock_dependency = Mock(...)

    # Act: Call the function/method being tested
    result = function_under_test(input_data, dependency=mock_dependency)

    # Assert: Verify the result is as expected
    assert result == expected_result
    mock_dependency.assert_called_once_with(...)
```

## Key Design Decisions

1. **Plugin-based extensibility**: New `@effect` commands can be added by implementing `AgentPlugin`
2. **Stateful execution**: `ExecutionModel` persists across turns, enabling multi-step workflows
3. **Context control**: Explicit `context clear` and `tools clear` prevent context explosion
4. **Local function execution**: Python functions run locally, only results go to LLM
5. **Tool injection**: LLM has `get_variable` and `set_variable` tools for state access

