import pytest
from unittest.mock import patch

from dorsal_adapters.common.validation import validate_record


def test_validate_record_missing_dorsalhub():
    """Ensure an ImportError with installation instructions is raised if dorsalhub is missing."""

    # Temporarily map the dorsal module to None to force an ImportError on import
    with patch.dict("sys.modules", {"dorsal.file.validators.open_schema": None}):
        with pytest.raises(ImportError, match="For auto-validation please pip install 'dorsalhub'."):
            validate_record({"dummy": "data"}, schema_id="audio-transcription")


def test_validate_record_success(valid_audio_record):
    """Ensure validate_record succeeds natively when dorsalhub is present and data is valid."""
    try:
        validate_record(valid_audio_record, schema_id="audio-transcription")
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")


def test_validate_record_with_version(valid_audio_record):
    """Ensure validate_record handles the version argument correctly."""
    try:
        # 0.4.0 is the current version assumed by our test data
        validate_record(valid_audio_record, schema_id="audio-transcription", version="0.4.0")
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")
