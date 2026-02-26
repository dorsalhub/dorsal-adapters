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
    **kwargs: Any,
) -> str:
    """Egress: Converts a 'document-extraction' record into a Tab-Separated Values table."""
    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    blocks = record.get("blocks", [])
    if not blocks:
        raise ValueError("The provided record contains no 'blocks'.")

    output = io.StringIO()
    writer = csv.writer(output, delimiter="\t")

    headers = ["page_number", "block_type", "x", "y", "width", "height", "text"]
    writer.writerow(headers)

    for block in blocks:
        box = block.get("box", {})
        row = [
            block.get("page_number", ""),
            block.get("block_type", "text"),
            box.get("x", ""),
            box.get("y", ""),
            box.get("width", ""),
            box.get("height", ""),
            block.get("text", ""),
        ]
        writer.writerow(row)

    return output.getvalue()


def from_tsv(
    tsv_content: str, producer: str = "tsv-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """Ingress: Parses a TSV string back into a 'document-extraction' record."""
    if not tsv_content.strip():
        raise ValueError("Provided TSV content is empty.")

    f = io.StringIO(tsv_content.strip())
    reader = csv.DictReader(f, delimiter="\t")

    if not reader.fieldnames or "text" not in reader.fieldnames:
        raise ValueError("TSV must contain at least a 'text' column.")

    blocks = []
    for row in reader:
        block = {"block_type": row.get("block_type", "text") or "text", "text": row.get("text", "")}

        if "page_number" in row and row["page_number"].isdigit():
            block["page_number"] = int(row["page_number"])

        box = {}
        for dim in ["x", "y", "width", "height"]:
            if dim in row and row[dim]:
                try:
                    box[dim] = float(row[dim])
                except ValueError:
                    pass
        if box:
            block["box"] = box

        blocks.append(block)

    record = {"producer": producer, "extraction_type": "mixed", "unit": "px", "blocks": blocks}

    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    return record
