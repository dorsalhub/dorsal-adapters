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

from dorsal_adapters.arxiv.bibtext_adapter import to_bibtex, from_bibtex
from dorsal_adapters.arxiv.helpers import extract_year_from_id


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


def test_extract_year_from_id():
    """Test the regex inferences for publication years from arXiv IDs."""
    # Modern format
    assert extract_year_from_id("2405.06604") == "2024"
    assert extract_year_from_id("2405.06604v2") == "2024"
    assert extract_year_from_id("0704.0001") == "2007"

    # Legacy format (1990s)
    assert extract_year_from_id("solv-int/9304001") == "1993"
    assert extract_year_from_id("hep-th/9912012v2") == "1999"

    # Legacy format (2000s)
    assert extract_year_from_id("math/0504001") == "2005"

    # Invalid / Unrecognized
    assert extract_year_from_id("not-an-id") is None


def test_to_bibtex_full_record(valid_arxiv_record):
    """Test standard egress to a comprehensive BibTeX citation."""
    bib = to_bibtex(valid_arxiv_record)

    assert "@misc{2405_06604v1," in bib
    assert "title = {A Great Paper on Something}," in bib
    assert "author = {Alice Smith and Bob Jones}," in bib
    assert "eprint = {2405.06604v1}," in bib
    assert "archivePrefix = {arXiv}," in bib
    assert "primaryClass = {cs.AI}," in bib
    assert "doi = {10.1234/5678}," in bib
    assert "url = {https://arxiv.org/abs/2405.06604}," in bib
    assert "year = {2024}" in bib  # Checks inference and trailing comma removal


def test_to_bibtex_minimal_record():
    """Ensure egress handles missing optional fields gracefully."""
    record = {"arxiv_id": "math/0504001"}
    bib = to_bibtex(record)

    assert "@misc{math_0504001," in bib
    assert "eprint = {math/0504001}," in bib
    assert "year = {2005}" in bib
    assert "title =" not in bib


def test_from_bibtex_parsing():
    """Test standard ingress regex parsing of BibTeX back to dictionary."""
    bib_input = """
    @misc{2405_06604v1,
      title = {A Great Paper},
      author = {Alice Smith and Bob Jones},
      eprint = {2405.06604v1},
      primaryClass = {cs.AI},
      doi = {10.1234/5678},
      url = {https://arxiv.org/abs/2405.06604}
    }
    """
    record = from_bibtex(bib_input, validate=False)

    assert record["title"] == "A Great Paper"
    assert record["authors"] == ["Alice Smith", "Bob Jones"]
    assert record["arxiv_id"] == "2405.06604v1"
    assert "cs.AI" in record["categories"]
    assert record["doi"] == "10.1234/5678"
    assert record["url"] == "https://arxiv.org/abs/2405.06604"


def test_from_bibtex_empty():
    """Ensure ingress fails gracefully on empty content."""
    with pytest.raises(ValueError, match="empty"):
        from_bibtex("   \n  ", validate=False)


def test_from_bibtex_validation_failure():
    """
    Since BibTeX doesn't store abstracts, parsing it back to dorsal/arxiv
    should fail strict schema validation because 'abstract' is required.
    """
    bib_input = "@misc{key, title={Test Paper}, eprint={1234.5678}, author={John Doe}}"

    with pytest.raises(JsonSchemaValidationError):
        from_bibtex(bib_input, validate=True)
