from typing import Any


class ResponseService:

    def generate(
        self,
        prompt: str,
        rows: list[dict[str, Any]],
        intent: str | None = None,
    ) -> str:

        if not rows:
            return "No results were found for your request."

        prompt_lower = prompt.lower()

        # ---------------------------------------------------------
        # 1. Single-row result
        # ---------------------------------------------------------
        if len(rows) == 1:
            row = rows[0]

            # Single-column result
            if len(row) == 1:
                column, value = next(iter(row.items()))

                if value is None:
                    return "No information was found for your request."

                column_lower = column.lower()

                # Count / employee count
                if (
                    "count" in column_lower
                    or "number" in column_lower
                    or column_lower.endswith("_count")
                ):
                    if (
                        "other employees" in prompt_lower
                        and (
                            "excluding me" in prompt_lower
                            or "excluding myself" in prompt_lower
                        )
                    ):
                        return (
                            f"There are {value} other employees in your "
                            "department, excluding you."
                        )

                    if "my department" in prompt_lower:
                        return (
                            f"There are {value} employees in your department."
                        )

                    if "department" in prompt_lower:
                        return (
                            f"There are {value} employees in the "
                            "requested department."
                        )

                    return (
                        f"There are {value} employees matching your request."
                    )

                # Department
                if "department" in column_lower:
                    return f"Your department is {value}."

                # Salary
                if "salary" in column_lower:
                    return f"Your salary is {value}."

                # Generic single value
                return f"The {self._humanize(column)} is {value}."

            # Two-column result
            if len(row) == 2:
                return self._format_two_column_result(row)

        # ---------------------------------------------------------
        # 2. Multiple rows
        # ---------------------------------------------------------
        if len(rows) > 1:
            return self._format_multiple_rows(rows)

        return "The requested information was retrieved successfully."

    # -------------------------------------------------------------
    # Two-column results
    # -------------------------------------------------------------

    def _format_two_column_result(
        self,
        row: dict[str, Any],
    ) -> str:

        columns = list(row.keys())

        first_column = columns[0]
        second_column = columns[1]

        first_value = row[first_column]
        second_value = row[second_column]

        first_lower = first_column.lower()
        second_lower = second_column.lower()

        # department + count
        if (
            "department" in first_lower
            and (
                "count" in second_lower
                or "number" in second_lower
            )
        ):
            return (
                f"There are {second_value} employees in the "
                f"{first_value} department."
            )

        if (
            "department" in second_lower
            and (
                "count" in first_lower
                or "number" in first_lower
            )
        ):
            return (
                f"There are {first_value} employees in the "
                f"{second_value} department."
            )

        # Generic categorical + numeric
        if isinstance(second_value, (int, float)):
            return (
                f"{first_value} has a value of {second_value}."
            )

        if isinstance(first_value, (int, float)):
            return (
                f"{second_value} has a value of {first_value}."
            )

        return (
            f"{self._humanize(first_column)} is {first_value}, "
            f"and {self._humanize(second_column)} is {second_value}."
        )

    # -------------------------------------------------------------
    # Multiple rows
    # -------------------------------------------------------------

    def _format_multiple_rows(
        self,
        rows: list[dict[str, Any]],
    ) -> str:

        return (
            f"I found {len(rows)} results matching your request. "
            "The detailed results are shown below."
        )

    # -------------------------------------------------------------
    # Formatting helper
    # -------------------------------------------------------------

    @staticmethod
    def _humanize(column: str) -> str:
        return column.replace("_", " ").strip().capitalize()


response_service = ResponseService()