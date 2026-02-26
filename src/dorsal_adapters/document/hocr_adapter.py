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

import html
import json
from typing import Any
from html.parser import HTMLParser

from dorsal_adapters.common.validation import validate_record


def _get_page_dimension(dim_data: Any, page_num: int, default: int = 1000) -> int:
    """Extracts the width or height for a specific page from the Open Schema format."""
    if isinstance(dim_data, (int, float)):
        return int(dim_data)

    if isinstance(dim_data, list):
        for config in dim_data:
            if page_num in config.get("pages", []):
                return int(config.get("value", default))

    return default


def _calculate_bbox(block: dict[str, Any]) -> tuple[int, int, int, int] | None:
    """Calculates x0, y0, x1, y1 from box, polygon, or multi_polygon."""
    if "box" in block:
        b = block["box"]
        return (int(b["x"]), int(b["y"]), int(b["x"] + b["width"]), int(b["y"] + b["height"]))

    if "polygon" in block:
        poly = block["polygon"]
        xs = [pt["x"] for pt in poly]
        ys = [pt["y"] for pt in poly]
        return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))

    if "multi_polygon" in block:
        xs, ys = [], []
        for poly in block["multi_polygon"]:
            xs.extend([pt["x"] for pt in poly])
            ys.extend([pt["y"] for pt in poly])
        if xs and ys:
            return (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))

    return None


def to_hocr(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
    **kwargs: Any,
) -> str:
    """Egress: Converts a 'document-extraction' record into an hOCR HTML document."""
    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    blocks = record.get("blocks", [])
    if not blocks:
        raise ValueError("The provided record contains no 'blocks'.")

    pages: dict[int, list[dict[str, Any]]] = {}
    for block in blocks:
        p_num = block.get("page_number", 1)
        pages.setdefault(p_num, []).append(block)

    output = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '  <meta charset="utf-8"/>',
        "  <title>hOCR Output</title>",
        f'  <meta name="ocr-system" content="{html.escape(record.get("producer", "dorsal-adapters"))}"/>',
        '  <meta name="ocr-capabilities" content="ocr_page ocr_carea ocr_par ocr_line ocrx_word"/>',
        "</head>",
        "<body>",
    ]

    for page_num in sorted(pages.keys()):
        width = _get_page_dimension(record.get("page_width"), page_num, default=1000)
        height = _get_page_dimension(record.get("page_height"), page_num, default=1000)

        output.append(f'  <div class="ocr_page" id="page_{page_num}" title="bbox 0 0 {width} {height}">')

        for block in pages[page_num]:
            attrs = block.get("attributes", {})
            hocr_class = attrs.pop("hocr_class", "ocr_line")

            title_parts = []
            bbox = _calculate_bbox(block)
            if bbox:
                title_parts.append(f"bbox {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}")

            if "score" in block:
                x_wconf = int(block["score"] * 100)
                title_parts.append(f"x_wconf {x_wconf}")

            title_attr = f' title="{"; ".join(title_parts)}"' if title_parts else ""

            data_attrs = []
            for k, v in attrs.items():
                if isinstance(v, (dict, list)):
                    v = json.dumps(v)
                data_attrs.append(f'data-{html.escape(str(k))}="{html.escape(str(v))}"')

            if "polygon" in block:
                data_attrs.append(f'data-polygon="{html.escape(json.dumps(block["polygon"]))}"')
            elif "multi_polygon" in block:
                data_attrs.append(f'data-multi-polygon="{html.escape(json.dumps(block["multi_polygon"]))}"')

            id_attr = f' id="{html.escape(block["id"])}"' if "id" in block else ""
            data_attr_str = (" " + " ".join(data_attrs)) if data_attrs else ""

            tag = "div" if hocr_class in ("ocr_carea", "ocr_par") else "span"
            text_content = html.escape(block.get("text", ""))

            output.append(
                f'    <{tag} class="{html.escape(hocr_class)}"{id_attr}{title_attr}{data_attr_str}>{text_content}</{tag}>'
            )

        output.append("  </div>")

    output.append("</body>\n</html>")

    return "\n".join(output)


