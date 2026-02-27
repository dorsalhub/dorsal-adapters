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

from dorsal_adapters.arxiv.ris_adapter import to_ris, from_ris


@pytest.fixture
def valid_arxiv_record():
    return {
        "arxiv_id": "2405.06604v1",
        "title": "A Great Paper on Something",
        "authors": ["Alice Smith", "Bob Jones"],
        "categories": ["cs.AI", "cs.LG"],
        "doi": "10.1234/5678",
        "url": "https://arxiv.org/abs/2405.06604",
        "abstract": "This is a great abstract.",
    }


def test_to_ris_full_record(valid_arxiv_record):
    """Ensure standard egress formats all tags correctly."""
    ris = to_ris(valid_arxiv_record, validate=False)

    assert "TY  - PREP" in ris
    assert "T1  - A Great Paper on Something" in ris
    assert "AU  - Alice Smith" in ris
    assert "AU  - Bob Jones" in ris
    assert "AB  - This is a great abstract." in ris
    assert "PY  - 2024" in ris
    assert "KW  - cs.AI" in ris
    assert "KW  - cs.LG" in ris
    assert "DO  - 10.1234/5678" in ris
    assert "UR  - https://arxiv.org/abs/2405.06604" in ris
    assert "M3  - 2405.06604v1" in ris
    assert "ER  - " in ris


def test_to_ris_minimal_record():
    """Ensure egress handles missing optional fields without raising exceptions."""
    record = {"arxiv_id": "math/0504001"}
    ris = to_ris(record, validate=False)

    assert "TY  - PREP" in ris
    assert "PY  - 2005" in ris
    assert "M3  - math/0504001" in ris
    assert "ER  - " in ris
    assert "T1  -" not in ris
    assert "AU  -" not in ris


def test_to_ris_validation_failure():
    """Ensure strict validation catches invalid types during egress."""
    invalid_record = {
        "arxiv_id": "1234.5678",
        "title": "Bad Categories",
        "abstract": "...",
        "authors": ["Me"],
        "categories": "not-an-array",
    }
    with pytest.raises(JsonSchemaValidationError):
        to_ris(invalid_record, validate=True)


def test_from_ris_full_document():
    """Ensure ingress strictly parses line-by-line RIS tags back to a dictionary."""
    ris_input = """TY  - PREP
T1  - A Great Paper on Something
AU  - Alice Smith
AU  - Bob Jones
AB  - This is a great abstract.
PY  - 2024
KW  - cs.AI
KW  - cs.LG
DO  - 10.1234/5678
UR  - https://arxiv.org/abs/2405.06604
M3  - 2405.06604v1
ER  - 
"""
    record = from_ris(ris_input, validate=False)

    assert record["arxiv_id"] == "2405.06604v1"
    assert record["doi"] == "10.1234/5678"
    assert record["categories"] == ["cs.AI", "cs.LG"]
    assert record["title"] == "A Great Paper on Something"
    assert record["authors"] == ["Alice Smith", "Bob Jones"]
    assert record["abstract"] == "This is a great abstract."


def test_from_ris_empty():
    """Ensure ingress fails gracefully on empty content."""
    with pytest.raises(ValueError, match="empty"):
        from_ris("   \n  ", validate=False)


def test_from_ris_validation_failure():
    """Ensure missing required fields throw schema validation errors on ingress."""
    ris_input = """TY  - PREP
M3  - 2405.06604v1
T1  - Title only
AU  - Bob
ER  - 
"""
    with pytest.raises(JsonSchemaValidationError):
        from_ris(ris_input, validate=True)


def test_from_ris_ignores_malformed_lines():
    """Ensure the parser safely skips lines that do not match the strict RIS format."""
    ris_input = """TY  - PREP
T1  - Title
Just some random text
M3- Bad Spacing
AU  - Valid Author
ER  - 
"""
    record = from_ris(ris_input, validate=False)
    assert record["title"] == "Title"
    assert record["authors"] == ["Valid Author"]
    assert "arxiv_id" not in record
