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
from dorsal_adapters.document.helpers import extract_spatial_pages


def to_txt(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
    strict: bool = False,
    **kwargs: Any,
) -> str:
    """Egress: Extracts the raw text from a 'document-extraction' record."""
    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    if not record.get("blocks"):
        raise ValueError("The provided record contains no 'blocks'.")

    pages = extract_spatial_pages(record, strict=strict, **kwargs)
    output = []

    for i, (page_num, paragraphs) in enumerate(pages):
        if i > 0:
            output.append(f"--- Page {page_num} ---")

        for para in paragraphs:
            text = para.get("text", "").strip()
            if text:
                output.append(text)

    return "\n\n".join(output)


def from_txt(
    txt_content: str, producer: str = "txt-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """Ingress: Wraps raw text into a valid 'document-extraction' record."""
    if not txt_content.strip():
        raise ValueError("Provided text content is empty.")

    record = {
        "producer": producer,
        "extraction_type": "text",
        "blocks": [{"block_type": "text", "text": txt_content.strip()}],
    }

    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    return record
