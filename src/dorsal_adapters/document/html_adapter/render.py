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

from typing import Any


def format_css_coords(box: dict[str, float], unit: str) -> str:
    """Translates schema units into absolute CSS positioning coordinates."""
    if unit == "normalized":
        return f"left: {box['x'] * 100}%; top: {box['y'] * 100}%; width: {box['width'] * 100}%; height: {box['height'] * 100}%;"
    elif unit == "per_mille":
        return f"left: {box['x'] / 10}%; top: {box['y'] / 10}%; width: {box['width'] / 10}%; height: {box['height'] / 10}%;"
    else:
        return f"left: {box['x']}px; top: {box['y']}px; width: {box['width']}px; height: {box['height']}px;"


def render_tree(node: dict[str, Any]) -> str:
    """Converts the layout tree into responsive Flexbox HTML."""
    ntype = node.get("type")
    if ntype == "empty":
        return ""

    if ntype == "leaf":
        block = node["block"]
        text = block.get("text", "")
        b_type = block.get("block_type", "text")
        if text:
            return f'<p class="block-text">{html.escape(text)}</p>'
        return f'<div class="figure-placeholder">[{b_type}]</div>'

    if ntype == "cluster":
        return "".join(render_tree(c) for c in node.get("children", []))

    box = node.get("box")
    children = node.get("children", [])

    if ntype == "y-cut":
        html_out = ['<div class="layout-y">']
        for c in children:
            html_out.append(render_tree(c))
        html_out.append("</div>")
        return "".join(html_out)

    if ntype == "x-cut":
        html_out = ['<div class="layout-x">']
        curr_x = box["x"] if box else 0
        parent_w = box["width"] if box and box["width"] > 0 else 1

        for c in children:
            c_box = c.get("box")
            if c_box:
                w_pct = (c_box["width"] / parent_w) * 100
                ml_pct = max(0, ((c_box["x"] - curr_x) / parent_w) * 100)
                style = f"width: {w_pct}%; margin-left: {ml_pct}%;"
                curr_x = c_box["x"] + c_box["width"]
            else:
                style = "flex: 1;"
            html_out.append(f'<div class="col" style="{style}">{render_tree(c)}</div>')
        html_out.append("</div>")
        return "".join(html_out)

    return ""
