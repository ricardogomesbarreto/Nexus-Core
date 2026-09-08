from nexus.models.contracts import (
    ModelError,
    ModelProtocolError,
    ModelProviderError,
    ModelProviderTimeoutError,
    ModelProviderUnavailableError,
    ModelValidationError,
)


def test_model_validation_error_belongs_to_model_error_family():
    assert issubclass(
        ModelValidationError,
        ModelError,
    )

    assert issubclass(
        ModelValidationError,
        ValueError,
    )


def test_model_protocol_error_belongs_to_model_error_family():
    assert issubclass(
        ModelProtocolError,
        ModelError,
    )

    assert issubclass(
        ModelProtocolError,
        RuntimeError,
    )


def test_model_provider_error_belongs_to_model_error_family():
    assert issubclass(
        ModelProviderError,
        ModelError,
    )

    assert issubclass(
        ModelProviderError,
        RuntimeError,
    )


def test_provider_unavailable_is_provider_error():
    assert issubclass(
        ModelProviderUnavailableError,
        ModelProviderError,
    )


def test_provider_timeout_is_provider_error():
    assert issubclass(
        ModelProviderTimeoutError,
        ModelProviderError,
    )


def test_provider_timeout_and_unavailable_are_distinct():
    assert (
        ModelProviderTimeoutError
        is not ModelProviderUnavailableError
    )


def test_model_routing_error_belongs_to_model_error_family():
    from nexus.models.router import ModelRoutingError

    assert issubclass(
        ModelRoutingError,
        ModelError,
    )

    assert issubclass(
        ModelRoutingError,
        RuntimeError,
    )


def test_specific_routing_errors_belong_to_routing_family():
    from nexus.models.router import (
        DuplicateModelProviderError,
        InvalidModelProviderError,
        InvalidModelProviderIdError,
        ModelRoutingError,
        UnknownModelProviderError,
    )

    routing_errors = (
        InvalidModelProviderError,
        InvalidModelProviderIdError,
        UnknownModelProviderError,
        DuplicateModelProviderError,
    )

    for error_type in routing_errors:
        assert issubclass(
            error_type,
            ModelRoutingError,
        )

        assert issubclass(
            error_type,
            ModelError,
        )
