import json
import subprocess
from pathlib import Path
from typing import Any


OPA_PATH = Path(r"C:\Tools\OPA\opa.exe")
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "opa"
    / "privacy_policy.rego"
)


class OPAService:
    def __init__(
        self,
        opa_path: Path = OPA_PATH,
        policy_path: Path = POLICY_PATH,
    ):
        self.opa_path = Path(opa_path)
        self.policy_path = Path(policy_path)

    @staticmethod
    def _allowed_column_names(allowed_columns: Any) -> set[str]:
        """Collect column names from supported policy formats."""
        if isinstance(allowed_columns, dict):
            names = set()

            for name, permitted in allowed_columns.items():
                if permitted is True:
                    names.add(name)
                elif isinstance(permitted, (list, tuple, set)):
                    names.update(
                        column
                        for column in permitted
                        if isinstance(column, str)
                    )
                elif isinstance(permitted, dict):
                    names.update(
                        column
                        for column, allowed in permitted.items()
                        if allowed is True
                    )

            return names

        if isinstance(allowed_columns, (list, tuple, set)):
            return {
                name
                for name in allowed_columns
                if isinstance(name, str)
            }

        return set()

    @staticmethod
    def _get_column_rule(
        privacy_rules: dict,
        column: str,
        physical_columns: list,
    ) -> dict | None:
        """Support flat rules and table-nested privacy rules."""
        # Backward-compatible flat format.
        direct_rule = privacy_rules.get(column)
        if isinstance(direct_rule, dict) and "action" in direct_rule:
            return direct_rule

        # Table-aware format: table -> column -> rule.
        matching_tables = {
            item.get("table")
            for item in physical_columns
            if isinstance(item, dict) and item.get("name") == column
        }

        matching_rules = []
        for table in matching_tables:
            table_rules = privacy_rules.get(table, {})
            if isinstance(table_rules, dict):
                rule = table_rules.get(column)
                if isinstance(rule, dict):
                    matching_rules.append(rule)

        if not matching_rules:
            return None

        actions = {rule.get("action") for rule in matching_rules}
        if not actions.issubset({"allow", "mask", "remove"}):
            return None

        # Fail conservatively if the same output maps to multiple
        # sources with different privacy actions.
        if "remove" in actions:
            action = "remove"
        elif "mask" in actions:
            action = "mask"
        else:
            action = "allow"

        return {"action": action}

    def evaluate(self, input_data: dict) -> dict:
        result_columns = input_data.get("result_columns", [])
        allowed_columns = input_data.get("allowed_columns", {})
        physical_columns = input_data.get("physical_columns", [])
        derived_columns = input_data.get("derived_columns", {})
        privacy_rules = input_data.get("privacy_rules", {})

        if not isinstance(result_columns, list) or not all(
            isinstance(column, str) for column in result_columns
        ):
            return {
                "allowed": False,
                "actions": {},
                "reason": "Invalid result column format.",
            }

        if not isinstance(privacy_rules, dict):
            return {
                "allowed": False,
                "actions": {},
                "reason": "Invalid privacy policy format.",
            }

        has_metadata = (
            "physical_columns" in input_data
            and "derived_columns" in input_data
        )

        if has_metadata:
            if not isinstance(physical_columns, list):
                return {
                    "allowed": False,
                    "actions": {},
                    "reason": "Invalid physical column metadata.",
                }

            if not isinstance(derived_columns, dict):
                return {
                    "allowed": False,
                    "actions": {},
                    "reason": "Invalid derived column metadata.",
                }

        # Confirm each physical column against its own table's policy.
        for column in physical_columns:
            if not isinstance(column, dict):
                return {
                    "allowed": False,
                    "actions": {},
                    "reason": "Invalid physical column metadata.",
                }

            table = column.get("table")
            name = column.get("name")

            if not isinstance(table, str) or not isinstance(name, str):
                return {
                    "allowed": False,
                    "actions": {},
                    "reason": "Invalid physical column metadata.",
                }

            table_columns = (
                allowed_columns.get(table)
                if isinstance(allowed_columns, dict)
                else None
            )

            if not isinstance(table_columns, (list, tuple, set)) or (
                name not in table_columns
            ):
                return {
                    "allowed": False,
                    "actions": {},
                    "reason": "policy_violation",
                }

        # Every derived output must have source metadata. OPA checks
        # whether those source columns are allowed and have valid rules.
        for output in result_columns:
            if output not in self._allowed_column_names(allowed_columns):
                if output not in derived_columns:
                    return {
                        "allowed": False,
                        "actions": {},
                        "reason": "policy_violation",
                    }

        # Run the configured local OPA policy.
        if not self.opa_path.is_file():
            raise RuntimeError(
                f"OPA executable not found: {self.opa_path}"
            )

        if not self.policy_path.is_file():
            raise RuntimeError(
                f"OPA policy file not found: {self.policy_path}"
            )

        process = subprocess.run(
            [
                str(self.opa_path),
                "eval",
                "-f",
                "json",
                "-I",
                "-d",
                str(self.policy_path),
                "data.queryshield.privacy.decision",
            ],
            input=json.dumps(input_data),
            text=True,
            capture_output=True,
            check=False,
        )

        if process.returncode != 0:
            raise RuntimeError(
                f"OPA evaluation failed: {process.stderr.strip()}"
            )

        try:
            response = json.loads(process.stdout)
            decision = response["result"][0]["expressions"][0]["value"]
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected OPA response: {process.stdout}"
            ) from exc

        if not isinstance(decision, dict):
            raise RuntimeError(
                f"OPA decision must be an object, got: {decision!r}"
            )

        if decision.get("allowed") is not True:
            return {
                "allowed": False,
                "actions": {},
                "reason": decision.get(
                    "reason", "OPA denied the privacy request."
                ),
            }

        # Resolve output actions from table-specific physical source rules.
        actions = {}
        invalid_rules = []

        for output in result_columns:
            if has_metadata and output in derived_columns:
                actions[output] = "allow"
                continue

            rule = self._get_column_rule(
                privacy_rules,
                output,
                physical_columns,
            )

            if not isinstance(rule, dict):
                invalid_rules.append(output)
                continue

            action = rule.get("action")

            if action not in {"allow", "mask", "remove"}:
                invalid_rules.append(output)
                continue

            actions[output] = action

        if invalid_rules:
            return {
                "allowed": False,
                "actions": {},
                "reason": (
                    "Missing or invalid privacy rules for: "
                    + ", ".join(sorted(set(invalid_rules)))
                ),
            }

        return {
            **decision,
            "allowed": True,
            "actions": actions,
        }