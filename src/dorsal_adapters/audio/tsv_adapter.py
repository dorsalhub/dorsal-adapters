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

import csv
import io
from typing import Any

from dorsal_adapters.common.validation import validate_record


def to_tsv(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
    include_speakers: bool = False,
) -> str:
    """Egress: Converts an 'audio-transcription' record to TSV format."""
    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    segments = record.get("segments", [])
    if not segments:
        raise ValueError("The provided record does not contain any 'segments'.")

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")

    headers = ["start_time", "end_time", "text"]
    if include_speakers:
        headers.append("speaker")

    writer.writerow(headers)

    for segment in segments:
        row = [f"{segment['start_time']:.3f}", f"{segment['end_time']:.3f}", segment["text"].replace("\t", " ").strip()]

        if include_speakers:
            speaker_name = segment.get("speaker", {}).get("name", "")
            row.append(speaker_name)

        writer.writerow(row)

    return output.getvalue()


def from_tsv(
    tsv_content: str, producer: str = "tsv-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """Ingress: Parses a TSV string into an 'audio-transcription' record."""
    if not tsv_content.strip():
        raise ValueError("Provided TSV content is empty.")

    f = io.StringIO(tsv_content.strip())
    reader = csv.DictReader(f, delimiter="\t")

    if not reader.fieldnames or "start_time" not in reader.fieldnames or "text" not in reader.fieldnames:
        raise ValueError("TSV must contain at least 'start_time' and 'text' columns.")

    segments = []
    full_text_blocks = []

    for row in reader:
        text = row["text"].strip()
        segment = {
            "start_time": float(row["start_time"]),
            "end_time": float(row.get("end_time", row["start_time"])),
            "text": text,
        }

        # Optionally grab speaker if it exists in the ingress data
        if "speaker" in row and row["speaker"].strip():
            segment["speaker"] = {"id": row["speaker"].strip(), "name": row["speaker"].strip()}

        segments.append(segment)
        full_text_blocks.append(text)

    record = {
        "producer": producer,
        "text": " ".join(full_text_blocks),
        "segments": segments,
    }

    if validate:
        validate_record(record, schema_id="audio-transcription", version=schema_version)

    return record
