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


import datetime
from typing import Any, Dict
import srt

from dorsal_adapters.common.validation import validate_record


def to_srt(
    record: Dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
) -> str:
    """Converts an Open Validation Schema 'audio-transcription' record into a formatted SRT string.

    Args:
        record (dict): The record instance to convert.
    """
    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    segments = record.get("segments", [])
    if not segments:
        raise ValueError("The provided record does not contain any 'segments'.")

    subtitles = []

    for i, segment in enumerate(segments, start=1):
        start = datetime.timedelta(seconds=segment["start_time"])
        end = datetime.timedelta(seconds=segment["end_time"])

        sub = srt.Subtitle(index=i, start=start, end=end, content=segment["text"].strip())
        subtitles.append(sub)

    return str(srt.compose(subtitles))


def from_srt(
    srt_content: str, producer: str = "srt-adapter", validate: bool = True, schema_version: str | None = None
) -> Dict[str, Any]:
    """
    Ingress: Parses an SRT string and converts it into a valid
    Open Validation Schema 'audio-transcription' record.
    """
    try:
        subtitles = list(srt.parse(srt_content))
    except srt.SRTParseError as err:
        raise ValueError(f"Failed to parse SRT content: {err}") from err

    segments = []
    full_text_blocks = []

    for sub in subtitles:
        start_time = sub.start.total_seconds()
        end_time = sub.end.total_seconds()

        text = sub.content.replace("\n", " ").strip()

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
