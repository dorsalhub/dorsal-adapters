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
import subprocess

from jsonschema_rs import ValidationError as JsonSchemaValidationError
from hocr_tools_lib.tools.hocr_check import Checker
from dorsal_adapters.document.hocr_adapter import from_hocr, to_hocr


def test_to_hocr_conversion(valid_document_record_1):
    """Test standard egress from Open Schema to hOCR HTML."""
    result = to_hocr(valid_document_record_1, validate=False)

    assert "<!DOCTYPE html>" in result
    assert '<meta name="ocr-system"' in result
    assert '<meta name="ocr-capabilities" content="ocr_page ocr_carea ocr_par ocr_line ocrx_word"/>' in result

    assert '<div class="ocr_page" id="page_1"' in result
    assert 'title="bbox 0 0 1000 1000"' in result

    assert ">Annual Report Summary</span>" in result

    assert 'title="bbox 50 120 300 520"' in result
    assert ">The first column of text begins here" in result

    assert 'title="bbox 100 100 500 250"' in result
    assert 'data-polygon="[{' in result
    assert ">This caption is wrapped around a circular diagram" in result


def test_to_hocr_page_dimensions(valid_document_record_2):
    """Ensure page width and height are correctly extracted from the schema."""
    result = to_hocr(valid_document_record_2, validate=False)

    assert '<div class="ocr_page" id="page_1" title="bbox 0 0 850 1100">' in result

    assert '<div class="ocr_page" id="page_2" title="bbox 0 0 1100 1100">' in result

    assert 'data-multi-polygon="[[' in result


def test_to_hocr_with_score_and_custom_classes():
    """Ensure scores are mapped to x_wconf and custom hOCR classes are respected."""
    record = {
        "extraction_type": "mixed",
        "blocks": [
            {
                "block_type": "text",
                "text": "Hello",
                "score": 0.857,
                "box": {"x": 10, "y": 10, "width": 50, "height": 10},
                "attributes": {"hocr_class": "ocrx_word", "custom_tag": "test_value"},
            },
            {"block_type": "text", "text": "Paragraph", "attributes": {"hocr_class": "ocr_par"}},
        ],
    }
    result = to_hocr(record, validate=False)

    assert '<span class="ocrx_word"' in result
    assert 'title="bbox 10 10 60 20; x_wconf 85"' in result
    assert 'data-custom_tag="test_value"' in result

    assert '<div class="ocr_par">Paragraph</div>' in result


def test_to_hocr_empty():
    """Ensure egress fails gracefully if 'blocks' are missing."""
    with pytest.raises(ValueError, match="contains no 'blocks'"):
        to_hocr({"extraction_type": "boxes"}, validate=False)


def test_validation_failure_on_invalid_data(invalid_document_bad_norm):
    """Verify that validation correctly catches schema violations."""
    with pytest.raises(JsonSchemaValidationError):
        to_hocr(invalid_document_bad_norm, validate=True)


def test_hocr_standard_compliance_with_hocr_tools_api(valid_document_record_1, tmp_path, capsys):
    """
    Uses the native Python API of `hocr-tools-lib` to rigorously validate
    that our egress adapter produces strictly compliant hOCR HTML.
    """

    hocr_output = to_hocr(valid_document_record_1, validate=False)

    test_file = tmp_path / "strict_validation_output.html"
    test_file.write_text(hocr_output, encoding="utf-8")

    checker = Checker(hocr_file=str(test_file), no_overlap=True)
    checker.check()

    captured = capsys.readouterr()

    if "not ok " in captured.err:
        pytest.fail(f"hOCR strict validation failed natively!\nSTDERR Output:\n{captured.err}")


def test_to_hocr_complex_attributes():
    """Ensure complex attributes (lists/dicts) are safely JSON serialized into data-* attributes."""
    record = {
        "extraction_type": "text",
        "blocks": [
            {
                "block_type": "text",
                "page_number": 1,
                "text": "Serialization Test",
                "attributes": {
                    "simple_string": "hello",
                    "complex_list": [1, 2, 3],
                    "complex_dict": {"nested": "value"},
                },
            }
        ],
    }
    result = to_hocr(record, validate=False)

    assert 'data-simple_string="hello"' in result

    assert 'data-complex_list="[1, 2, 3]"' in result
    assert 'data-complex_dict="{&quot;nested&quot;: &quot;value&quot;}"' in result


def test_from_hocr_basic_conversion():
    """Test standard ingress of hOCR HTML to a Dorsal Open Schema record."""
    hocr_input = """
    <div class="ocr_page" id="page_1" title="bbox 0 0 1000 1000">
        <span class="ocr_line" id="line_1" title="bbox 10 20 110 70; x_wconf 95">Hello   World</span>
    </div>
    """
    record = from_hocr(hocr_input, producer="test-runner", validate=False)

    assert record["producer"] == "test-runner"
    assert record["unit"] == "px"
    assert record["page_width"] == [{"value": 1000, "pages": [1]}]
    assert record["page_height"] == [{"value": 1000, "pages": [1]}]

    blocks = record["blocks"]
    assert len(blocks) == 1

    b = blocks[0]
    assert b["text"] == "Hello World"
    assert b["id"] == "line_1"
    assert b["page_number"] == 1
    assert b["score"] == 0.95
    assert b["box"] == {"x": 10.0, "y": 20.0, "width": 100.0, "height": 50.0}
    assert b["attributes"]["hocr_class"] == "ocr_line"


