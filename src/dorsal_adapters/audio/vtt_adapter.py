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

import webvtt
from typing import Any

from dorsal_adapters.common.validation import validate_record


def _vtt_time_to_seconds(time_str: str) -> float:
    """Converts WebVTT timestamp format (HH:MM:SS.mmm or MM:SS.mmm) into seconds."""
    parts = time_str.split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def _seconds_to_vtt_time(seconds: float) -> str:
    """Converts seconds into WebVTT timestamp format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def to_vtt(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
    include_speakers: bool = False,
) -> str:
    """Converts an Open Validation Schema 'audio-transcription' record into a formatted WebVTT string.

    Args:
        record (dict): The record instance to convert.
        validate (bool): Whether to validate the record against the Dorsal schema.
        schema_version (str | None): The specific schema version to validate against.
    """
    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    segments = record.get("segments", [])
    if not segments:
        raise ValueError("The provided record does not contain any 'segments'.")

    vtt = webvtt.WebVTT()

    for segment in segments:
        caption = webvtt.Caption(
            start=_seconds_to_vtt_time(segment["start_time"]),
            end=_seconds_to_vtt_time(segment["end_time"]),
            text=segment["text"].strip(),
        )

        if include_speakers:
            speaker = segment.get("speaker")
            if speaker and "name" in speaker:
                caption.text = f"<v {speaker['name']}>{caption.text}"

        vtt.captions.append(caption)

    return str(vtt.content)


def from_vtt(
    vtt_content: str, producer: str = "vtt-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """
    Ingress: Parses a WebVTT string and converts it into a valid
    Open Validation Schema 'audio-transcription' record.
    """
    try:
        vtt = webvtt.from_string(vtt_content)
    except Exception as err:
        raise ValueError(f"Failed to parse WebVTT content: {err}") from err

    segments = []
    full_text_blocks = []

    for caption in vtt:
        start_time = _vtt_time_to_seconds(caption.start)
        end_time = _vtt_time_to_seconds(caption.end)

        text = caption.text.replace("\n", " ").strip()

        segments.append({"text": text, "start_time": start_time, "end_time": end_time})
        full_text_blocks.append(text)

    record = {
        "producer": producer,
        "text": " ".join(full_text_blocks),
        "segments": segments,
    }

    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    return record
