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

import ast
import re
import subprocess
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "dorsal_adapters"


def _canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _declared_dependencies() -> set[str]:
    with open(ROOT / "pyproject.toml", "rb") as f:
        project = tomllib.load(f)["project"]
    return {_canonical(re.split(r"[\s<>=!~;\[]", dep, maxsplit=1)[0]) for dep in project["dependencies"]}


def _module_level_imports(path: Path) -> set[str]:
    names = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_module_level_imports_are_declared_dependencies():
    """Every third-party package imported at module level is a declared runtime dependency."""
    declared = _declared_dependencies()
    distributions = packages_distributions()

    undeclared = {}
    for path in PACKAGE.rglob("*.py"):
        for name in _module_level_imports(path):
            if name in sys.stdlib_module_names or name == "dorsal_adapters":
                continue
            providers = {_canonical(d) for d in distributions.get(name, [])}
            if not providers & declared:
                undeclared[f"{path.relative_to(ROOT)}: {name}"] = sorted(providers)

    assert not undeclared


def test_adapters_import_and_export_without_dorsal():
    """Every adapter module imports, and exports with validate=False, when dorsalhub isn't installed."""
    script = """
import importlib
import sys

sys.modules["dorsal"] = None

from dorsal_adapters.registry import _REGISTRY, get_adapter

for _, module_path, *_ in _REGISTRY.values():
    importlib.import_module(module_path)

record = {"track_id": 1, "segments": [{"start_time": 0.5, "end_time": 1.5, "text": "Hello"}]}
print(get_adapter("audio-transcription", "srt").export(record, validate=False))
"""
    result = subprocess.run([sys.executable, "-I", "-c", script], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert "Hello" in result.stdout
