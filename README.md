# Actions Workflow Map

Turn complex GitHub Actions YAML into a clear visual and machine-readable operational map.

## What v0.1.0 does

- Parses one local workflow file.
- Maps triggers, jobs, `needs`, runners, conditions, matrices, environments, permissions, action references, and basic concurrency metadata.
- Links literal `upload-artifact` producers and `download-artifact` consumers.
- Generates Mermaid, HTML, JSON, and a console summary.
- Emits evidence-linked deterministic review findings: WF101, WF201, WF301, WF302, WF401, and WF501.

The tool maps declared configuration. It does not fully simulate GitHub Actions runtime behavior and does not replace GitHub validation, actionlint, or security scanners.

## Five-minute quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
actions-workflow-map examples/matrix-artifact.yml
```

Outputs are written to `workflow-map/`:

- `workflow-map.mmd`
- `workflow-map.html`
- `workflow-report.json`

Choose a directory with:

```bash
actions-workflow-map .github/workflows/ci.yml --output build/workflow-map
```

## Development

```bash
python -m pip install -e .[dev]
ruff check .
pytest -q
```

## Phase 1 limitations

Literal values are mapped conservatively. Dynamic expressions, cross-workflow execution, reusable-workflow internals, implicit artifact transfer, outputs, and complete condition evaluation are not resolved. See [docs/limitations.md](docs/limitations.md).

## Privacy

Local-first: workflow contents are not uploaded by this package.

## License

MIT
