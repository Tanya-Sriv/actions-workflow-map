from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .artifact_flow import extract_artifacts
from .discovery import WorkflowDiscoveryError
from .errors import WorkflowMapError
from .parser import parse_workflow
from .renderers import render_html, render_json, render_mermaid
from .repository_parser import parse_repository
from .rules import run_rules

app = typer.Typer(
    help=(
        "Turn GitHub Actions YAML into a visual operational map."
    )
)

DEFAULT_OUTPUT_DIR = Path("workflow-map")
WORKFLOW_EXTENSIONS = {".yml", ".yaml"}


def run_single_workflow(
    workflow_path: Path,
    output: Path,
) -> None:
    """Analyze one GitHub Actions workflow file."""
    model = parse_workflow(workflow_path)

    extract_artifacts(model)
    run_rules(model)

    mermaid = render_mermaid(model)

    output.mkdir(parents=True, exist_ok=True)

    mermaid_path = output / "workflow-map.mmd"
    html_path = output / "workflow-map.html"
    json_path = output / "workflow-report.json"

    mermaid_path.write_text(
        mermaid,
        encoding="utf-8",
    )

    html_path.write_text(
        render_html(model, mermaid),
        encoding="utf-8",
    )

    json_path.write_text(
        render_json(model),
        encoding="utf-8",
    )

    edge_count = sum(
        len(job.needs)
        for job in model.jobs.values()
    )

    matrix_jobs = sum(
        bool(job.matrix)
        for job in model.jobs.values()
    )

    typer.echo(
        f"Workflow: {model.name or workflow_path.name}"
    )

    typer.echo(
        f"Jobs: {len(model.jobs)}"
        f" | needs edges: {edge_count}"
        f" | matrix jobs: {matrix_jobs}"
    )

    typer.echo(
        f"Artifacts: {len(model.artifacts)}"
        f" | findings: {len(model.findings)}"
    )

    for finding in model.findings:
        typer.echo(
            f"[{finding.severity.upper()}] "
            f"{finding.rule_id}: "
            f"{finding.title} — "
            f"{finding.evidence}"
        )

    typer.echo(
        f"Reports written to: {output.resolve()}"
    )


def run_repository(
    repository_path: Path,
    output: Path,
) -> None:
    """Discover and parse workflows in a repository."""
    repository = parse_repository(repository_path)

    typer.echo(
        "Actions Workflow Map — Repository Analysis"
    )
    typer.echo(f"Repository: {repository.root}")
    typer.echo(
        f"Workflows discovered: {len(repository.workflows)}"
    )
    typer.echo(
        f"Parse findings: {len(repository.findings)}"
    )

    if repository.findings:
        typer.echo("")
        typer.echo("Repository findings:")

        for finding in repository.findings:
            typer.echo(
                f"[{finding.severity.upper()}] "
                f"{finding.rule_id}: "
                f"{finding.title} — "
                f"{finding.evidence}"
            )

    if not repository.workflows:
        typer.echo(
            "No GitHub Actions workflow files were found "
            "under .github/workflows."
        )
        return

    output.mkdir(parents=True, exist_ok=True)

    typer.echo("")
    typer.echo("Parsed workflows:")

    for workflow in repository.workflows:
        typer.echo(f"  - {workflow.source_path}")

    typer.echo("")
    typer.echo(
        "Repository discovery completed successfully."
    )
    typer.echo(
        "Repository-level report generation will be "
        "added in the next implementation step."
    )


@app.command()
def main(
    source: Annotated[
        Path,
        typer.Argument(
            exists=True,
            readable=True,
            help=(
                "GitHub Actions workflow file or "
                "repository directory"
            ),
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output directory",
        ),
    ] = DEFAULT_OUTPUT_DIR,
) -> None:
    """Analyze one workflow file or an entire repository."""
    try:
        if source.is_file():
            if source.suffix.lower() not in WORKFLOW_EXTENSIONS:
                raise typer.BadParameter(
                    "Workflow file must use a "
                    ".yml or .yaml extension."
                )

            run_single_workflow(
                workflow_path=source,
                output=output,
            )
            return

        if source.is_dir():
            run_repository(
                repository_path=source,
                output=output,
            )
            return

        raise typer.BadParameter(
            "Input must be a workflow YAML file "
            "or repository directory."
        )

    except typer.BadParameter:
        raise

    except WorkflowDiscoveryError as exc:
        typer.echo(
            f"Repository discovery error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc

    except WorkflowMapError as exc:
        typer.echo(
            f"Error: {exc}",
            err=True,
        )
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    app()