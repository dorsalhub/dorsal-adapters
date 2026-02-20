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
import webvtt
from dorsal_adapters.audio.vtt import from_vtt, to_vtt

VALID_VTT = """WEBVTT

00:00:00.500 --> 00:00:04.750
Welcome back! Today, my guest is the renowned chef, Jean-Pierre.

00:00:05.100 --> 00:00:08.250
Thank you, it's a pleasure. You know, the secret is simple,

00:00:08.250 --> 00:00:10.900
c'est une question de respect pour le produit.
"""


def test_to_vtt_conversion(valid_audio_record):
    """Test standard egress from Open Schema to WebVTT string."""
    result = to_vtt(valid_audio_record, validate=False)

    assert "WEBVTT" in result
    assert "00:00:00.500 --> 00:00:04.750" in result
    assert "Welcome back!" in result
    assert "<v" not in result  # Speakers shouldn't be included by default

    # Ensure webvtt-py can parse our output
    assert len(webvtt.from_string(result)) == 5


def test_to_vtt_with_speakers(valid_audio_record):
    """Test egress correctly injects WebVTT speaker tags when requested."""
    result = to_vtt(valid_audio_record, validate=False, include_speakers=True)

    assert "<v Maria>Welcome back!" in result
    assert "<v Jean-Pierre>Thank you," in result


def test_from_vtt_conversion():
    """Test standard ingress from WebVTT string to Open Schema record."""
    record = from_vtt(VALID_VTT, producer="test-runner", validate=False)

    assert record["producer"] == "test-runner"
    assert len(record["segments"]) == 3
    assert record["segments"][0]["start_time"] == 0.5
    assert record["segments"][0]["end_time"] == 4.75
    assert "Welcome back!" in record["segments"][0]["text"]
    assert "c'est une question de respect pour le produit." in record["text"]


def test_from_vtt_strips_speaker_tags():
    """Test that webvtt parsing correctly strips out `<v Speaker>` tags from the raw text."""
    vtt_with_speakers = """WEBVTT

00:00:00.000 --> 00:00:05.000
<v Maria>Hello there!
"""
    record = from_vtt(vtt_with_speakers, validate=False)
    assert record["segments"][0]["text"] == "Hello there!"
    assert "<v Maria>" not in record["segments"][0]["text"]


def test_to_vtt_missing_segments(invalid_audio_record_2):
    """Ensure egress fails gracefully if the record is missing segments."""
    with pytest.raises(ValueError, match="does not contain any 'segments'"):
        to_vtt(invalid_audio_record_2, validate=False)


def test_from_vtt_parse_error():
    """Ensure malformed WebVTT content raises a ValueError."""
    bad_vtt = "This is just a random text file.\n00:00 -> 01:00\nNo WEBVTT header."
    with pytest.raises(ValueError, match="Failed to parse WebVTT content"):
        from_vtt(bad_vtt)


def test_validation_success_with_defaults(valid_audio_record):
    """Verify that auto-validation passes with a valid record and string."""
    try:
        from_vtt(VALID_VTT, validate=True)
        to_vtt(valid_audio_record, validate=True)
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")


def test_validation_failure_on_invalid_data(invalid_audio_record_1):
    """Verify that validation correctly catches schema violations."""
    with pytest.raises(JsonSchemaValidationError):
        to_vtt(invalid_audio_record_1, validate=True)
