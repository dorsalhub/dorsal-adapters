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

import logging
from typing import Any, cast

from dorsal_adapters.common.constants import OpenSchemaName

logger = logging.getLogger(__name__)

OTHER_SCHEMAS = {"dorsal/arxiv"}


def validate_record(record: dict[str, Any], schema_id: OpenSchemaName | str, version: str | None = None) -> None:
    """Validate a single record against a validation schema."""
    try:
        from dorsal.file.validators.open_schema import get_open_schema_validator
    except ImportError as e:
        raise ImportError("For auto-validation please pip install 'dorsalhub'.") from e

    if schema_id in OTHER_SCHEMAS:
        from dorsal.common.validators.json_schema import get_json_schema_validator
        from dorsal.api.dataset import get_dataset_schema

        schema = get_dataset_schema(schema_id)
        validator = get_json_schema_validator(schema=schema, strict=True)
    else:
        kwargs = {"version": version} if version else {}
        validator = get_open_schema_validator(cast(OpenSchemaName, schema_id), **kwargs)

    validator.validate(record)
