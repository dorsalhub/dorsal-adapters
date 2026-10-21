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
import os
import re
from typing import Any, Literal

from dorsal_adapters.common.validation import validate_record
from dorsal_adapters.document.helpers import extract_spatial_pages, get_page_dim, xy_cut
from dorsal_adapters.document.html_adapter.render import format_css_coords, render_tree
from dorsal_adapters.document.html_adapter.styles import CORE_CSS, THEMES

_STYLE_END_TAG = re.compile(r"</(?=style)", re.IGNORECASE)


def _read_stylesheet(path: str | os.PathLike[str]) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return _STYLE_END_TAG.sub(r"<\\/", f.read())


def _resolve_theme_css(style: str, style_path: str | os.PathLike[str] | None) -> str:
    if style_path is not None:
        if style != "default":
            raise ValueError("Pass either 'style' or 'style_path', not both.")
        return _read_stylesheet(style_path)

    theme_css = THEMES.get(style)
    if theme_css is None:
        raise ValueError(
            f"Unknown style {style!r}. Use one of the themes 'default', 'dark' or 'none', "
            "or pass a stylesheet file as 'style_path'."
        )
    return theme_css


def _footer_div(footer: str) -> str:
    return f'  <div class="document-footer">\n    {html.escape(str(footer))}\n  </div>'


def to_html(
    record: dict[str, Any],
    *,
    validate: bool = True,
    schema_version: str | None = None,
    strict: bool = False,
    layout: Literal["col", "grid", "wireframe"] = "col",
    style: Literal["default", "dark", "none"] | str = "default",
    style_path: str | os.PathLike[str] | None = None,
    footer: str | None = None,
    fragment: bool = False,
    **kwargs: Any,
) -> str:
    """Egress: Converts a 'document-extraction' record into responsive semantic HTML.

    Args:
        record: The 'document-extraction' record to render.
        validate: Validate the record against its schema before rendering.
        schema_version: The schema version to validate against.
        strict: Keep each line of a paragraph on its own line.
        layout: 'col' (a single column), 'grid' (a 2D layout inferred from the block coordinates)
            or 'wireframe' (each block drawn at its coordinates).
        style: The theme: 'default', 'dark' or 'none'. Any other value raises `ValueError`;
            pass a custom stylesheet as `style_path`.
        style_path: A CSS file to use in place of the theme. Its contents are embedded in the page.
        footer: Text shown at the bottom of the page. It is escaped, so any HTML in it is shown as text.
        fragment: Return only the document markup, without `<html>`, `<head>` or `<body>`.
            `style` and `style_path` are ignored.
    """
    if validate:
        validate_record(record, schema_id="document-extraction", version=schema_version)

    unit = record.get("unit", "px")
    spatial_pages = extract_spatial_pages(record, strict=strict, **kwargs)

    html_out = []

    if not fragment:
        theme_css = _resolve_theme_css(style, style_path)

        html_out.extend(
            [
                "<!DOCTYPE html>",
                '<html lang="en">',
                "<head>",
                '  <meta charset="utf-8"/>',
                "  <title>Document Extraction</title>",
                "  <style>",
                CORE_CSS,
                theme_css,
                "  </style>",
                "</head>",
                "<body>",
            ]
        )

    if not spatial_pages:
        html_out.append(
            '  <div class="page-container page-flow"><p class="block-text"><em>No content extracted from this document.</em></p></div>'
        )
        if footer:
            html_out.append(_footer_div(footer))

        if not fragment:
            html_out.extend(["</body>", "</html>"])

        return "\n".join(html_out)

    gap_y = float(kwargs.get("gap_y", -1.0))
    gap_x = float(kwargs.get("gap_x", -1.0))

    for i, (page_num, paragraphs) in enumerate(spatial_pages):
        if i > 0:
            html_out.append(f'  <div class="page-divider">Page {html.escape(str(page_num))}</div>')

        pw = get_page_dim(record, page_num, "page_width") or 850.0
        ph = get_page_dim(record, page_num, "page_height") or 1100.0

        if layout == "wireframe":
            html_out.append(
                f'  <div class="page-container page-wireframe" style="width: {pw}px; height: {ph}px; max-width: 100%;">'
            )
        elif layout in ("grid", "col"):
            html_out.append('  <div class="page-container page-flow">')
        else:
            raise ValueError(f"Unknown layout: '{layout}'. Supported layouts are 'col', 'grid', and 'wireframe'.")

        if layout == "grid":
            page_tree = xy_cut(paragraphs, gap_y=gap_y, gap_x=gap_x)
            html_out.append(render_tree(page_tree))

        elif layout == "col":
            html_out.append('<div class="layout-y">')
            for para in paragraphs:
                text = para.get("text", "")
                b_type = para.get("block_type", "text")
                if text:
                    html_out.append(f'  <p class="block-text">{html.escape(text)}</p>')
                else:
                    html_out.append(f'  <div class="figure-placeholder">[{html.escape(str(b_type))}]</div>')
            html_out.append("</div>")

        elif layout == "wireframe":
            for para in paragraphs:
                box = para.get("box")
                text = para.get("text", "")
                if box:
                    style_str = format_css_coords(box, unit)
                    html_out.append(
                        f'  <div class="wireframe-box" style="{style_str}" title="{html.escape(text)}">{html.escape(text)}</div>'
                    )

        html_out.append("  </div>")

    if footer:
        html_out.append(_footer_div(footer))

    if not fragment:
        html_out.extend(["</body>", "</html>"])

    return "\n".join(html_out)
