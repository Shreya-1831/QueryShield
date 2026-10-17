from sqlalchemy import text

from app.database.connection import engine


def get_user_policy(employee_id: str) -> dict | None:
    """
    Load the complete effective policy for an employee
    directly from the database.
    """

    with engine.connect() as db:

        rows = db.execute(
            text(
                """
                SELECT
                    r.role_name,
                    p.table_name,
                    p.allowed_columns,
                    p.row_condition,
                    pp.column_name AS privacy_column,
                    pp.sensitivity,
                    pp.action
                FROM users u

                JOIN roles r
                    ON u.role_id = r.role_id

                JOIN data_policies p
                    ON p.role_id = u.role_id

                LEFT JOIN privacy_policies pp
                    ON pp.role_id = u.role_id
                    AND pp.table_name = p.table_name

                WHERE u.employee_id = :employee_id
                  AND u.is_active = 1

                ORDER BY
                    p.table_name,
                    pp.column_name
                """
            ),
            {
                "employee_id": employee_id
            },
        ).mappings().all()

    if not rows:
        return None

    first = rows[0]

    policy = {
        "employee_id": employee_id,
        "role": first["role_name"],
        "tables": {},
    }

    for row in rows:

        table_name = row["table_name"]

        if table_name not in policy["tables"]:

            policy["tables"][table_name] = {
                "allowed_columns": {
                    column.strip()
                    for column in row["allowed_columns"].split(",")
                    if column.strip()
                },

                "row_condition": row["row_condition"],

                "privacy": {},
            }

        if row["privacy_column"]:

            policy["tables"][table_name]["privacy"][
                row["privacy_column"]
            ] = {
                "sensitivity": row["sensitivity"],
                "action": row["action"],
            }

    return policy


def build_privacy_context(employee_id: str):
    """
    Convert the database-derived effective policy into
    the structure consumed by the Privacy & Leakage Engine.
    """

    from app.privacy.privacy_service import PrivacyContext

    policy = get_user_policy(employee_id)

    if not policy:
        return None

    allowed_columns = {}

    privacy_rules = {}

    for table_name, table_policy in policy["tables"].items():

        allowed_columns[table_name] = set(
            table_policy["allowed_columns"]
        )

        privacy_rules[table_name] = dict(
            table_policy["privacy"]
        )

    return PrivacyContext(
        employee_id=policy["employee_id"],
        role=policy["role"],
        allowed_columns=allowed_columns,
        privacy_rules=privacy_rules,
    )