from __future__ import annotations

from dataclasses import dataclass

from .models import RepositoryModel


@dataclass(slots=True, frozen=True)
class RepositoryEdge:
    source: str
    target: str
    relationship: str


def workflow_node(path: str) -> str:
    return f"workflow::{path}"


def job_node(path: str, job_id: str) -> str:
    return f"job::{path}::{job_id}"


def build_repository_edges(repository: RepositoryModel) -> list[RepositoryEdge]:
    edges: list[RepositoryEdge] = []
    for workflow in repository.workflows:
        path = repository.relative_path(workflow.source_path)
        edges.append(RepositoryEdge("repository", workflow_node(path), "contains"))
        for job in workflow.jobs.values():
            current = job_node(path, job.id)
            edges.append(RepositoryEdge(workflow_node(path), current, "contains"))
            for dependency in job.needs:
                edges.append(
                    RepositoryEdge(job_node(path, dependency), current, "needs")
                )
            if job.environment:
                environment = (
                    job.environment.get("name")
                    if isinstance(job.environment, dict)
                    else job.environment
                )
                edges.append(
                    RepositoryEdge(current, f"environment::{environment}", "deploys-to")
                )
            if job.concurrency_details and job.concurrency_details.group:
                edges.append(
                    RepositoryEdge(
                        current,
                        f"concurrency::{job.concurrency_details.group}",
                        "uses-concurrency",
                    )
                )
        if workflow.concurrency_details and workflow.concurrency_details.group:
            edges.append(
                RepositoryEdge(
                    workflow_node(path),
                    f"concurrency::{workflow.concurrency_details.group}",
                    "uses-concurrency",
                )
            )

    for reference in repository.reusable_workflow_references:
        source = job_node(reference.caller_workflow_path, reference.caller_job)
        if reference.target_workflow_path:
            target = workflow_node(reference.target_workflow_path)
        else:
            target = f"external::{reference.reference}"
        edges.append(RepositoryEdge(source, target, "calls"))

    return sorted(edges, key=lambda edge: (edge.source, edge.target, edge.relationship))
