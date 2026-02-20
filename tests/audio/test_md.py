import pytest
from jsonschema_rs import ValidationError as JsonSchemaValidationError
from dorsal_adapters.audio.md import from_md, to_md, _format_time, _parse_time

VALID_MD = """# Transcription

**[00:00 - 00:04]** Welcome back! Today, my guest is the renowned chef, Jean-Pierre.

**[00:05 - 00:08]** Thank you, it's a pleasure. You know, the secret is simple,

**[00:08 - 00:10]** c'est une question de respect pour le produit.

**[00:11 - 00:11]** [laughter]

**[00:12 - 00:14]** It's all about respecting the product.
"""


def test_time_helpers():
    """Test the internal time formatting and parsing utilities."""
    # Test formatting with milliseconds
    assert _format_time(65.123, include_milliseconds=True) == "01:05.123"
    assert _format_time(3665.123, include_milliseconds=True) == "01:01:05.123"

    # Test formatting without milliseconds
    assert _format_time(65.123, include_milliseconds=False) == "01:05"
    assert _format_time(3665.123, include_milliseconds=False) == "01:01:05"

    # Test parsing
    assert _parse_time("01:05.123") == 65.123
    assert _parse_time("01:01:05.123") == 3665.123
    assert _parse_time("65.123") == 65.123


def test_to_md_conversion(valid_audio_record):
    """Test standard egress from Open Schema to Markdown."""
    result = to_md(valid_audio_record, validate=False)

    assert "# Transcription" in result
    assert "**[00:00 - 00:04]** Welcome back!" in result
    assert "**[00:12 - 00:14]** It's all about respecting the product." in result


def test_to_md_no_segments(valid_audio_record):
    """Test egress gracefully handles records with text but no segments."""
    record = valid_audio_record.copy()
    del record["segments"]

    result = to_md(record, validate=False)
    assert "# Transcription" in result
    assert "Welcome back!" in result
    assert "**[" not in result  # Timestamps shouldn't be rendered if segments are missing


def test_to_md_options(valid_audio_record):
    """Test egress configuration flags (timestamps, speakers, ms)."""
    result = to_md(
        valid_audio_record, validate=False, include_timestamps=True, include_milliseconds=True, include_speakers=True
    )
    assert "**[00:00.500 - 00:04.750]** **Maria:** Welcome back!" in result


def test_to_md_no_timestamps_no_speakers(valid_audio_record):
    """Test egress without timestamps or speakers."""
    result = to_md(valid_audio_record, validate=False, include_timestamps=False, include_speakers=False)
    assert "Welcome back!" in result
    assert "**[" not in result
    assert "**Maria:**" not in result


def test_from_md_conversion():
    """Test standard ingress from Markdown string to Open Schema record."""
    record = from_md(VALID_MD, producer="test-runner", validate=False)

    assert record["producer"] == "test-runner"
    assert len(record["segments"]) == 5
    assert record["segments"][0]["start_time"] == 0.0
    assert record["segments"][0]["end_time"] == 4.0
    assert record["segments"][0]["text"] == "Welcome back! Today, my guest is the renowned chef, Jean-Pierre."
    assert "c'est une question de respect pour le produit." in record["text"]


def test_from_md_with_speakers():
    """Test ingress parsing handles speaker names correctly."""
    md_with_speakers = "# Transcription\n\n**[00:00 - 00:05]** **Maria:** Hello!"
    record = from_md(md_with_speakers, validate=False)

    assert record["segments"][0]["speaker"]["name"] == "Maria"
    assert record["segments"][0]["text"] == "Hello!"


def test_from_md_plain_text():
    """Test ingress gracefully handles lines without strict timestamp formatting."""
    md_plain = "# Transcription\n\nJust some random text without timestamps."
    record = from_md(md_plain, validate=False)

    assert record["segments"][0]["start_time"] == 0.0
    assert record["segments"][0]["end_time"] == 0.0
    assert record["segments"][0]["text"] == "Just some random text without timestamps."


def test_to_md_empty(invalid_audio_record_2):
    """Ensure egress fails gracefully if neither text nor segments exist."""
    with pytest.raises(ValueError, match="contains no 'text' or 'segments'"):
        to_md(invalid_audio_record_2, validate=False)


def test_from_md_empty():
    """Ensure ingress fails gracefully on empty text."""
    with pytest.raises(ValueError, match="Provided Markdown content is empty"):
        from_md("   \n  ", validate=False)


def test_validation_success_with_defaults(valid_audio_record):
    """Verify that auto-validation passes with valid data."""
    try:
        from_md(VALID_MD, validate=True)
        to_md(valid_audio_record, validate=True)
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")


def test_validation_failure_on_invalid_data(invalid_audio_record_1):
    """Verify that validation correctly catches schema violations."""
    with pytest.raises(JsonSchemaValidationError):
        to_md(invalid_audio_record_1, validate=True)
