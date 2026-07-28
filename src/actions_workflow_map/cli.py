from __future__ import annotations

from pathlib import Path

import typer

from .artifact_flow import extract_artifacts
from .errors import WorkflowMapError
from .parser import parse_workflow
from .renderers import render_html, render_json, render_mermaid
from .rules import run_rules

app = typer.Typer(help="Turn GitHub Actions YAML into a visual operational map.")


@app.command()
def main(
    workflow: Path = typer.Argument(..., exists=True, readable=True, help="Local .yml or .yaml workflow file"),
    output: Path = typer.Option(Path("workflow-map"), "--output", "-o", help="Output directory"),
) -> None:
    try:
        model = parse_workflow(workflow)
        extract_artifacts(model)
        run_rules(model)
        mermaid = render_mermaid(model)
        output.mkdir(parents=True, exist_ok=True)
        (output / "workflow-map.mmd").write_text(mermaid, encoding="utf-8")
        (output / "workflow-map.html").write_text(render_html(model, mermaid), encoding="utf-8")
        (output / "workflow-report.json").write_text(render_json(model), encoding="utf-8")
    except WorkflowMapError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    edge_count = sum(len(job.needs) for job in model.jobs.values())
    matrix_jobs = sum(bool(job.matrix) for job in model.jobs.values())
    typer.echo(f"Workflow: {model.name or workflow.name}")
    typer.echo(f"Jobs: {len(model.jobs)} | needs edges: {edge_count} | matrix jobs: {matrix_jobs}")
    typer.echo(f"Artifacts: {len(model.artifacts)} | findings: {len(model.findings)}")
    for finding in model.findings:
        typer.echo(f"[{finding.severity.upper()}] {finding.rule_id}: {finding.title} — {finding.evidence}")
    typer.echo(f"Reports written to: {output.resolve()}")


if __name__ == "__main__":
    app()
