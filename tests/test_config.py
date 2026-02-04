import pytest
from pydantic import ValidationError

from trading_mcp.config import Settings


def test_settings_validation_error_includes_field():
    with pytest.raises(ValidationError) as exc:
        Settings(environment="dev", data_dir="/tmp")

    assert "default_symbol" in str(exc.value)