def test_from_hocr_hierarchical_bubbling():
    """Ensure that nested words properly bubble their text up to the target class (e.g., ocr_line)."""
    hocr_input = """
    <div class="ocr_page" id="page_1">
        <div class="ocr_par">
            <span class="ocr_line">
                <span class="ocrx_word">First</span>
                <span class="ocrx_word">Second</span>
            </span>
        </div>
    </div>
    """

    record = from_hocr(hocr_input, validate=False)
    assert len(record["blocks"]) == 1
    assert record["blocks"][0]["text"] == "First Second"
    assert record["blocks"][0]["attributes"]["hocr_class"] == "ocr_line"

    record_words = from_hocr(hocr_input, target_class="ocrx_word", validate=False)
    assert len(record_words["blocks"]) == 2
    assert record_words["blocks"][0]["text"] == "First"
    assert record_words["blocks"][1]["text"] == "Second"


def test_from_hocr_attribute_deserialization():
    """Ensure data-* attributes are converted back to dicts/lists, and handle bad JSON safely."""
    hocr_input = """
    <div class="ocr_page" id="page_1">
        <span class="ocr_line" 
            data-custom_dict="{&quot;a&quot;: 1}" 
            data-custom_list="[1, 2]" 
            data-bad_json="[1, 2" 
            data-simple_string="just a string">Text</span>
    </div>
    """
    record = from_hocr(hocr_input, validate=False)
    attrs = record["blocks"][0]["attributes"]

    assert attrs["custom_dict"] == {"a": 1}
    assert attrs["custom_list"] == [1, 2]
    assert attrs["bad_json"] == "[1, 2"
    assert attrs["simple_string"] == "just a string"


def test_from_hocr_polygon_deserialization():
    """Ensure polygons are restored correctly, and bad polygons are safely ignored."""
    hocr_input = """
    <div class="ocr_page" id="page_1">
        <span class="ocr_line" data-polygon="[{&quot;x&quot;:10, &quot;y&quot;:10}]">Good Poly</span>
        <span class="ocr_line" data-multi-polygon="[[{&quot;x&quot;:10, &quot;y&quot;:10}]]">Good Multi</span>
        <span class="ocr_line" data-polygon="bad_json">Bad Poly</span>
        <span class="ocr_line" data-multi-polygon="bad_json">Bad Multi</span>
    </div>
    """
    record = from_hocr(hocr_input, validate=False)
    blocks = record["blocks"]

    assert blocks[0]["polygon"] == [{"x": 10, "y": 10}]
    assert blocks[1]["multi_polygon"] == [[{"x": 10, "y": 10}]]

    assert "polygon" not in blocks[2]
    assert "multi_polygon" not in blocks[3]


def test_from_hocr_title_parsing_edge_cases():
    """Hit the ValueError try/excepts for malformed titles."""
    hocr_input = """
    <div class="ocr_page" id="page_1">
        <span class="ocr_line" title="bbox a b c d; x_wconf bad; something else">Bad Floats</span>
        <span class="ocr_line" title="bbox 1 2 3">Missing coordinates</span>
        <span class="ocr_line" title=" ; ; ; ">Empty props</span>
    </div>
    """
    record = from_hocr(hocr_input, validate=False)
    blocks = record["blocks"]

    assert blocks[0]["text"] == "Bad Floats"
    assert "box" not in blocks[0]
    assert "score" not in blocks[0]

    assert blocks[1]["text"] == "Missing coordinates"
    assert "box" not in blocks[1]


def test_from_hocr_empty_content():
    """Ensure ingress fails gracefully on empty text."""
    with pytest.raises(ValueError, match="Provided hOCR content is empty"):
        from_hocr("   \n  ", validate=False)


def test_from_hocr_roundtrip_validation(valid_document_record_1):
    """
    End-to-End integration test:
    Convert Open Schema to hOCR, then hOCR back to Open Schema, and ensure it validates!
    """
    hocr_html = to_hocr(valid_document_record_1, validate=False)
    try:
        roundtrip_record = from_hocr(hocr_html, validate=True)
        assert roundtrip_record["extraction_type"] == "mixed"
        assert len(roundtrip_record["blocks"]) > 0
    except Exception as e:
        pytest.fail(f"Roundtrip validation failed: {e}")


def test_from_hocr_orphaned_end_tags():
    """Hit the empty stack return in handle_endtag to ensure malformed HTML is handled safely."""

    hocr_input = "</div></span><div class='ocr_page'><span class='ocr_line'>Saved it!</span></div>"

    record = from_hocr(hocr_input, validate=False)

    assert len(record["blocks"]) == 1
    assert record["blocks"][0]["text"] == "Saved it!"
