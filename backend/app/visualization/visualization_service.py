from dataclasses import dataclass
from enum import Enum
from typing import Any


class VisualizationType(str, Enum):
    KPI = "kpi"
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    HISTOGRAM = "histogram"
    TABLE = "table"


@dataclass(frozen=True)
class VisualizationResult:
    visualization_type: VisualizationType
    title: str
    x_axis: str | None
    y_axis: str | None
    data: list[dict[str, Any]]
    reason: str


NUMERIC_TYPES = (int, float)


def _is_numeric(value: Any) -> bool:
    return isinstance(value, NUMERIC_TYPES) and not isinstance(value, bool)


def _column_values(
    rows: list[dict[str, Any]],
    column: str,
) -> list[Any]:
    return [
        row[column]
        for row in rows
        if column in row and row[column] is not None
    ]


def _numeric_columns(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []

    columns = list(rows[0].keys())

    return [
        column
        for column in columns
        if any(
            _is_numeric(row.get(column))
            for row in rows
        )
    ]


def _categorical_columns(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []

    columns = list(rows[0].keys())

    return [
        column
        for column in columns
        if any(
            value is not None and not _is_numeric(value)
            for value in _column_values(rows, column)
        )
    ]


def _date_like_columns(rows: list[dict[str, Any]]) -> list[str]:
    """
    Detect columns that represent time/date dimensions.

    This includes both textual date columns and numeric year columns.
    """
    if not rows:
        return []

    columns = list(rows[0].keys())

    date_keywords = (
        "date",
        "year",
        "month",
        "time",
        "timestamp",
    )

    return [
        column
        for column in columns
        if any(
            keyword in column.lower()
            for keyword in date_keywords
        )
    ]


def _id_like_columns(rows: list[dict[str, Any]]) -> list[str]:
    """
    Detect numeric columns that represent categorical identifiers.

    Examples:
        department_id
        manager_id
        branch_id

    These values are technically numeric, but should be treated
    as categorical/grouping dimensions for visualization.
    """
    if not rows:
        return []

    columns = list(rows[0].keys())

    id_keywords = (
        "_id",
        "id",
    )

    return [
        column
        for column in columns
        if any(
            keyword in column.lower()
            for keyword in id_keywords
        )
    ]


class VisualizationService:

    def analyze(
        self,
        rows: list[dict[str, Any]],
        title: str = "Query Result",
    ) -> VisualizationResult:

        # ---------------------------------------------------------
        # 0. Empty result → TABLE
        # ---------------------------------------------------------
        if not rows:
            return VisualizationResult(
                visualization_type=VisualizationType.TABLE,
                title=title,
                x_axis=None,
                y_axis=None,
                data=[],
                reason="No data available; using table fallback.",
            )

        columns = list(rows[0].keys())

        numeric = _numeric_columns(rows)
        categorical = _categorical_columns(rows)
        date_like = _date_like_columns(rows)
        id_like = _id_like_columns(rows)

        # Numeric ID fields are technically numeric, but represent
        # categorical/grouping dimensions.
        categorical_for_chart = [
            column
            for column in columns
            if column in categorical or column in id_like
        ]

        # ---------------------------------------------------------
        # 1. Single numeric value → KPI
        # ---------------------------------------------------------
        if len(rows) == 1 and len(columns) == 1:
            value = rows[0].get(columns[0])

            if _is_numeric(value):
                return VisualizationResult(
                    visualization_type=VisualizationType.KPI,
                    title=title,
                    x_axis=None,
                    y_axis=columns[0],
                    data=rows,
                    reason=(
                        "Single numeric result is best represented "
                        "as a KPI."
                    ),
                )

        # ---------------------------------------------------------
        # 2. Single row with one categorical + one numeric → KPI
        # ---------------------------------------------------------
        if len(rows) == 1 and len(columns) == 2:

            chart_categorical = [
                column
                for column in categorical_for_chart
                if column not in date_like
            ]

            if (
                len(numeric) == 1
                and len(chart_categorical) == 1
            ):
                return VisualizationResult(
                    visualization_type=VisualizationType.KPI,
                    title=title,
                    x_axis=chart_categorical[0],
                    y_axis=numeric[0],
                    data=rows,
                    reason=(
                        "Single numeric metric is best represented "
                        "as a KPI."
                    ),
                )

        # ---------------------------------------------------------
        # 3. Date/year + numeric → LINE
        #
        # Checked before generic categorical charts because
        # joining_year is itself numeric.
        # ---------------------------------------------------------
        date_numeric = [
            column
            for column in date_like
            if column in numeric
        ]

        date_categorical = [
            column
            for column in date_like
            if column in categorical
        ]

        # Numeric year + numeric metric
        if date_numeric and numeric:

            y_candidates = [
                column
                for column in numeric
                if column != date_numeric[0]
            ]

            if len(y_candidates) == 1:
                return VisualizationResult(
                    visualization_type=VisualizationType.LINE,
                    title=title,
                    x_axis=date_numeric[0],
                    y_axis=y_candidates[0],
                    data=rows,
                    reason=(
                        "Date/year-based analytical data is suitable "
                        "for a line chart."
                    ),
                )

        # Textual date/time + numeric metric
        if date_categorical and numeric:

            non_date_numeric = [
                column
                for column in numeric
                if column not in date_like
            ]

            if len(non_date_numeric) == 1:
                return VisualizationResult(
                    visualization_type=VisualizationType.LINE,
                    title=title,
                    x_axis=date_categorical[0],
                    y_axis=non_date_numeric[0],
                    data=rows,
                    reason=(
                        "Date/time-based analytical data is suitable "
                        "for a line chart."
                    ),
                )

        # ---------------------------------------------------------
        # 4. Complex employee/detail result → TABLE
        #
        # Multiple dimensions or multiple metrics should not be
        # forced into a pie/bar chart.
        # ---------------------------------------------------------
        if len(columns) >= 3:
            return VisualizationResult(
                visualization_type=VisualizationType.TABLE,
                title=title,
                x_axis=None,
                y_axis=None,
                data=rows,
                reason=(
                    "Detailed multi-column result is best represented "
                    "as a table."
                ),
            )

        # ---------------------------------------------------------
        # 5. Categorical/group identifier + numeric metric
        #
        # Examples:
        # department_id + employee_count
        # department + employee_count
        # designation + average_salary
        # ---------------------------------------------------------
        if (
            len(rows) <= 12
            and len(categorical_for_chart) == 1
        ):
            x_axis = categorical_for_chart[0]

            y_candidates = [
                column
                for column in numeric
                if column != x_axis
            ]

            if len(y_candidates) == 1:
                y_axis = y_candidates[0]

                # Numeric identifier dimensions such as
                # department_id are categorical comparisons.
                # Prefer BAR for clear comparison.
                if x_axis in id_like:
                    return VisualizationResult(
                        visualization_type=VisualizationType.BAR,
                        title=title,
                        x_axis=x_axis,
                        y_axis=y_axis,
                        data=rows,
                        reason=(
                            "Identifier-based categorical comparison "
                            "is suitable for a bar chart."
                        ),
                    )

                # Small textual categorical distribution → PIE
                if len(rows) <= 4:
                    return VisualizationResult(
                        visualization_type=VisualizationType.PIE,
                        title=title,
                        x_axis=x_axis,
                        y_axis=y_axis,
                        data=rows,
                        reason=(
                            "Small categorical distribution is suitable "
                            "for a pie chart."
                        ),
                    )

                # Larger categorical comparison → BAR
                return VisualizationResult(
                    visualization_type=VisualizationType.BAR,
                    title=title,
                    x_axis=x_axis,
                    y_axis=y_axis,
                    data=rows,
                    reason=(
                        "Categorical values with a numeric metric are "
                        "suitable for a bar chart."
                    ),
                )

        # ---------------------------------------------------------
        # 6. Single numeric column with many rows → HISTOGRAM
        # ---------------------------------------------------------
        if len(numeric) == 1 and not categorical_for_chart:
            return VisualizationResult(
                visualization_type=VisualizationType.HISTOGRAM,
                title=title,
                x_axis=numeric[0],
                y_axis=None,
                data=rows,
                reason=(
                    "A numeric distribution is suitable for "
                    "a histogram."
                ),
            )

        # ---------------------------------------------------------
        # 7. Everything else → TABLE
        # ---------------------------------------------------------
        return VisualizationResult(
            visualization_type=VisualizationType.TABLE,
            title=title,
            x_axis=None,
            y_axis=None,
            data=rows,
            reason=(
                "Result structure is not suitable for a specialized "
                "chart; using table fallback."
            ),
        )


visualization_service = VisualizationService()