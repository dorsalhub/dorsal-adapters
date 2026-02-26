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

from typing import Any
from dorsal_adapters.common.validation import validate_record


def to_txt(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
) -> str:
    """Egress: Extracts the raw text from an 'audio-transcription' record."""
    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    # Prefer the concatenated text field if it exists
    if "text" in record and record["text"].strip():
        text: str = record["text"]
        return text.strip()

    # Fallback to joining segments
    segments = record.get("segments", [])
    if not segments:
        raise ValueError("The provided record contains no 'text' or 'segments'.")

    return " ".join(segment["text"].strip() for segment in segments)


def from_txt(
    txt_content: str, producer: str = "txt-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """Ingress: Wraps raw text into a valid 'audio-transcription' record."""
    if not txt_content.strip():
        raise ValueError("Provided text content is empty.")

    record = {
        "producer": producer,
        "text": txt_content.strip(),
    }

    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    return record
