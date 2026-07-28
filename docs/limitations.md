# Known limitations

Version 0.1.0 does not perform GitHub expression evaluation, runtime simulation, output data-flow analysis, repository-wide discovery, remote reusable-workflow resolution, implicit artifact-name inference, matrix Cartesian expansion, branch-filter path analysis, or security auditing. The HTML report uses a CDN-hosted Mermaid module for browser rendering; the YAML itself is not transmitted by the Python tool, but opening the report may fetch the JavaScript dependency.
