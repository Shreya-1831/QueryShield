from app.visualization.visualization_service import (
    VisualizationType,
    visualization_service,
)


def test_kpi_from_safe_analytics_result():
    rows = [
        {"employee_count": 45}
    ]

    result = visualization_service.analyze(
        rows,
        "Employee Count",
    )

    assert result.visualization_type == VisualizationType.KPI
    assert result.data == rows


def test_pie_from_safe_grouped_result():
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


def test_bar_from_safe_grouped_result():
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
    assert result.data == rows


def test_line_from_date_analysis_result():
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


def test_histogram_from_safe_numeric_result():
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


def test_table_fallback_for_detail_result():
    rows = [
        {
            "employee_id": "EMP001",
            "name": "Employee 1",
            "salary": 50000,
        },
        {
            "employee_id": "EMP002",
            "name": "Employee 2",
            "salary": 60000,
        },
    ]

    result = visualization_service.analyze(
        rows,
        "Employee Details",
    )

    assert result.visualization_type == VisualizationType.TABLE


def test_empty_safe_result_uses_table():
    result = visualization_service.analyze(
        [],
        "No Results",
    )

    assert result.visualization_type == VisualizationType.TABLE
    assert result.data == []


def test_removed_privacy_field_never_reaches_visualization():
    """
    Simulate the result AFTER privacy protection.

    salary was removed by the privacy layer, so visualization
    must only receive the remaining authorized fields.
    """
    safe_rows = [
        {
            "department": "IT",
            "employee_count": 10,
        },
        {
            "department": "HR",
            "employee_count": 5,
        },
    ]

    result = visualization_service.analyze(
        safe_rows,
        "Employees by Department",
    )

    assert result.visualization_type == VisualizationType.PIE

    for row in result.data:
        assert "salary" not in row


def test_unauthorized_field_never_reaches_chart_data():
    """
    Visualization must operate only on the already-authorized
    result supplied to it.
    """
    safe_rows = [
        {
            "department": "IT",
            "employee_count": 10,
        },
        {
            "department": "HR",
            "employee_count": 5,
        },
    ]

    result = visualization_service.analyze(
        safe_rows,
        "Employees by Department",
    )

    fields = set(result.data[0].keys())

    assert "department" in fields
    assert "employee_count" in fields
    assert "salary" not in fields
    assert "phone" not in fields
    assert "address" not in fields


def test_visualization_does_not_invent_unauthorized_fields():
    rows = [
        {
            "department": "IT",
            "employee_count": 10,
        },
        {
            "department": "HR",
            "employee_count": 5,
        },
    ]

    result = visualization_service.analyze(
        rows,
        "Employees by Department",
    )

    source_fields = set(rows[0].keys())
    result_fields = set(result.data[0].keys())

    assert result_fields.issubset(source_fields)