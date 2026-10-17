import pytest

from app.visualization.visualization_service import (
    VisualizationType,
    visualization_service,
)


def test_single_numeric_result_selects_kpi():
    rows = [
        {"employee_count": 45}
    ]

    result = visualization_service.analyze(
        rows,
        "Employee Count",
    )

    assert result.visualization_type == VisualizationType.KPI
    assert result.y_axis == "employee_count"
    assert result.data == rows


def test_small_categorical_result_selects_pie():
    rows = [
        {"department": "IT", "employee_count": 10},
        {"department": "HR", "employee_count": 5},
        {"department": "Finance", "employee_count": 7},
    ]

    result = visualization_service.analyze(
        rows,
        "Employees by Department",
    )

    assert result.visualization_type == VisualizationType.PIE
    assert result.x_axis == "department"
    assert result.y_axis == "employee_count"


def test_large_categorical_result_selects_bar():
    rows = [
        {"department": "IT", "employee_count": 10},
        {"department": "HR", "employee_count": 5},
        {"department": "Finance", "employee_count": 7},
        {"department": "Sales", "employee_count": 8},
        {"department": "Admin", "employee_count": 4},
        {"department": "Support", "employee_count": 6},
        {"department": "Legal", "employee_count": 3},
    ]

    result = visualization_service.analyze(
        rows,
        "Employees by Department",
    )

    assert result.visualization_type == VisualizationType.BAR
    assert result.x_axis == "department"
    assert result.y_axis == "employee_count"


def test_yearly_analysis_selects_line():
    rows = [
        {"joining_year": 2024, "employee_count": 10},
        {"joining_year": 2025, "employee_count": 15},
        {"joining_year": 2026, "employee_count": 20},
    ]

    result = visualization_service.analyze(
        rows,
        "Employees Joined by Year",
    )

    assert result.visualization_type == VisualizationType.LINE
    assert result.x_axis == "joining_year"
    assert result.y_axis == "employee_count"


def test_numeric_distribution_selects_histogram():
    rows = [
        {"salary": 30000},
        {"salary": 35000},
        {"salary": 40000},
        {"salary": 45000},
        {"salary": 50000},
    ]

    result = visualization_service.analyze(
        rows,
        "Salary Distribution",
    )

    assert result.visualization_type == VisualizationType.HISTOGRAM
    assert result.x_axis == "salary"
    assert result.y_axis is None


def test_complex_detail_result_uses_table():
    rows = [
        {
            "employee_id": "EMP001",
            "name": "Alice",
            "salary": 50000,
        },
        {
            "employee_id": "EMP002",
            "name": "Bob",
            "salary": 60000,
        },
    ]

    result = visualization_service.analyze(
        rows,
        "Employee Details",
    )

    assert result.visualization_type == VisualizationType.TABLE
    assert result.x_axis is None
    assert result.y_axis is None


def test_empty_result_uses_table():
    result = visualization_service.analyze(
        [],
        "Empty Result",
    )

    assert result.visualization_type == VisualizationType.TABLE
    assert result.data == []


def test_visualization_preserves_result_data():
    rows = [
        {"department": "IT", "employee_count": 10},
        {"department": "HR", "employee_count": 5},
    ]

    result = visualization_service.analyze(
        rows,
        "Employees",
    )

    assert result.data == rows


def test_visualization_does_not_create_new_fields():
    rows = [
        {"department": "IT", "employee_count": 10},
        {"department": "HR", "employee_count": 5},
    ]

    result = visualization_service.analyze(
        rows,
        "Employees",
    )

    source_fields = set(rows[0].keys())
    result_fields = set(result.data[0].keys())

    assert result_fields == source_fields