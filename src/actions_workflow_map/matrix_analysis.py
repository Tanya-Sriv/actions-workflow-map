from __future__ import annotations

from itertools import product
from typing import Any

from .models import MatrixModel


def _contains_expression(value: Any) -> bool:
    if isinstance(value, str):
        return "${{" in value
    if isinstance(value, list):
        return any(_contains_expression(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_expression(item) for item in value.values())
    return False


def _matches(combination: dict[str, Any], pattern: dict[str, Any]) -> bool:
    return all(combination.get(key) == value for key, value in pattern.items())


def parse_matrix(raw_matrix: Any) -> MatrixModel | None:
    if raw_matrix in (None, {}):
        return None
    if not isinstance(raw_matrix, dict):
        return MatrixModel(has_unresolved_expressions=True)

    includes_raw = raw_matrix.get("include", []) or []
    excludes_raw = raw_matrix.get("exclude", []) or []
    includes = [dict(item) for item in includes_raw if isinstance(item, dict)]
    excludes = [dict(item) for item in excludes_raw if isinstance(item, dict)]

    dimensions: dict[str, list[Any]] = {}
    unresolved = _contains_expression(raw_matrix)
    for key, value in raw_matrix.items():
        if key in {"include", "exclude"}:
            continue
        if isinstance(value, list):
            dimensions[str(key)] = list(value)
        else:
            unresolved = True

    estimate: int | None = None
    if dimensions and not unresolved:
        keys = list(dimensions)
        combinations = [
            dict(zip(keys, values, strict=True))
            for values in product(*(dimensions[key] for key in keys))
        ]
        combinations = [
            combination
            for combination in combinations
            if not any(_matches(combination, exclusion) for exclusion in excludes)
        ]
        estimate = len(combinations) + len(includes)

    return MatrixModel(
        dimensions=dimensions,
        includes=includes,
        excludes=excludes,
        estimated_expansion=estimate,
        has_unresolved_expressions=unresolved,
    )