def _parse_hocr_title(title: str) -> dict[str, Any]:
    """Parses hOCR title attribute into bbox, score, etc."""
    result: dict[str, Any] = {}
    for prop in title.split(";"):
        prop = prop.strip()
        if not prop:
            continue
        parts = prop.split()
        if parts[0] == "bbox" and len(parts) == 5:
            try:
                x0, y0, x1, y1 = map(float, parts[1:])
                result["box"] = {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
            except ValueError:
                pass
        elif parts[0] == "x_wconf" and len(parts) == 2:
            try:
                result["score"] = float(parts[1]) / 100.0
            except ValueError:
                pass
    return result


class HOCRParser(HTMLParser):
    """Zero-dependency HTML Parser specifically built to extract hOCR layout data."""

    def __init__(self, target_class: str = "ocr_line"):
        super().__init__()
        self.target_class = target_class
        self.blocks: list[dict[str, Any]] = []
        self.page_width_map: dict[int, float] = {}
        self.page_height_map: dict[int, float] = {}
        self.page_count = 0
        self.current_page_num = 1

        self.stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = {k: v or "" for k, v in attrs}
        classes = attr_dict.get("class", "").split()
        hocr_class = next((c for c in classes if c.startswith("ocr")), None)

        if hocr_class == "ocr_page":
            self.page_count += 1

            page_id = attr_dict.get("id", "")
            import re

            m = re.search(r"\d+", page_id)
            self.current_page_num = int(m.group()) if m else self.page_count

            title_data = _parse_hocr_title(attr_dict.get("title", ""))
            if "box" in title_data:
                self.page_width_map[self.current_page_num] = title_data["box"]["width"]
                self.page_height_map[self.current_page_num] = title_data["box"]["height"]

        self.stack.append(
            {
                "tag": tag,
                "hocr_class": hocr_class,
                "attr_dict": attr_dict,
                "text_chunks": [],
                "page_num": self.current_page_num,
            }
        )

    def handle_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1]["text_chunks"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return

        for i in reversed(range(len(self.stack))):
            if self.stack[i]["tag"] == tag:
                closed_element = self.stack.pop(i)

                full_text = "".join(closed_element["text_chunks"])

                if self.stack:
                    self.stack[-1]["text_chunks"].append(full_text)

                import re

                clean_text = re.sub(r"\s+", " ", full_text).strip()

                if closed_element["hocr_class"] == self.target_class and clean_text:
                    self._build_block(closed_element, clean_text)
                break

    def _build_block(self, element: dict[str, Any], text: str) -> None:
        attr_dict = element["attr_dict"]
        title_data = _parse_hocr_title(attr_dict.get("title", ""))

        block: dict[str, Any] = {"block_type": "text", "text": text, "page_number": element["page_num"]}

        if "id" in attr_dict:
            block["id"] = attr_dict["id"]

        if "box" in title_data:
            block["box"] = title_data["box"]
        if "score" in title_data:
            block["score"] = title_data["score"]

        attributes = {"hocr_class": element["hocr_class"]}

        for k, v in attr_dict.items():
            if k.startswith("data-"):
                key_name = k[5:]

                if key_name == "polygon":
                    try:
                        block["polygon"] = json.loads(v)
                    except json.JSONDecodeError:
                        pass
                elif key_name == "multi-polygon":
                    try:
                        block["multi_polygon"] = json.loads(v)
                    except json.JSONDecodeError:
                        pass
                else:
                    try:
                        attributes[key_name] = json.loads(v)
                    except (json.JSONDecodeError, TypeError):
                        attributes[key_name] = v

        block["attributes"] = attributes
        self.blocks.append(block)


def from_hocr(
    hocr_content: str,
    producer: str = "hocr-adapter",
    *,
    validate: bool = True,
    schema_version: str | None = None,
    target_class: str = "ocr_line",
) -> dict[str, Any]:
    """Ingress: Parses an hOCR HTML string back into a 'document-extraction' record."""
    if not hocr_content.strip():
        raise ValueError("Provided hOCR content is empty.")

    parser = HOCRParser(target_class=target_class)
    parser.feed(hocr_content)

    record: dict[str, Any] = {"producer": producer, "extraction_type": "mixed", "unit": "px", "blocks": parser.blocks}

    if parser.page_width_map:
        record["page_width"] = [{"value": v, "pages": [k]} for k, v in parser.page_width_map.items()]
    if parser.page_height_map:
        record["page_height"] = [{"value": v, "pages": [k]} for k, v in parser.page_height_map.items()]

    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    return record
