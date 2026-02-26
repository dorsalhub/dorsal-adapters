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

import pytest
from dorsal_adapters.document.html_adapter.parser import from_html


def test_from_html_empty_content():
    """Ensure ingress fails gracefully on empty text."""
    with pytest.raises(ValueError, match="Provided HTML content is empty"):
        from_html("   \n  ", validate=False)


def test_from_html_conversion():
    """Test standard ingress from HTML string to Open Schema record."""
    html_input = "<html><body><h1>Title</h1><p>  Some   text \n here.  </p></body></html>"
    record = from_html(html_input, producer="test-parser", validate=False)

    assert record["producer"] == "test-parser"
    assert record["extraction_type"] == "text"
    assert len(record["blocks"]) == 1

    assert record["blocks"][0]["text"] == "Title Some text here."
    assert record["blocks"][0]["block_type"] == "text"


def test_from_html_validation():
    """Verify that auto-validation passes with a successfully parsed record."""
    html_input = "<p>Valid text</p>"

    record = from_html(html_input, validate=True)
    assert record["blocks"][0]["text"] == "Valid text"
