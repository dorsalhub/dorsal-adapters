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

import json
import pytest
from jsonschema_rs import ValidationError as JsonSchemaValidationError

from dorsal_adapters.arxiv.csl_json_adapter import to_csl_json, _parse_author_name


@pytest.fixture
def valid_arxiv_record():
    return {
        "arxiv_id": "2405.06604v1",
        "title": "A Great Paper on Something",
        "authors": ["Alice Smith", "Bob Jones", "C. D. Broad", "Prince"],
        "categories": ["cs.AI", "cs.LG"],
        "doi": "10.1234/5678",
        "url": "https://arxiv.org/abs/2405.06604",
        "abstract": "This is a great abstract.",
    }


def test_parse_author_name():
    """Ensure the pragmatic space-split handles standard names, initials, and mononyms."""
    assert _parse_author_name("Alice Smith") == {"given": "Alice", "family": "Smith"}
    assert _parse_author_name("C. D. Broad") == {"given": "C. D.", "family": "Broad"}
    assert _parse_author_name("Prince") == {"family": "Prince"}
    assert _parse_author_name(" ") == {}


def test_to_csl_json_full_record(valid_arxiv_record):
    """Ensure standard egress formats all keys correctly into valid CSL-JSON."""
    csl_str = to_csl_json(valid_arxiv_record)
    csl_data = json.loads(csl_str)

    assert isinstance(csl_data, list)
    item = csl_data[0]

    assert item["id"] == "2405.06604v1"
    assert item["type"] == "article"
    assert item["publisher"] == "arXiv"
    assert item["title"] == "A Great Paper on Something"
    assert item["abstract"] == "This is a great abstract."
    assert item["DOI"] == "10.1234/5678"
    assert item["URL"] == "https://arxiv.org/abs/2405.06604"
    assert item["number"] == "2405.06604v1"

    assert item["author"][0] == {"given": "Alice", "family": "Smith"}
    assert item["author"][1] == {"given": "Bob", "family": "Jones"}
    assert item["author"][2] == {"given": "C. D.", "family": "Broad"}
    assert item["author"][3] == {"family": "Prince"}

    assert item["issued"]["date-parts"][0] == [2024]


def test_to_csl_json_minimal_record():
    """Ensure egress handles missing optional fields without raising exceptions."""
    record = {"arxiv_id": "math/0504001"}
    csl_str = to_csl_json(record)
    item = json.loads(csl_str)[0]

    assert item["id"] == "math/0504001"
    assert item["type"] == "article"
    assert item["issued"]["date-parts"][0] == [2005]

    assert "title" not in item
    assert "author" not in item
    assert "DOI" not in item
