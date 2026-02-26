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
import os
import pytest


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_json(filename: str) -> dict:
    """Helper to load a JSON file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def valid_audio_record() -> dict:
    """Provides a valid audio transcription record."""
    return load_json("audio-transcription-1.json")


@pytest.fixture
def invalid_audio_record_1() -> dict:
    """Provides a record with an invalid segment (missing required fields)."""
    return load_json("audio-transcription-invalid-segment.json")


@pytest.fixture
def invalid_audio_record_2() -> dict:
    """Provides a record entirely missing text and segments."""
    return load_json("audio-transcription-missing-content.json")


@pytest.fixture
def valid_document_record_1() -> dict:
    """Provides a valid mixed-extraction record."""
    return load_json("document-extraction-1.json")


@pytest.fixture
def valid_document_record_2() -> dict:
    """Provides a valid record with visual elements but no text."""
    return load_json("document-extraction-2.json")


@pytest.fixture
def invalid_document_missing_text() -> dict:
    """Provides a record with missing text."""
    return load_json("document-extraction-bad-missing-text.json")


@pytest.fixture
def invalid_document_bad_norm() -> dict:
    """Provides a record with a bad multipolygon."""
    return load_json("document-extraction-bad-multipolygon-norm.json")
