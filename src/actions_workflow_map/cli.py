from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .artifact_flow import extract_artifacts
from .discovery import WorkflowDiscoveryError
from .errors import WorkflowMapError
from .parser import parse_workflow
from .renderers import (
    render_html,
    render_json,
    render_mermaid,
    render_repository_html,
    render_repository_json,
    render_repository_mermaid,
)
from .repository_parser import parse_repository
from .rules import run_rules

app = typer.Typer(help="Turn GitHub Actions YAML into a visual operational map.")
DEFAULT_OUTPUT_DIR = Path("workflow-map")
WORKFLOW_EXTENSIONS = {".yml", ".yaml"}


def _workflow_slug(path: str | Path) -> str:
    stem = Path(path).stem
    return "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in stem
    )


def _write_single_workflow_outputs(model: object, output: Path) -> None:
    mermaid = render_mermaid(model)
    output.mkdir(parents=True, exist_ok=True)
    (output / "workflow-map.mmd").write_text(mermaid, encoding="utf-8")
    (output / "workflow-map.html").write_text(
        render_html(model, mermaid),
        encoding="utf-8",
    )
    (output / "workflow-report.json").write_text(
        render_json(model),
        encoding="utf-8",
    )


def run_single_workflow(workflow_path: Path, output: Path) -> None:
    model = parse_workflow(workflow_path)
    extract_artifacts(model)
    run_rules(model)
    _write_single_workflow_outputs(model, output)

    edge_count = sum(len(job.needs) for job in model.jobs.values())
    matrix_jobs = sum(bool(job.matrix) for job in model.jobs.values())
    typer.echo(f"Workflow: {model.name or workflow_path.name}")
    typer.echo(
        f"Jobs: {len(model.jobs)} | needs edges: {edge_count} "
        f"| matrix jobs: {matrix_jobs}"
    )
    typer.echo(
        f"Artifacts: {len(model.artifacts)} | findings: {len(model.findings)}"
    )
    for finding in model.findings:
        typer.echo(
            f"[{finding.severity.upper()}] {finding.rule_id}: "
            f"{finding.title} — {finding.evidence}"
        )
    typer.echo(f"Reports written to: {output.resolve()}")


def run_repository(repository_path: Path, output: Path) -> None:
    repository = parse_repository(repository_path)
    output.mkdir(parents=True, exist_ok=True)

    for workflow in repository.workflows:
        workflow_output = output / "workflows" / _workflow_slug(workflow.source_path)
        _write_single_workflow_outputs(workflow, workflow_output)

    mermaid = render_repository_mermaid(repository)
    (output / "repository-map.mmd").write_text(mermaid, encoding="utf-8")
    (output / "repository-map.html").write_text(
        render_repository_html(repository, mermaid),
        encoding="utf-8",
    )
    (output / "repository-report.json").write_text(
        render_repository_json(repository),
        encoding="utf-8",
    )

    summary = repository.summary
    typer.echo("Actions Workflow Map — Repository Analysis")
    typer.echo(f"Repository: {repository.root}")
    typer.echo(f"Workflows parsed: {summary.workflow_count}")
    typer.echo(f"Workflow parse failures: {summary.parse_failure_count}")
    typer.echo(f"Jobs: {summary.job_count}")
    typer.echo(f"Dependencies: {summary.dependency_count}")
    typer.echo(f"Reusable workflow calls: {summary.reusable_workflow_count}")
    typer.echo(
        "Local reusable workflows resolved: "
        f"{summary.resolved_reusable_workflow_count}"
    )
    typer.echo(f"Matrix jobs: {summary.matrix_job_count}")
    typer.echo(
        "Estimated matrix executions: "
        f"{summary.estimated_matrix_executions}"
    )
    typer.echo(f"Concurrency groups: {summary.concurrency_group_count}")
    typer.echo(f"Findings: {summary.finding_count}")
    typer.echo(f"Reports written to: {output.resolve()}")


@app.command()
def main(
    source: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            help="GitHub Actions workflow file or repository directory",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output directory"),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """Analyze one workflow file or all workflows in a repository."""
    try:
        if source.is_file():
            if source.suffix.lower() not in WORKFLOW_EXTENSIONS:
                raise typer.BadParameter(
                    "Workflow file must use a .yml or .yaml extension."
                )
            run_single_workflow(source, output)
            return
        if source.is_dir():
            run_repository(source, output)
            return
        raise typer.BadParameter(
            "Input must be a workflow YAML file or repository directory."
        )
    except typer.BadParameter:
        raise
    except WorkflowDiscoveryError as exc:
        typer.echo(f"Repository discovery error: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except WorkflowMapError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    app()