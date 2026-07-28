from pathlib import Path


WORKFLOW_EXTENSIONS = {".yml", ".yaml"}


class WorkflowDiscoveryError(Exception):
    """Raised when repository workflow discovery cannot be completed."""


def discover_workflow_files(repository_root: Path) -> list[Path]:
    root = repository_root.resolve()

    if not root.exists():
        raise WorkflowDiscoveryError(f"Path does not exist: {root}")

    if not root.is_dir():
        raise WorkflowDiscoveryError(
            f"Repository path is not a directory: {root}"
        )

    workflow_directory = root / ".github" / "workflows"

    if not workflow_directory.exists():
        return []

    if not workflow_directory.is_dir():
        raise WorkflowDiscoveryError(
            f"Workflow path is not a directory: {workflow_directory}"
        )

    workflow_files = [
        path.resolve()
        for path in workflow_directory.iterdir()
        if path.is_file()
        and path.suffix.lower() in WORKFLOW_EXTENSIONS
    ]

    return sorted(workflow_files)