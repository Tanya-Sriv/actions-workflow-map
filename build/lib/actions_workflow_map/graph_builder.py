from __future__ import annotations

from dataclasses import dataclass

from .models import WorkflowModel


@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    relationship: str
    label: str | None = None


def build_edges(model: WorkflowModel) -> list[GraphEdge]:
    edges: list[GraphEdge] = []
    for job in model.jobs.values():
        for dependency in job.needs:
            edges.append(GraphEdge(dependency, job.id, "needs"))
        if job.environment:
            env = job.environment.get("name") if isinstance(job.environment, dict) else job.environment
            edges.append(GraphEdge(job.id, f"environment:{env}", "deploys-to"))
    for artifact in model.artifacts:
        artifact_node = f"artifact:{artifact.name}"
        for producer in artifact.producers:
            edges.append(GraphEdge(producer, artifact_node, "produces"))
        for consumer in artifact.consumers:
            edges.append(GraphEdge(artifact_node, consumer, "consumes"))
    return edges
