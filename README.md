<p align="center">
  <img src="https://dorsalhub.com/static/img/dorsal-adapters-logo.png" alt="Dorsal" width="520">
</p>

<p align="center">
  <a href="https://pypi.org/project/dorsalhub-adapters/">
    <img src="https://img.shields.io/pypi/v/dorsalhub-adapters?color=0ea5e9" alt="PyPI version">
  </a>
  <a href="https://codecov.io/gh/dorsalhub/dorsal-adapters">
    <img src="https://codecov.io/gh/dorsalhub/dorsal-adapters/graph/badge.svg" alt="codecov">
  </a>
  <a href="https://opensource.org/licenses/Apache-2.0">
    <img src="https://img.shields.io/badge/license-Apache_2.0-0ea5e9" alt="License">
  </a>
</p>

**Dorsal Adapters** translates [validated](https://github.com/dorsalhub/open-validation-schemas) JSON records into various industry-standard formats.

## Supported Formats

### Document Extraction (`open/document-extraction`)

* **`md`**: **RAG-Optimized Markdown** — Injects semantic headings, hallucination warnings, and visual placeholders directly into the text stream for LLM consumption.
* **`html`**: **Semantic HTML (.html)** — Renders a responsive, visually inferred 2D DOM layout from raw spatial coordinates.
* **`hocr`**: **hOCR (.hocr.html)** — An industry-standard OCR output format embedding layout, confidence scores, and style information in standard HTML.
* **`tsv`**: **Tab-Separated Values** — Perfect for spreadsheet ingestion and tabular data analysis.
* **`txt`**: **Plain Text** — Flattens the document layout into clean, stitched paragraphs.

### Audio Transcription (`open/audio-transcription`)

* **`srt`**: **SubRip Text (.srt)** — The most widely used plaintext subtitle format.
* **`vtt`**: **WebVTT (.vtt)** — The W3C standard web subtitle format for HTML5 video players.
* **`md`**: **RAG-Optimized Markdown** — Merges speaker tags, non-verbal events (e.g., `[laughter]`), and low-confidence warnings into clean markdown.
* **`tsv`**: **Tab-Separated Values** — Organizes segments, start/end times, and speakers into a neat table.
* **`txt`**: **Plain Text** — A continuous, readable transcript.

### arXiv Metadata (`dorsal/arxiv`)

* **`bib`**: **BibTeX (.bib)** — A standard bibliographic reference format, for LaTeX integration and academic publishing.
* **`ris`**: **RIS (.ris)** — A universal citation format, supported by reference managers e.g. Zotero, Mendeley, and EndNote.
* **`md`**: **RAG-Optimized Markdown** — Embeds standard YAML frontmatter (ID, DOI, Categories, Year) and markdown formatting for ingestion into PKMs or RAG pipelines.

---

## Installation

Dorsal Adapters is available on PyPI as `dorsalhub-adapters`:
```bash
pip install dorsalhub-adapters
```

## Usage

### Within Dorsal

Dorsal Adapters is a core dependency for [Dorsal](https://github.com/dorsalhub/dorsal).

Example: using `--export` to generate a subtitle file.

```console
$ dorsal run dorsalhub/whisper /home/video/test.mkv --export=srt
1
00:00:01,970 --> 00:00:05,970
You might be wondering how I ended up in this situation.

2
00:00:05,970 --> 00:00:08,970
Yeah that's me. A young subtitle.

3
00:00:08,970 --> 00:00:18,590
Little did I know what life had in store for me.


Outputs saved successfully:
  ↳ /home/user/sandbox/test.dorsal.json
  ↳ /home/user/sandbox/test.srt
```

- `--export` can take the ID of adapter for a given output schema (e.g. `md` for Markdown or `txt` for text).

### Standalone Usage

Adapters are Python classes with methods for exporting to and parsing from the supported file formats:

* `export(record)` / `export_file(record, fp)`: Converts a JSON record into a standard format.
* `parse(content)` / `parse_file(fp)`: Best-effort conversion from a standard format back into a Dorsal JSON Record.

#### Example: Audio to Subtitles (SRT)

In this example, a valid [`open/audio-transcription`](https://docs.dorsalhub.com/reference/schemas/open/audio-transcription/) record is converted into a subtitle file.

```python
from dorsal_adapters.registry import get_adapter

# 1. The raw JSON record from your model
transcription = {
    "track_id": 1,
    "language": "eng",
    "segments": [
        {
            "start_time": 0.5,
            "end_time": 4.75,
            "text": "Welcome back! Today, my guest is the renowned chef, Jean-Pierre."
        }
    ]
}

# 2. Retrieve the adapter for the schema and target format
adapter = get_adapter("audio-transcription", "srt")

# 3. Export to the target format (.srt)
srt_string = adapter.export(transcription)
print(srt_string)

# 4. Parse the formatted string back into a Dorsal record
parsed_record = adapter.parse(srt_string)

```

**Tip:** You can programmatically check what formats are supported for a given schema using `list_formats`:

```python
from dorsal_adapters.registry import list_formats
print(list_formats("document-extraction"))

```

## Contributing

We welcome contributions! If you have written a translation script for an **Open Validation Schema**, please open a PR.

## License

Dorsal Adapters is open source and provided under the Apache 2.0 license.
