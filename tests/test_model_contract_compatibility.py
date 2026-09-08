from nexus.models.contracts import (
    ModelProtocolError,
    ModelRequest,
    ModelResponse,
    ModelValidationError,
)
from nexus.models.local_model import (
    LocalModelProtocolError,
    LocalModelRequest,
    LocalModelResponse,
    LocalModelValidationError,
)


def test_local_model_request_is_generic_model_request_alias():
    assert LocalModelRequest is ModelRequest


def test_local_model_response_is_generic_model_response_alias():
    assert LocalModelResponse is ModelResponse


def test_local_model_validation_error_is_generic_alias():
    assert LocalModelValidationError is ModelValidationError


def test_local_model_protocol_error_is_generic_alias():
    assert LocalModelProtocolError is ModelProtocolError
