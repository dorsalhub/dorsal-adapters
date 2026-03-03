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

import io
import pytest
from dorsal_adapters.registry import Adapter, get_adapter, list_formats


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
        extension="text",
        export_fn=dummy_export,
        parse_fn=dummy_parse,
    )


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

    fmt_names = [f[0] for f in formats]
    assert "srt" in fmt_names
    assert "vtt" in fmt_names
    assert "tsv" in fmt_names

    assert fmt_names == sorted(fmt_names)


def test_list_formats_not_found():
    """Ensure list_formats returns an empty list for unknown schemas."""
    formats = list_formats("fake/schema")
    assert formats == []


def test_adapter_not_implemented_errors():
    """
    Test that calling export or parse methods on an adapter without 
    defined functions raises NotImplementedError.
    """
    dead_adapter = Adapter(
        schema_id="test/none",
        format_name="none",
        description="No functions",
        extension="txt",
        export_fn=None,
        parse_fn=None,
    )

    with pytest.raises(NotImplementedError, match="Exporting to 'none' is not currently supported"):
        dead_adapter.export({"key": "val"})

    with pytest.raises(NotImplementedError, match="Parsing from 'none' is not currently supported"):
        dead_adapter.parse("some content")

    with pytest.raises(NotImplementedError, match="Exporting to 'none' is not currently supported"):
        dead_adapter.export_file({"key": "val"}, io.StringIO())

    with pytest.raises(NotImplementedError, match="Parsing from 'none' is not currently supported"):
        dead_adapter.parse_file(io.StringIO("content"))


def test_real_world_one_way_adapter():
    """
    Verify NotImplementedError using a real registered adapter 
    that only supports one-way conversion (e.g., BibTeX).
    """
    adapter = get_adapter("dorsal/arxiv", "bibtex")

    assert "@misc" in adapter.export({
        "arxiv_id": "2405.06604",
        "title": "Title",
        "abstract": "Abstract",
        "authors": ["Author"]
    })

    with pytest.raises(NotImplementedError, match="Parsing from 'bibtex' is not currently supported"):
        adapter.parse("@misc{...}")