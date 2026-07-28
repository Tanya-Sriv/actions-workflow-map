class WorkflowMapError(Exception):
    """Base exception for user-facing failures."""


class WorkflowParseError(WorkflowMapError):
    """Raised when workflow YAML cannot be parsed."""
