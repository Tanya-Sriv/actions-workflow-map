# Rule catalog

- **WF101** Missing declared dependency: a literal artifact consumer has no direct `needs` link to a visible producer.
- **WF201** Broad write permissions: `write-all`, or three or more explicitly writable scopes.
- **WF301** Artifact consumer without visible producer.
- **WF302** Artifact producer without visible consumer (informational).
- **WF401** Job has no `timeout-minutes`.
- **WF501** External action reference is not pinned to a 40-character commit SHA.

These are review signals, not proof of runtime failure or a complete security audit.

### WF101 — Missing declared dependency

**Limitation:** Static matching uses literal artifact names and direct
`needs` relationships only.
