from __future__ import annotations

import json

from ..models import RepositoryModel


def render_repository_json(repository: RepositoryModel) -> str:
    payload = repository.to_dict()
    for workflow in payload["workflows"]:
        workflow["source_path"] = repository.relative_path(workflow["source_path"])
    return json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
