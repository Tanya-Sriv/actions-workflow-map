from actions_workflow_map.matrix_analysis import parse_matrix


def test_estimates_literal_matrix() -> None:
    model = parse_matrix({"os": ["linux", "windows"], "python": ["3.11", "3.12"]})
    assert model is not None
    assert model.estimated_expansion == 4


def test_applies_include_and_exclude() -> None:
    model = parse_matrix(
        {
            "os": ["linux", "windows"],
            "python": ["3.11", "3.12"],
            "exclude": [{"os": "windows", "python": "3.11"}],
            "include": [{"os": "macos", "python": "3.12"}],
        }
    )
    assert model is not None
    assert model.estimated_expansion == 4


def test_expression_matrix_is_unresolved() -> None:
    model = parse_matrix({"os": "${{ fromJSON(inputs.os) }}"})
    assert model is not None
    assert model.estimated_expansion is None
    assert model.has_unresolved_expressions
