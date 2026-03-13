from pathlib import Path

import pytest
from pydantic import ValidationError

from config import Settings


def test_settings_validation_error_includes_field():
    with pytest.raises(ValidationError) as exc:
        Settings(environment="dev", data_dir=Path("/tmp"))

    assert "default_symbol" in str(exc.value)
