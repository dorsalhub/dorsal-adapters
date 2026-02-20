<p align="center">
  <img src="https://dorsalhub.com/static/img/dorsal-adapters-logo.png" alt="Dorsal" width="520">
</p>

<p align="center">
  <strong>Export validated JSON to standard formats.</strong>
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

## Installation

Dorsal Adapters is available on pypi as `dorsalhub-adapters`:
```bash
pip install dorsalhub-adapters
```

## Usage

Adapters are strictly typed, pure Python classes with four exposed methods: 
- `export(record)` / `export_file(record, fp)`: Converts a JSON record into a standard format e.g. `audio-transcription` -> **.srt**
- `parse(content)` / `parse_file(fp)`: Best effort conversion from a standard format to JSON Record, e.g. **.srt** -> `audio-transcription`

In both cases, the JSON is [Open Validation Schemas](https://github.com/dorsalhub/open-validation-schemas)-compliant.


### Example: Two-Way Audio Conversion

In this example, a valid [`open/audio-transcription`](https://docs.dorsalhub.com/reference/schemas/open/audio-transcription/) record is converted to SubRip Text (.srt) format.

```python
from dorsal_adapters.registry import get_adapter

# 1. The record we want to convert.
dorsal_record = {
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
srt_string = adapter.export(dorsal_record)
print(srt_string)

# 4. Parse the formatted string back into a Dorsal record
parsed_record = adapter.parse(srt_string)

```

**Tip:** You can check what formats are supported for a given schema using `list_formats`:

```python
from dorsal_adapters.registry import list_formats

print(list_formats("audio-transcription"))
```

## Supported Formats

Dorsal Adapters supports two-way conversion (exporting and parsing) between schema-validated JSON records and the following formats:

### Audio Transcription (via `open/audio-transcription`)

* `srt`: SubRip Subtitle format
* `vtt`: WebVTT format - W3C standard web subtitle format
* `md`: Markdown format - A markdown-formatted audio transcription optimized for RAG
* `txt`: Plain Text format
* `tsv`: Tab-Separated Values format

## Contributing

We welcome contributions! If you have written a translation script for an **Open Validation Schema** that maps to a widely used industry standard, please open a PR.

See `CONTRIBUTING.md` for our development setup using `uv` and our strict typing guidelines.

## License

Dorsal Adapters is open source and provided under the Apache 2.0 license.
