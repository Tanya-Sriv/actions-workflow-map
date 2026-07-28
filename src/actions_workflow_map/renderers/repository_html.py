from __future__ import annotations

from html import escape
from pathlib import Path

from jinja2 import Template

from ..models import RepositoryModel

_TEMPLATE = Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Actions Workflow Map — Repository Analysis</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1400px;margin:auto;padding:2rem;color:#1f2937}
.card{border:1px solid #d1d5db;border-radius:10px;padding:1rem;margin:1rem 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}.metric{background:#f8fafc}
.warning{border-left:5px solid #b45309}.error{border-left:5px solid #b91c1c}.info{border-left:5px solid #2563eb}
.muted{color:#6b7280}.mermaid{overflow:auto}table{border-collapse:collapse;width:100%}th,td{border:1px solid #d1d5db;padding:.6rem;text-align:left}
code{background:#f3f4f6;padding:.1rem .3rem}
</style>
<script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'; mermaid.initialize({startOnLoad:true,securityLevel:'strict'});</script>
</head><body>
<h1>Actions Workflow Map — Repository Analysis</h1>
<p class="muted">Declared configuration map for {{ root }}</p>
<div class="grid">
{% for label, value in metrics %}<div class="card metric"><strong>{{ value }}</strong><br>{{ label }}</div>{% endfor %}
</div>
<div class="card"><div class="mermaid">{{ mermaid }}</div></div>
<h2>Workflows</h2>
<table><thead><tr><th>Workflow</th><th>Jobs</th><th>Findings</th><th>Report</th></tr></thead><tbody>
{% for item in workflows %}<tr><td><code>{{ item.path }}</code></td><td>{{ item.jobs }}</td><td>{{ item.findings }}</td><td><a href="{{ item.href }}">Open</a></td></tr>{% endfor %}
</tbody></table>
<h2>Reusable workflow references</h2>
{% if references %}<table><thead><tr><th>Caller</th><th>Reference</th><th>Status</th></tr></thead><tbody>
{% for ref in references %}<tr><td>{{ ref.caller }}</td><td><code>{{ ref.reference }}</code></td><td>{{ ref.status }}</td></tr>{% endfor %}
</tbody></table>{% else %}<p>No reusable workflow references were found.</p>{% endif %}
<h2>Findings</h2>
{% if findings %}{% for f in findings %}<div class="card {{ f.severity }}"><strong>{{ f.rule_id }} — {{ f.title }}</strong><p>{{ f.evidence }}</p>{% if f.remediation %}<p><strong>Suggested review:</strong> {{ f.remediation }}</p>{% endif %}{% if f.limitation %}<p class="muted">Limitation: {{ f.limitation }}</p>{% endif %}</div>{% endfor %}{% else %}<p>No repository findings.</p>{% endif %}
<h2>Boundary</h2><p>This report maps declared YAML configuration. It does not simulate GitHub Actions runtime behavior, evaluate every expression, or download remote reusable workflows.</p>
</body></html>""")


def _slug(path: str) -> str:
    stem = Path(path).stem
    return "".join(character if character.isalnum() or character in "-_" else "-" for character in stem)


def render_repository_html(repository: RepositoryModel, mermaid: str) -> str:
    summary = repository.summary
    metrics = [
        ("Workflows", summary.workflow_count),
        ("Jobs", summary.job_count),
        ("Dependencies", summary.dependency_count),
        ("Reusable calls", summary.reusable_workflow_count),
        ("Matrix jobs", summary.matrix_job_count),
        ("Estimated matrix executions", summary.estimated_matrix_executions),
        ("Concurrency groups", summary.concurrency_group_count),
        ("Findings", summary.finding_count),
    ]
    workflows = []
    for workflow in sorted(
        repository.workflows,
        key=lambda item: repository.relative_path(item.source_path),
    ):
        path = repository.relative_path(workflow.source_path)
        workflows.append(
            {
                "path": escape(path),
                "jobs": len(workflow.jobs),
                "findings": len(workflow.findings),
                "href": f"workflows/{_slug(path)}/workflow-map.html",
            }
        )
    references = []
    for reference in repository.reusable_workflow_references:
        if reference.escapes_repository:
            status = "escapes repository"
        elif reference.is_resolved:
            status = f"resolved: {reference.target_workflow_path}"
        elif reference.is_local:
            status = "local target not found"
        else:
            status = "external reference"
        references.append(
            {
                "caller": escape(
                    f"{reference.caller_workflow_path}::jobs.{reference.caller_job}"
                ),
                "reference": escape(reference.reference),
                "status": escape(status),
            }
        )
    return _TEMPLATE.render(
        root=".",
        metrics=metrics,
        mermaid=escape(mermaid),
        workflows=workflows,
        references=references,
        findings=repository.findings,
    )
