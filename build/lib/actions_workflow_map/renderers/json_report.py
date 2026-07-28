from __future__ import annotations

import json

from ..models import WorkflowModel


def render_json(model: WorkflowModel) -> str:
    return json.dumps(model.to_dict(), indent=2, sort_keys=True, default=str) + "\n"
