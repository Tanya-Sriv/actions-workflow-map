from __future__ import annotations

import re
from typing import Any

from ..graph_builder import build_edges
from ..models import WorkflowModel


def _id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def _text(value: Any) -> str:
    return str(value).replace('"', "'").replace("\n", " ")


def render_mermaid(model: WorkflowModel) -> str:
    lines = ["flowchart TD"]
    if isinstance(model.triggers, list):
        trigger_values = model.triggers
    elif isinstance(model.triggers, dict):
        trigger_values = list(model.triggers.keys())
    else:
        trigger_values = [model.triggers]

    for trigger in trigger_values:
        node = f"trigger_{_id(str(trigger))}"
        lines.append(f'  {node}(["trigger: {_text(trigger)}"])')
        for job in model.jobs.values():
            if not job.needs:
                lines.append(f"  {node} --> {_id(job.id)}")

    for job in model.jobs.values():
        details = [job.name or job.id]
        if job.runs_on:
            details.append(f"runner: {_text(job.runs_on)}")
        if job.matrix:
            dimensions = ", ".join(f"{k}={v}" for k, v in job.matrix.items())
            details.append(f"matrix: {_text(dimensions)}")
        if job.condition:
            details.append(f"if: {_text(job.condition)}")
        label = "<br/>".join(details)
        lines.append(f'  {_id(job.id)}["{label}"]')

    for edge in build_edges(model):
        source, target = _id(edge.source), _id(edge.target)
        if edge.source.startswith("artifact:"):
            label = edge.source.removeprefix("artifact:")
            lines.append(f'  {source}{{{{"artifact: {_text(label)}"}}}}')
        if edge.target.startswith("artifact:"):
            label = edge.target.removeprefix("artifact:")
            lines.append(f'  {target}{{{{"artifact: {_text(label)}"}}}}')
        if edge.target.startswith("environment:"):
            label = edge.target.removeprefix("environment:")
            lines.append(f'  {target}(["environment: {_text(label)}"])')
        lines.append(f"  {source} -->|{edge.relationship}| {target}")

    return "\n".join(dict.fromkeys(lines)) + "\n"
