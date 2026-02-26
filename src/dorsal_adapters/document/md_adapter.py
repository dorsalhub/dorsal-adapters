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
import re
from typing import Any
from dorsal_adapters.common.validation import validate_record
from dorsal_adapters.document.helpers import extract_spatial_pages


def to_md(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
    strict: bool = False,
    include_frontmatter: bool = True,
    low_confidence_threshold: float = 0.80,
    **kwargs: Any,
) -> str:
    """Egress: Converts a 'document-extraction' record into a RAG-optimized Markdown document."""
    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    if not record.get("blocks"):
        raise ValueError("The provided record contains no 'blocks'.")

    output = []

    if include_frontmatter:
        frontmatter = ["---"]
        for key in ["producer", "extraction_type", "unit", "score_explanation"]:
            if key in record:
                frontmatter.append(f"{key}: {record[key]}")

        if "attributes" in record and isinstance(record["attributes"], dict):
            frontmatter.append("attributes:")
            for k, v in record["attributes"].items():
                val_str = json.dumps(v)
                frontmatter.append(f"  {k}: {val_str}")

        frontmatter.append("---")
        if len(frontmatter) > 2:
            output.append("\n".join(frontmatter))

    pages = extract_spatial_pages(record, strict=strict, **kwargs)

    for _i, (page_num, paragraphs) in enumerate(pages):
        output.append(f"## Page {page_num}")

        for para in paragraphs:
            text = para.get("text", "").strip()
            b_type = para.get("block_type", "text")
            attrs = para.get("attributes", {})
            score = para.get("score")

            if not text and b_type != "text":
                box = para.get("box")
                if box:
                    coords = (
                        f"x:{round(box['x'])}, y:{round(box['y'])}, w:{round(box['width'])}, h:{round(box['height'])}"
                    )
                    output.append(f"> *[{b_type.capitalize()} at {coords}]*")
                continue

            if not text:
                continue

            visual_class = str(attrs.get("visual_class", "")).lower()
            if visual_class in ("title", "h1"):
                text = f"# {text}"
            elif visual_class == "h2":
                text = f"## {text}"
            elif visual_class in ("h3", "heading"):
                text = f"### {text}"

            if score is not None and score < low_confidence_threshold:
                text = f"> ⚠️ **Low Confidence Read ({score:.2f})**:\n> {text}"

            output.append(text)

    return "\n\n".join(output)


def from_md(
    md_content: str, producer: str = "md-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """Ingress: Parses a Markdown string back into a 'document-extraction' record."""
    if not md_content.strip():
        raise ValueError("Provided Markdown content is empty.")

    clean_content = re.sub(r"^---\n.*?\n---\n", "", md_content, flags=re.DOTALL).strip()

    blocks = []
    current_page = 1
    page_pattern = re.compile(r"^##\s+Page\s+(\d+)", re.IGNORECASE)

    for line in clean_content.splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped == "---":
            continue

        match = page_pattern.match(line_stripped)
        if match:
            current_page = int(match.group(1))
            continue

        blocks.append({"block_type": "text", "text": line_stripped, "page_number": current_page})

    record = {"producer": producer, "extraction_type": "text", "blocks": blocks}

    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    return record
