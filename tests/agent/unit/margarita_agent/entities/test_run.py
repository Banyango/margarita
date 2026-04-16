from margarita.agent.entities.run import TokenUsage


def _create_token_usage(
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> TokenUsage:
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
    )


def test_total_tokens_should_return_sum_when_calculated():
    # Arrange
    usage = _create_token_usage(input_tokens=100, output_tokens=50)

    # Act
    total = usage.total_tokens

    # Assert
    assert total == 150


def test_accumulate_should_add_values_when_called():
    # Arrange
    usage = _create_token_usage(
        input_tokens=10,
        output_tokens=20,
        cache_read_tokens=5,
        cache_write_tokens=3,
    )
    other = _create_token_usage(
        input_tokens=30,
        output_tokens=40,
        cache_read_tokens=15,
        cache_write_tokens=7,
    )

    # Act
    usage.accumulate(other)

    # Assert
    assert usage.input_tokens == 40
    assert usage.output_tokens == 60
    assert usage.cache_read_tokens == 20
    assert usage.cache_write_tokens == 10
