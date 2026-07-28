from __future__ import annotations

from html import escape

from jinja2 import Template

from ..models import WorkflowModel

_TEMPLATE = Template("""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<style>body{font-family:system-ui,sans-serif;max-width:1200px;margin:auto;padding:2rem;color:#1f2937}code,pre{background:#f3f4f6}.card{border:1px solid #d1d5db;border-radius:10px;padding:1rem;margin:1rem 0}.warning{border-left:5px solid #b45309}.info{border-left:5px solid #2563eb}.muted{color:#6b7280}.mermaid{overflow:auto}</style>
<script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'; mermaid.initialize({startOnLoad:true,securityLevel:'strict'});</script>
</head><body>
<h1>{{ title }}</h1><p class="muted">Declared configuration map for {{ source }}</p>
<div class="card"><div class="mermaid">{{ mermaid }}</div></div>
<h2>Summary</h2><div class="card"><p><strong>Jobs:</strong> {{ jobs }}</p><p><strong>Artifacts:</strong> {{ artifacts }}</p><p><strong>Findings:</strong> {{ findings|length }}</p></div>
<h2>Findings</h2>
{% if findings %}{% for f in findings %}<div class="card {{ f.severity }}"><strong>{{ f.rule_id }} — {{ f.title }}</strong><p>{{ f.evidence }}</p>{% if f.remediation %}<p><strong>Suggested review:</strong> {{ f.remediation }}</p>{% endif %}{% if f.limitation %}<p class="muted">Limitation: {{ f.limitation }}</p>{% endif %}</div>{% endfor %}{% else %}<p>No Phase 1 findings.</p>{% endif %}
<h2>Boundary</h2><p>This report maps declared YAML configuration. It does not simulate all runtime behavior or replace GitHub validation, actionlint, or security scanners.</p>
</body></html>""")


def render_html(model: WorkflowModel, mermaid: str) -> str:
    return _TEMPLATE.render(title=escape(model.name or "Actions Workflow Map"), source=escape(model.source_path), mermaid=escape(mermaid), jobs=len(model.jobs), artifacts=len(model.artifacts), findings=model.findings)
