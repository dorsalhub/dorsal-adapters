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
from dorsal_adapters.document.txt_adapter import from_txt, to_txt

VALID_TXT = "This is a simple text document.\n\nIt has two paragraphs."


def test_to_txt_conversion(valid_document_record_1):
    """Test standard egress from Open Schema to plain text."""
    result = to_txt(valid_document_record_1, validate=False)
    assert "--- Page 2 ---" in result
    assert "Annual Report Summary" in result
    assert "The first column of text begins here" in result


def test_from_txt_conversion():
    """Test standard ingress from text string to Open Schema record."""
    record = from_txt(VALID_TXT, producer="test-runner", validate=False)
    assert record["producer"] == "test-runner"
    assert record["extraction_type"] == "text"
    assert len(record["blocks"]) == 1
    assert record["blocks"][0]["text"] == VALID_TXT


def test_to_txt_empty():
    """Ensure egress fails gracefully if 'blocks' are missing."""
    with pytest.raises(ValueError, match="contains no 'blocks'"):
        to_txt({"extraction_type": "text"}, validate=False)


def test_from_txt_empty():
    """Ensure ingress fails gracefully on empty text."""
    with pytest.raises(ValueError, match="Provided text content is empty"):
        from_txt("   \n  ", validate=False)


def test_validation_success_with_defaults(valid_document_record_1):
    """Verify that auto-validation passes with a valid record and string."""
    try:
        from_txt(VALID_TXT, validate=True)
        to_txt(valid_document_record_1, validate=True)
    except Exception as e:
        pytest.fail(f"Validation failed unexpectedly: {e}")


def test_validation_failure_on_invalid_data(invalid_document_bad_norm):
    """Verify that validation correctly catches schema violations."""
    with pytest.raises(JsonSchemaValidationError):
        to_txt(invalid_document_bad_norm, validate=True)
