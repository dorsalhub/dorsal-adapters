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

import importlib
import json

from typing import Any, Callable, IO


class Adapter:
    """Convert between schema-validated records and specific formats."""

    __slots__ = ("schema_id", "format_name", "description", "extension", "_export_fn", "_parse_fn")

    def __init__(
        self,
        schema_id: str,
        format_name: str,
        description: str,
        extension: str,
        export_fn: Callable[..., Any],
        parse_fn: Callable[..., dict[str, Any]],
    ) -> None:
        self.schema_id = schema_id
        self.format_name = format_name
        self.description = description
        self.extension = extension
        self._export_fn = export_fn
        self._parse_fn = parse_fn

    def export(self, record: dict[str, Any] | str | bytes, **kwargs: Any) -> Any:
        """
        Converts a Dorsal record into the target format.
        Smartly accepts either a Python dictionary or a stringified JSON record.
        """
        if isinstance(record, (str, bytes)):
            try:
                record = json.loads(record)
            except json.JSONDecodeError as err:
                raise ValueError(f"Failed to decode stringified JSON record: {err}") from err

        if not isinstance(record, dict):
            raise TypeError(f"Record must be a dictionary or a JSON string, got {type(record).__name__}.")

        return self._export_fn(record, **kwargs)

    def parse(self, content: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Parses the target format (e.g., an SRT string) into a validated Dorsal record.
        """
        return self._parse_fn(content, **kwargs)

    def export_file(self, record: dict[str, Any] | str | bytes, fp: IO[Any], **kwargs: Any) -> None:
        """
        Converts a Dorsal record and writes it directly to a file-like object.
        """
        fp.write(self.export(record, **kwargs))

    def parse_file(self, fp: IO[Any], **kwargs: Any) -> dict[str, Any]:
        """
        Reads from a file-like object and parses it into a validated Dorsal record.
        """
        return self.parse(fp.read(), **kwargs)

    def __repr__(self) -> str:
        return f"Adapter(schema_id='{self.schema_id}', format_name='{self.format_name}')"


_REGISTRY: dict[tuple[str, str], tuple[str, str, str, str, str]] = {
    # dorsal/arxiv
    ("dorsal/arxiv", "bibtex"): (
        "BibTeX (.bib) - A bibliographic reference format.",
        "dorsal_adapters.arxiv.bibtext_adapter",
        "to_bibtex",
        "from_bibtex",
        "bib",
    ),
    ("dorsal/arxiv", "md"): (
        "Markdown (.md) - A RAG-optimized markdown document.",
        "dorsal_adapters.arxiv.md_adapter",
        "to_md",
        "from_md",
        "md",
    ),
    # audio-transcription
    ("open/audio-transcription", "srt"): (
        "SubRip Text (.srt) - A widely used, plaintext subtitle format.",
        "dorsal_adapters.audio.srt_adapter",
        "to_srt",
        "from_srt",
        "srt",
    ),
    ("open/audio-transcription", "vtt"): (
        "WebVTT (.vtt) - W3C standard web subtitle format.",
        "dorsal_adapters.audio.vtt_adapter",
        "to_vtt",
        "from_vtt",
        "vtt",
    ),
    ("open/audio-transcription", "md"): (
        "Markdown (.md) - A markdown-formatted audio transcription",
        "dorsal_adapters.audio.md_adapter",
        "to_md",
        "from_md",
        "md",
    ),
    ("open/audio-transcription", "txt"): (
        "Plain Text (.txt).",
        "dorsal_adapters.audio.txt_adapter",
        "to_txt",
        "from_txt",
        "txt",
    ),
    ("open/audio-transcription", "tsv"): (
        "Tab-Separated Values (.tsv).",
        "dorsal_adapters.audio.tsv_adapter",
        "to_tsv",
        "from_tsv",
        "tsv",
    ),
    # document-extraction
    ("open/document-extraction", "txt"): (
        "Plain Text (.txt).",
        "dorsal_adapters.document.txt_adapter",
        "to_txt",
        "from_txt",
        "txt",
    ),
    ("open/document-extraction", "tsv"): (
        "Tab-Separated Values (.tsv).",
        "dorsal_adapters.document.tsv_adapter",
        "to_tsv",
        "from_tsv",
        "tsv",
    ),
    ("open/document-extraction", "hocr"): (
        "hOCR (.html) - An OCR output format in standard HTML",
        "dorsal_adapters.document.hocr_adapter",
        "to_hocr",
        "from_hocr",
        "hocr.html",
    ),
    ("open/document-extraction", "md"): (
        "Markdown (.md) - A markdown-formatted document transcription",
        "dorsal_adapters.document.md_adapter",
        "to_md",
        "from_md",
        "md",
    ),
    ("open/document-extraction", "html"): (
        "Semantic HTML (.html) - A responsive, visually inferred layout.",
        "dorsal_adapters.document.html_adapter",
        "to_html",
        "from_html",
        "html",
    ),
}

ALIAS_MAPPING = {"audio-transcription": "open/audio-transcription", "document-extraction": "open/document-extraction"}


def get_adapter(schema_id: str, format_name: str) -> Adapter:
    """
    Just-In-Time Factory: Dynamically imports the required module and returns
    a freshly instantiated Adapter object.
    """
    if schema_id in ALIAS_MAPPING:
        schema_id = ALIAS_MAPPING[schema_id]
    try:
        desc, module_path, export_name, parse_name, ext = _REGISTRY[(schema_id, format_name)]
    except KeyError as err:
        raise ValueError(f"Adapter not found for schema={schema_id} and format={format_name}.") from err

    module = importlib.import_module(module_path)

    export_fn = getattr(module, export_name)
    parse_fn = getattr(module, parse_name)

    return Adapter(
        schema_id=schema_id,
        format_name=format_name,
        description=desc,
        extension=ext,
        export_fn=export_fn,
        parse_fn=parse_fn,
    )


def list_formats(schema_id: str) -> list[tuple[str, str]]:
    """Returns a list of (format_name, description) for all supported formats of a schema."""
    formats = [(fmt, desc) for (sid, fmt), (desc, _, _, _, _) in _REGISTRY.items() if sid == schema_id]
    return sorted(formats, key=lambda x: x[0])
