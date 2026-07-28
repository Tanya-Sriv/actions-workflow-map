from pathlib import Path

from actions_workflow_map.models import JobModel, RepositoryModel, WorkflowModel
from actions_workflow_map.reusable_workflows import resolve_reusable_workflows


def _workflow(path: Path, uses: str | None = None) -> WorkflowModel:
    return WorkflowModel(
        name=path.stem,
        source_path=str(path.resolve()),
        triggers={"workflow_call": None},
        permissions=None,
        concurrency=None,
        jobs={"call": JobModel(id="call", uses=uses)},
    )


def test_resolves_local_reference(tmp_path: Path) -> None:
    caller = tmp_path / ".github" / "workflows" / "caller.yml"
    target = tmp_path / ".github" / "workflows" / "target.yml"
    target.parent.mkdir(parents=True)
    caller.touch()
    target.touch()
    repository = RepositoryModel(
        root=tmp_path,
        workflows=[_workflow(caller, "./.github/workflows/target.yml"), _workflow(target)],
    )
    refs = resolve_reusable_workflows(repository)
    assert refs[0].is_resolved
    assert refs[0].target_workflow_path == ".github/workflows/target.yml"


def test_records_remote_reference(tmp_path: Path) -> None:
    caller = tmp_path / ".github" / "workflows" / "caller.yml"
    caller.parent.mkdir(parents=True)
    caller.touch()
    repository = RepositoryModel(
        root=tmp_path,
        workflows=[_workflow(caller, "org/repo/.github/workflows/build.yml@v1")],
    )
    refs = resolve_reusable_workflows(repository)
    assert not refs[0].is_local


def test_detects_escape(tmp_path: Path) -> None:
    caller = tmp_path / ".github" / "workflows" / "caller.yml"
    caller.parent.mkdir(parents=True)
    caller.touch()
    repository = RepositoryModel(
        root=tmp_path,
        workflows=[_workflow(caller, "./../outside.yml")],
    )
    refs = resolve_reusable_workflows(repository)
    assert refs[0].escapes_repository
