from sqlalchemy import text

from app.policy.policy_service import get_user_policy
from app.database.connection import engine


def _get_authorized_relationships(authorized_tables: set[str]) -> list[str]:
    """
    Discover foreign-key relationships from MySQL.

    Only relationships where BOTH tables are authorized are returned.
    """

    if not authorized_tables:
        return []

    placeholders = ", ".join(
        f":table_{i}" for i in range(len(authorized_tables))
    )

    params = {
        f"table_{i}": table
        for i, table in enumerate(sorted(authorized_tables))
    }

    query = text(
        f"""
        SELECT
            TABLE_NAME AS child_table,
            COLUMN_NAME AS child_column,
            REFERENCED_TABLE_NAME AS parent_table,
            REFERENCED_COLUMN_NAME AS parent_column
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND REFERENCED_TABLE_NAME IS NOT NULL
          AND TABLE_NAME IN ({placeholders})
          AND REFERENCED_TABLE_NAME IN ({placeholders})
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
    )

    # The same named placeholders cannot be reused safely with
    # separate IN lists, so build a second set for the referenced tables.
    query = text(
        f"""
        SELECT
            TABLE_NAME AS child_table,
            COLUMN_NAME AS child_column,
            REFERENCED_TABLE_NAME AS parent_table,
            REFERENCED_COLUMN_NAME AS parent_column
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND REFERENCED_TABLE_NAME IS NOT NULL
          AND TABLE_NAME IN (
              {", ".join(f":child_{i}" for i in range(len(authorized_tables)))}
          )
          AND REFERENCED_TABLE_NAME IN (
              {", ".join(f":parent_{i}" for i in range(len(authorized_tables)))}
          )
        ORDER BY TABLE_NAME, COLUMN_NAME
        """
    )

    params = {}

    for i, table in enumerate(sorted(authorized_tables)):
        params[f"child_{i}"] = table
        params[f"parent_{i}"] = table

    with engine.connect() as db:
        rows = db.execute(query, params).mappings().all()

    relationships = []

    for row in rows:
        relationships.append(
            f"{row['child_table']}.{row['child_column']} = "
            f"{row['parent_table']}.{row['parent_column']}"
        )

    return relationships


def build_schema_context(employee_id: str) -> str:
    """
    Build the schema available to the authenticated user.

    The schema contains:
    - authorized tables
    - authorized columns
    - authorized row restrictions
    - database-defined relationships between authorized tables
    """

    policy = get_user_policy(employee_id)

    if not policy:
        raise PermissionError("No active data policy found")

    schemas = []

    for table, data in policy["tables"].items():

        allowed_columns = sorted(data["allowed_columns"])

        if not allowed_columns:
            continue

        schemas.append(
            f"TABLE {table}\n"
            f"COLUMNS:\n"
            + "\n".join(
                f"    - {column}"
                for column in allowed_columns
            )
        )

    if not schemas:
        raise PermissionError("No authorized schema available")

    authorized_tables = {
        table
        for table, data in policy["tables"].items()
        if data["allowed_columns"]
    }

    relationships = _get_authorized_relationships(
        authorized_tables
    )

    context = "\n\n".join(schemas)

    if relationships:
        context += "\n\nAUTHORIZED RELATIONSHIPS:\n"

        context += "\n".join(
            f"    - {relationship}"
            for relationship in relationships
        )

    return context