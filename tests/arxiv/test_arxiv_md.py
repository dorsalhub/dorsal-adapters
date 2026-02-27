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

from dorsal_adapters.arxiv.md_adapter import to_md, from_md


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


def test_to_md_full_record(valid_arxiv_record):
    """Ensure standard egress formats frontmatter and markdown body correctly."""
    md = to_md(valid_arxiv_record, validate=False)

    assert "arxiv_id: 2405.06604v1" in md
    assert "year: 2024" in md
    assert "categories: [cs.AI, cs.LG]" in md
    assert "doi: 10.1234/5678" in md
    assert "# A Great Paper on Something" in md
    assert "**Authors:** Alice Smith, Bob Jones" in md
    assert "## Abstract\nThis is a great abstract." in md


def test_to_md_minimal_record():
    """Ensure egress handles missing optional fields without raising exceptions."""
    record = {"arxiv_id": "math/0504001"}
    md = to_md(record, validate=False)

    assert "arxiv_id: math/0504001" in md
    assert "year: 2005" in md
    assert "# " not in md
    assert "**Authors:**" not in md
    assert "## Abstract" not in md


def test_to_md_validation_failure():
    """Ensure strict validation catches invalid types during egress."""
    invalid_record = {
        "arxiv_id": "1234.5678",
        "title": "Bad Categories",
        "abstract": "...",
        "authors": ["Me"],
        "categories": "not-an-array",  # Categories should be an array of strings
    }
    with pytest.raises(JsonSchemaValidationError):
        to_md(invalid_record, validate=True)


def test_from_md_full_document():
    """Ensure ingress regex successfully extracts metadata from standard markdown."""
    md_input = """---
arxiv_id: 2405.06604v1
year: 2024
categories: [cs.AI, cs.LG]
doi: 10.1234/5678
---

# A Great Paper on Something

**Authors:** Alice Smith, Bob Jones

## Abstract
This is a great abstract.
"""
    record = from_md(md_input, validate=False)

    assert record["arxiv_id"] == "2405.06604v1"
    assert record["doi"] == "10.1234/5678"
    assert record["categories"] == ["cs.AI", "cs.LG"]
    assert record["title"] == "A Great Paper on Something"
    assert record["authors"] == ["Alice Smith", "Bob Jones"]
    assert record["abstract"] == "This is a great abstract."


def test_from_md_empty():
    """Ensure ingress fails gracefully on empty content."""
    with pytest.raises(ValueError, match="empty"):
        from_md("   \n  ", validate=False)


def test_from_md_validation_failure():
    """Ensure missing required fields throw schema validation errors on ingress."""
    md_input = """---
arxiv_id: 2405.06604v1
---
# Title only
**Authors:** Bob
"""
    with pytest.raises(JsonSchemaValidationError):
        from_md(md_input, validate=True)
