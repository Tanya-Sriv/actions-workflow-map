from __future__ import annotations

import re
from pathlib import Path

from ..models import RepositoryModel
from ..repository_graph import build_repository_edges, job_node, workflow_node


def _id(value: str) -> str:
    return "node_" + re.sub(r"[^A-Za-z0-9_]", "_", value)


def _text(value: object) -> str:
    return str(value).replace('"', "'").replace("\n", " ")


def render_repository_mermaid(repository: RepositoryModel) -> str:
    lines = ["flowchart TD", '  repository["repository"]']

    for workflow in sorted(
        repository.workflows,
        key=lambda item: repository.relative_path(item.source_path),
    ):
        path = repository.relative_path(workflow.source_path)
        workflow_id = _id(workflow_node(path))
        subgraph_id = _id(f"subgraph::{path}")
        lines.append(f'  subgraph {subgraph_id}["{_text(path)}"]')
        lines.append(
            f'    {workflow_id}["{_text(workflow.name or Path(path).name)}"]'
        )
        for job in sorted(workflow.jobs.values(), key=lambda item: item.id):
            details = [job.name or job.id]
            if job.matrix_details and job.matrix_details.estimated_expansion is not None:
                details.append(
                    f"matrix≈{job.matrix_details.estimated_expansion}"
                )
            if job.environment:
                details.append(f"env={_text(job.environment)}")
            label = "<br/>".join(_text(part) for part in details)
            lines.append(f'    {_id(job_node(path, job.id))}["{label}"]')
        lines.append("  end")

    declared_nodes: set[str] = {"repository"}
    for edge in build_repository_edges(repository):
        for node in (edge.source, edge.target):
            node_id = _id(node)
            if node_id in declared_nodes:
                continue
            if node.startswith("environment::"):
                label = node.removeprefix("environment::")
                lines.append(f'  {node_id}(["environment: {_text(label)}"])')
            elif node.startswith("concurrency::"):
                label = node.removeprefix("concurrency::")
                lines.append(f'  {node_id}{{{{"concurrency: {_text(label)}"}}}}')
            elif node.startswith("external::"):
                label = node.removeprefix("external::")
                lines.append(f'  {node_id}[["external: {_text(label)}"]]')
            declared_nodes.add(node_id)
        lines.append(
            f"  {_id(edge.source)} -->|{edge.relationship}| {_id(edge.target)}"
        )

    return "\n".join(dict.fromkeys(lines)) + "\n"
