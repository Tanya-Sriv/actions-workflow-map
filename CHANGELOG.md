# Changelog

## [0.2.1] - 2026-07-28

### Changed

- Added Zenodo deposit and software citation metadata.
- Added repository and release identifiers.
- No functional changes.

## [0.2.0] - 2026-07-28

### Added

- Repository-wide workflow discovery under `.github/workflows`
- Repository HTML, Mermaid, and JSON reports
- Individual reports for every parsed workflow in repository mode
- Local reusable workflow resolution and `workflow_call` validation
- Workflow- and job-level concurrency extraction
- Shared static concurrency-group findings
- Workflow permission inheritance and job permission-expansion findings
- Matrix `include`, `exclude`, and estimated-expansion analysis
- Graceful continuation after malformed workflow files
- Repository demonstration fixture and CI smoke test

### Changed

- CLI accepts either a workflow YAML file or repository directory
- Package version updated to `0.2.0`

## [0.1.0] - 2026-07-27

### Added

- Initial single-workflow Mermaid, HTML, JSON, console, artifact-flow, and finding support
