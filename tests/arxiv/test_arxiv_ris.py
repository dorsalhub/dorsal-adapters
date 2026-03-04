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

from dorsal_adapters.arxiv.ris_adapter import to_ris


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
