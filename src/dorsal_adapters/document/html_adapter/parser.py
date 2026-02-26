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

import re
from typing import Any

from dorsal_adapters.common.validation import validate_record


def from_html(
    html_content: str, producer: str = "html-adapter", *, validate: bool = True, schema_version: str | None = None
) -> dict[str, Any]:
    """Ingress: Extracts raw text from HTML and wraps it into a basic 'document-extraction' record."""
    if not html_content.strip():
        raise ValueError("Provided HTML content is empty.")

    text_content = re.sub(r"<[^>]+>", " ", html_content)
    text_content = re.sub(r"\s+", " ", text_content).strip()

    record = {
        "producer": producer,
        "extraction_type": "text",
        "blocks": [{"block_type": "text", "text": text_content}],
    }

    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    return record
