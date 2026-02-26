# Copyright 2026 Dorsal Hub LTD
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from unittest.mock import patch

from dorsal_adapters.common.validation import validate_record


def test_validate_record_missing_dorsalhub():
    """Ensure an ImportError with installation instructions is raised if dorsalhub is missing."""

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
        validate_record(valid_audio_record, schema_id="audio-transcription", version="0.4.0")
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")
