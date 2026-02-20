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
