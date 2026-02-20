import io
import pytest
from dorsal_adapters.registry import Adapter, get_adapter, list_formats


# --- Mock Functions for the Adapter Class ---
def dummy_export(record: dict, **kwargs) -> str:
    return f"exported: {record.get('key')} extra={kwargs.get('extra')}"


def dummy_parse(content: str, **kwargs) -> dict:
    return {"parsed": content, "extra": kwargs.get("extra")}


@pytest.fixture
def dummy_adapter() -> Adapter:
    """Provides a basic Adapter instance for testing class methods natively."""
    return Adapter(
        schema_id="test/schema",
        format_name="test-fmt",
        description="A test adapter",
        export_fn=dummy_export,
        parse_fn=dummy_parse,
    )


# --- Adapter Class Tests ---
def test_adapter_export_dict(dummy_adapter):
    """Test exporting natively with a Python dictionary."""
    result = dummy_adapter.export({"key": "value"}, extra="yes")
    assert result == "exported: value extra=yes"


def test_adapter_export_json_str(dummy_adapter):
    """Test the smart export wrapper successfully parses a JSON string."""
    result = dummy_adapter.export('{"key": "json_str"}')
    assert result == "exported: json_str extra=None"


def test_adapter_export_json_bytes(dummy_adapter):
    """Test the smart export wrapper successfully parses JSON bytes."""
    result = dummy_adapter.export(b'{"key": "json_bytes"}')
    assert result == "exported: json_bytes extra=None"


def test_adapter_export_invalid_json(dummy_adapter):
    """Ensure invalid JSON strings raise a clean ValueError."""
    with pytest.raises(ValueError, match="Failed to decode stringified JSON record"):
        dummy_adapter.export('{"key": broken')


def test_adapter_export_invalid_type(dummy_adapter):
    """Ensure passing something other than a dict, string, or bytes raises a TypeError."""
    with pytest.raises(TypeError, match="Record must be a dictionary or a JSON string"):
        dummy_adapter.export(["not", "a", "dict"])


def test_adapter_parse(dummy_adapter):
    """Test the standard parse wrapper."""
    result = dummy_adapter.parse("raw content", extra="yes")
    assert result == {"parsed": "raw content", "extra": "yes"}


def test_adapter_export_file(dummy_adapter):
    """Test writing export results directly to a file-like object."""
    fp = io.StringIO()
    dummy_adapter.export_file({"key": "file_val"}, fp, extra="yes")
    assert fp.getvalue() == "exported: file_val extra=yes"


def test_adapter_parse_file(dummy_adapter):
    """Test reading directly from a file-like object into the parser."""
    fp = io.StringIO("file content")
    result = dummy_adapter.parse_file(fp, extra="yes")
    assert result == {"parsed": "file content", "extra": "yes"}


def test_adapter_repr(dummy_adapter):
    """Test the string representation of the Adapter class."""
    assert repr(dummy_adapter) == "Adapter(schema_id='test/schema', format_name='test-fmt')"


# --- Registry Function Tests ---
def test_get_adapter_success():
    """Test successful dynamic loading of a registered adapter."""
    adapter = get_adapter("open/audio-transcription", "srt")
    assert adapter.schema_id == "open/audio-transcription"
    assert adapter.format_name == "srt"
    assert callable(adapter._export_fn)
    assert callable(adapter._parse_fn)


def test_get_adapter_alias():
    """Test that alias mapping correctly resolves 'audio-transcription' to 'open/audio-transcription'."""
    adapter = get_adapter("audio-transcription", "txt")
    assert adapter.schema_id == "open/audio-transcription"
    assert adapter.format_name == "txt"


def test_get_adapter_not_found():
    """Ensure requesting an unregistered adapter raises a clear ValueError."""
    with pytest.raises(ValueError, match="Adapter not found for schema=open/audio-transcription and format=fake"):
        get_adapter("open/audio-transcription", "fake")


def test_list_formats():
    """Test that list_formats returns a sorted tuple of available formats for a valid schema."""
    formats = list_formats("open/audio-transcription")
    assert len(formats) > 0

    # Check that it returns expected tuples of (format_name, description)
    fmt_names = [f[0] for f in formats]
    assert "srt" in fmt_names
    assert "vtt" in fmt_names
    assert "tsv" in fmt_names

    # Verify sorting logic
    assert fmt_names == sorted(fmt_names)


def test_list_formats_not_found():
    """Ensure list_formats returns an empty list for unknown schemas."""
    formats = list_formats("fake/schema")
    assert formats == []
