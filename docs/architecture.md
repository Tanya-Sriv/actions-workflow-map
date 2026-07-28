# Architecture

The package separates four concerns: YAML parsing into an explicit intermediate model, artifact extraction and graph construction, deterministic rule evaluation, and independent renderers. This keeps findings inspectable and allows unsupported expressions to remain unresolved rather than guessed.
