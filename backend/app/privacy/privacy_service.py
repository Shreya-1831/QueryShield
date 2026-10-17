from dataclasses import dataclass, field
from typing import Any
import sqlglot
from sqlglot import exp


@dataclass
class PrivacyContext:
    employee_id: str
    role: str
    allowed_columns: dict[str, set[str]] = field(default_factory=dict)
    privacy_rules: dict[str, dict[str, dict[str, str]]] = field(
        default_factory=dict
    )


@dataclass
class PrivacyResult:
    rows: list[dict[str, Any]]
    filtered_rows: int = 0
    masked_fields: int = 0
    removed_fields: int = 0
    leakage_detected: bool = False
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)


class PrivacyService:

    def __init__(self, small_group_threshold: int = 5):
        self.small_group_threshold = small_group_threshold

    def protect(
        self,
        rows: list[dict[str, Any]],
        context: PrivacyContext,
        table_name: str,
        opa_decision: dict,
        authorized_sql: str | None = None,
    ) -> PrivacyResult:

        result = PrivacyResult(rows=[])

        if not rows:
            return result

        # --------------------------------------------------
        # 1. OPA privacy authorization
        # --------------------------------------------------

        if not opa_decision.get("allowed", False):
            result.blocked = True
            result.leakage_detected = True
            result.reasons.append(
                opa_decision.get(
                    "reason",
                    "Privacy policy violation."
                )
            )
            return result

        # --------------------------------------------------
        # 2. Small-group aggregation protection
        # --------------------------------------------------

        if authorized_sql:
            small_group_reason = self._check_small_group_aggregation(
                rows,
                authorized_sql,
            )

            if small_group_reason:
                result.blocked = True
                result.leakage_detected = True
                result.reasons.append(small_group_reason)
                return result

        sensitive_aggregation_reason = (
            self._check_sensitive_aggregation(
                rows,
                context,
                table_name,
                authorized_sql,
            )
        )

        if sensitive_aggregation_reason:
            result.blocked = True
            result.leakage_detected = True
            result.reasons.append(
                sensitive_aggregation_reason
            )
            return result
        
        # --------------------------------------------------
        # 3. Apply OPA actions
        # --------------------------------------------------

        actions = opa_decision.get("actions", {})

        protected_rows = []

        for row in rows:
            safe_row = {}

            for column, value in row.items():

                action = actions.get(column)

                if action == "allow":
                    safe_row[column] = value

                elif action == "mask":
                    safe_row[column] = self._mask_value(value)
                    result.masked_fields += 1

                elif action == "remove":
                    result.removed_fields += 1
                    result.leakage_detected = True

                else:
                    result.removed_fields += 1
                    result.leakage_detected = True
                    result.reasons.append(
                        f"Column '{column}' had no valid privacy action."
                    )

            protected_rows.append(safe_row)

        result.rows = protected_rows

        if result.masked_fields:
            result.reasons.append(
                "Sensitive fields were masked according to policy."
            )

        if result.removed_fields:
            result.reasons.append(
                "Fields were removed according to privacy policy."
            )

        return result

    # ======================================================
    # SMALL-GROUP AGGREGATION PROTECTION
    # ======================================================

    def _check_small_group_aggregation(
        self,
        rows: list[dict[str, Any]],
        sql: str,
    ) -> str | None:

        try:
            tree = sqlglot.parse_one(sql, read="mysql")

            if not isinstance(tree, exp.Select):
                return None

            # Only apply this rule to GROUP BY queries.
            group = tree.args.get("group")

            if group is None:
                return None

            # Find COUNT(...) output columns.
            count_columns = []

            for expression in tree.expressions:

                target = expression

                alias = None

                if isinstance(expression, exp.Alias):
                    alias = expression.alias
                    target = expression.this

                if isinstance(target, exp.Count):

                    output_name = alias

                    if not output_name:
                        output_name = target.sql(
                            dialect="mysql"
                        )

                    count_columns.append(output_name)

            # If the grouped query doesn't expose a count,
            # don't guess the group size from another aggregate.
            if not count_columns:
                return None

            # Check every returned group.
            for row in rows:

                for count_column in count_columns:

                    value = row.get(count_column)

                    if value is None:
                        continue

                    try:
                        group_size = int(value)
                    except (TypeError, ValueError):
                        continue

                    if group_size < self.small_group_threshold:
                        return (
                            "Small-group aggregation blocked: "
                            f"group size {group_size} is below "
                            f"the minimum threshold of "
                            f"{self.small_group_threshold}."
                        )

            return None

        except Exception:
            # Fail closed if the aggregation structure cannot
            # be safely analyzed.
            return (
                "Small-group aggregation could not be safely evaluated."
            )
    def _check_sensitive_aggregation(
        self,
        rows: list[dict[str, Any]],
        context: PrivacyContext | None,
        table_name: str,
        authorized_sql: str | None,
    ) -> str | None:
        """
        Prevent aggregate expressions from exposing sensitive
        source columns without an explicitly safe policy.

        Examples:
            AVG(salary)
            SUM(salary)
            MIN(salary)
            MAX(salary)
        """

        if not authorized_sql:
            return None

        # Some unit tests exercise aggregation protection
        # without a privacy context. In that case, this check
        # cannot determine column sensitivity, so leave the
        # decision to the other privacy checks.
        if context is None:
            return None

        try:
            tree = sqlglot.parse_one(
                authorized_sql,
                read="mysql",
            )

            if not isinstance(tree, exp.Select):
                return None

            privacy_rules = context.privacy_rules.get(
                table_name,
                {},
            )

            sensitive_columns = {
                column
                for column, rule in privacy_rules.items()
                if rule.get("sensitivity") == "sensitive"
                and rule.get("action") != "allow"
            }

            if not sensitive_columns:
                return None

            aggregate_types = (
                exp.Avg,
                exp.Sum,
                exp.Min,
                exp.Max,
            )

            for expression in tree.expressions:
                aggregates = expression.find_all(
                    *aggregate_types
                )

                for aggregate in aggregates:
                    source_columns = {
                        column.name
                        for column in aggregate.find_all(
                            exp.Column
                        )
                    }

                    exposed_columns = (
                        source_columns
                        & sensitive_columns
                    )

                    if exposed_columns:
                        column = sorted(exposed_columns)[0]

                        return (
                            "Sensitive aggregation blocked: "
                            f"aggregate on protected column "
                            f"'{column}' is not permitted."
                        )

            return None

        except Exception:
            return (
                "Sensitive aggregation could not be safely evaluated."
            )
    # ======================================================
    # MASKING
    # ======================================================

    @staticmethod
    def _mask_value(value: Any) -> Any:

        if value is None:
            return None

        value = str(value)

        if len(value) <= 4:
            return "*" * len(value)

        visible = 2

        return (
            value[:visible]
            + "*" * (len(value) - visible)
        )