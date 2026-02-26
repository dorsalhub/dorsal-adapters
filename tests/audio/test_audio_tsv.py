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
from jsonschema_rs import ValidationError as JsonSchemaValidationError
from dorsal_adapters.audio.tsv_adapter import from_tsv, to_tsv


VALID_TSV = """start_time\tend_time\ttext
0.500\t4.750\tWelcome back! Today, my guest is the renowned chef, Jean-Pierre.
5.100\t8.250\tThank you, it's a pleasure. You know, the secret is simple,
8.250\t10.900\tc'est une question de respect pour le produit.
11.000\t11.800\t[laughter]
12.000\t14.500\tIt's all about respecting the product.
"""


def test_to_tsv_conversion(valid_audio_record):
    """Test standard egress from Open Schema to TSV string."""
    result = to_tsv(valid_audio_record, validate=False)

    assert "start_time\tend_time\ttext" in result
    assert "0.500\t4.750\tWelcome back!" in result
    assert "12.000\t14.500\tIt's all about respecting the product." in result
    assert "Maria" not in result


def test_to_tsv_with_speakers(valid_audio_record):
    """Test egress correctly includes the speaker column when requested."""
    result = to_tsv(valid_audio_record, validate=False, include_speakers=True)

    assert "start_time\tend_time\ttext\tspeaker" in result
    assert "0.500\t4.750\tWelcome back! Today, my guest is the renowned chef, Jean-Pierre.\tMaria" in result


def test_from_tsv_conversion():
    """Test standard ingress from TSV string to Open Schema record."""
    record = from_tsv(VALID_TSV, producer="test-runner", validate=False)

    assert record["producer"] == "test-runner"
    assert len(record["segments"]) == 5
    assert record["segments"][0]["start_time"] == 0.5
    assert record["segments"][0]["end_time"] == 4.75
    assert "Welcome back!" in record["segments"][0]["text"]


def test_from_tsv_with_speakers():
    """Test ingress correctly parses a TSV that contains speaker data."""
    tsv_with_speaker = "start_time\tend_time\ttext\tspeaker\n0.5\t4.75\tWelcome back!\tMaria\n"
    record = from_tsv(tsv_with_speaker, validate=False)

    assert record["segments"][0]["speaker"]["name"] == "Maria"
    assert record["segments"][0]["speaker"]["id"] == "Maria"


def test_to_tsv_missing_segments(invalid_audio_record_2):
    """Ensure egress fails gracefully if the record is missing segments."""
    with pytest.raises(ValueError, match="does not contain any 'segments'"):
        to_tsv(invalid_audio_record_2, validate=False)


def test_from_tsv_empty():
    """Ensure ingress fails gracefully on an empty TSV string."""
    with pytest.raises(ValueError, match="content is empty"):
        from_tsv("   \n  ", validate=False)


def test_from_tsv_missing_columns():
    """Ensure ingress fails if required TSV columns are missing."""
    with pytest.raises(ValueError, match="must contain at least 'start_time' and 'text' columns"):
        from_tsv("end_time\tspeaker\n2.5\tBob\n", validate=False)


def test_validation_success_with_defaults(valid_audio_record):
    """Verify that auto-validation passes with valid data."""
    try:
        from_tsv(VALID_TSV, validate=True)
        to_tsv(valid_audio_record, validate=True)
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")


def test_validation_failure_on_invalid_data(invalid_audio_record_1):
    """Verify that validation correctly catches schema violations."""
    with pytest.raises(JsonSchemaValidationError):
        to_tsv(invalid_audio_record_1, validate=True)
