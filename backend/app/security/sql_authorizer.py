import sqlglot
from sqlglot import exp

def _nearest_select(node):
    """Return the nearest SELECT scope containing this node."""
    parent = node.parent

    while parent is not None:
        if isinstance(parent, exp.Select):
            return parent
        parent = parent.parent

    return None


def _direct_tables(select):
    """Tables belonging directly to this SELECT, excluding nested scopes."""
    return [
        table
        for table in select.find_all(exp.Table)
        if _nearest_select(table) is select
    ]


def _direct_columns(select):
    """Columns belonging directly to this SELECT."""
    return [
        column
        for column in select.find_all(exp.Column)
        if _nearest_select(column) is select
    ]


def _aliases(select):
    """Map table aliases to physical table names for one SELECT scope."""
    return {
        table.alias_or_name: table.name
        for table in _direct_tables(select)
    }


def _inside_alias_clause(column):
    """Check whether a column occurs in ORDER BY, GROUP BY, or HAVING."""
    parent = column.parent

    while parent is not None:
        if isinstance(parent, exp.Select):
            return False

        if isinstance(parent, (exp.Order, exp.Group, exp.Having)):
            return True

        parent = parent.parent

    return False


def _parse_row_condition(condition, table_name):
    """Parse a trusted policy condition for its specific table."""
    if not condition:
        return None

    if not table_name.replace("_", "").isalnum():
        raise ValueError("Invalid row-policy table name")

    try:
        tree = sqlglot.parse_one(
            f"SELECT 1 FROM `{table_name}` WHERE ({condition})",
            read="mysql",
        )
        where = tree.args.get("where")

        if where is None:
            raise ValueError("Row policy must contain a WHERE condition")

        if any(
            isinstance(node, (exp.Subquery, exp.Select))
            for node in where.walk()
        ):
            raise ValueError("Subqueries are not allowed in row policies")

        return where.this

    except Exception as exc:
        raise ValueError(
            f"Invalid row authorization condition: {exc}"
        ) from exc


def _apply_row_conditions(tree, row_conditions):
    """Apply row policies to matching tables in the top-level SELECT."""
    if not row_conditions:
        return tree

    if not isinstance(tree, exp.Select):
        raise ValueError("Row policies require a top-level SELECT")

    tables = _direct_tables(tree)

    for policy_table, condition in row_conditions.items():
        if not condition:
            continue

        matches = [
            table for table in tables
            if table.name.lower() == policy_table.lower()
        ]

        # A policy for a table absent from the query is irrelevant.
        if not matches:
            continue

        # Avoid ambiguous self-joins until each table occurrence
        # can receive its own independently validated policy.
        if len(matches) != 1:
            raise ValueError(
                f"Multiple references to policy-protected table "
                f"'{policy_table}' are not supported"
            )

        table = matches[0]
        alias = table.alias_or_name

        predicate = _parse_row_condition(condition, policy_table)

        # Qualify policy columns with the table alias so joins work.
        for column in predicate.find_all(exp.Column):
            if not column.table:
                column.set("table", exp.to_identifier(alias))

        where = tree.args.get("where")

        if where is not None:
            combined = exp.and_(
                where.this.copy(),
                predicate.copy(),
            )
        else:
            combined = predicate.copy()

        tree.set("where", exp.Where(this=combined))

    return tree


def _validate_access(
    tree,
    allowed_columns,
    allowed_tables,
    allowed_database=None,
    allow_aggregations=True,
):
    """Validate table, column, and query-scope access."""

    allowed_tables = {
        table.lower() for table in allowed_tables
    }

    # Support both table-specific column policies and legacy flat sets.
    if isinstance(allowed_columns, dict):
        table_columns = {
            table.lower(): {
                column.lower() for column in columns
            }
            for table, columns in allowed_columns.items()
        }
        flat_columns = (
            set().union(*table_columns.values())
            if table_columns
            else set()
        )
    else:
        table_columns = {}
        flat_columns = {
            column.lower() for column in allowed_columns
        }

    # Reject CTEs until their lineage can be validated safely.
    if any(
        isinstance(node, exp.CTE)
        for node in tree.walk()
    ):
        return "CTEs are not supported by the SQL authorizer"

    # Reject derived tables until their output-column lineage is supported.
    for node in tree.find_all(exp.Subquery):
        if isinstance(node.parent, (exp.From, exp.Join)):
            return "Derived-table queries are not supported"

    selects = list(tree.find_all(exp.Select))

    if not selects:
        return "Only SELECT queries are allowed"

    for select in selects:
        tables = _direct_tables(select)
        table_names = {
            table.name.lower() for table in tables
        }
        aliases = {
            alias.lower(): physical.lower()
            for alias, physical in _aliases(select).items()
        }

        # Validate every directly referenced table.
        for table in tables:
            table_name = table.name.lower()

            if table.db:
                if (
                    allowed_database is None
                    or table.db.lower() != allowed_database.lower()
                ):
                    return "Database-qualified table access denied"

            if table.catalog:
                return "Catalog-qualified table access denied"

            if table_name not in allowed_tables:
                return "Table access denied"

        # Preserve the existing policy: allow aggregates when the query
        # includes HAVING, but reject aggregate SELECT queries without it.
        
        has_aggregate = any(
            isinstance(node, exp.AggFunc)
            for expression in select.expressions
            for node in expression.walk()
        )

        has_having = select.args.get("having") is not None

        if has_aggregate and not allow_aggregations and not has_having:
            return "Aggregate queries are not allowed"
        
        aggregate_aliases = {
            expression.alias.lower()
            for expression in select.expressions
            if isinstance(expression, exp.Alias)
            and any(
                isinstance(node, exp.AggFunc)
                for node in expression.this.walk()
            )
        }

        # Validate columns in this SELECT scope.
        for column in _direct_columns(select):
            
            if (
                allow_aggregations
                and has_aggregate
                and not column.table
                and column.name.lower() in aggregate_aliases
                and _inside_alias_clause(column)
            ):
                continue

            if column.is_star:
                # SELECT * is checked separately by authorize_sql().
                continue

            column_name = column.name.lower()

            if column.table:
                # Resolve aliases to physical table names.
                physical_table = aliases.get(
                    column.table.lower(),
                    column.table.lower(),
                )

                if physical_table not in allowed_tables:
                    return "Column access denied"

                if table_columns:
                    permitted_columns = table_columns.get(
                        physical_table, set()
                    )

                    if column_name not in permitted_columns:
                        return "Column access denied"
                elif column_name not in flat_columns:
                    return "Column access denied"

                continue

            # Legacy flat-set mode has no table ownership information.
            if not table_columns:
                if column_name not in flat_columns:
                    return "Column access denied"
                continue

            # Find tables in this scope that own the unqualified column.
            owners = [
                table_name
                for table_name in table_names
                if column_name in table_columns.get(
                    table_name, set()
                )
            ]

            if not owners:
                return "Column access denied"

            if len(owners) > 1:
                return "Ambiguous unqualified column access"

    return None

def authorize_sql(
    sql,
    allowed_columns,
    allowed_tables,
    row_condition=None,
    allowed_database=None,
    allow_aggregations=True,
):
    """Authorize a single read-only SELECT query."""
    try:
        statements = sqlglot.parse(sql, read="mysql")
        statements = [statement for statement in statements if statement is not None]

        if len(statements) != 1:
            return False, "Multiple SQL statements are not allowed", None

        tree = statements[0]

        if not isinstance(tree, exp.Select):
            return False, "Only SELECT queries are allowed", None

        if not tree.expressions:
            return False, "SELECT list cannot be empty", None

        # Reject SELECT * in any SELECT scope.
        for select in tree.find_all(exp.Select):
            for expression in select.expressions:
                if isinstance(expression, exp.Star):
                    return False, "SELECT * is not allowed", None

                if (
                    isinstance(expression, exp.Column)
                    and expression.is_star
                ):
                    return False, "SELECT * is not allowed", None

        
        if isinstance(row_condition, str):
            row_conditions = {"employees": row_condition}
        elif isinstance(row_condition, dict):
            row_conditions = row_condition
        elif row_condition is None:
            row_conditions = {}
        else:
            return False, "Invalid row policy configuration", None

        if row_conditions:
            nested_selects = [
                select for select in tree.find_all(exp.Select)
                if select is not tree
            ]
            if nested_selects:
                return (
                    False,
                    "Nested SELECTs are not supported with row-level policies",
                    None,
                )

        reason = _validate_access(
            tree,
            allowed_columns,
            allowed_tables,
            allowed_database=allowed_database,
            allow_aggregations=allow_aggregations,
        )

        if reason:
            return False, reason, None

        if row_conditions:
            try:
                tree = _apply_row_conditions(tree, row_conditions)
            except ValueError as exc:
                return False, str(exc), None

            reason = _validate_access(
                tree,
                allowed_columns,
                allowed_tables,
                allowed_database=allowed_database,
                allow_aggregations=allow_aggregations,
            )

            if reason:
                return False, f"Row policy validation failed: {reason}", None

        return True, "Query authorized", tree.sql(dialect="mysql")

    except ValueError as exc:
        return False, str(exc), None
    except Exception:
        return False, "Invalid SQL", None


def _resolve_column(column, aliases, allowed_columns):
    """Resolve a column to a physical table when unambiguous."""
    if column.table:
        return aliases.get(column.table, column.table)

    owners = [
        table_name
        for table_name, columns in allowed_columns.items()
        if column.name in columns
    ]

    return owners[0] if len(owners) == 1 else None


def extract_query_metadata(sql, allowed_columns: dict[str, set[str]]) -> dict:
    """Extract output, derived-expression, and filter metadata."""
    try:
        tree = sqlglot.parse_one(sql, read="mysql")

        if not isinstance(tree, exp.Select):
            raise ValueError("Only SELECT queries are supported")

        if any(isinstance(node, exp.CTE) for node in tree.walk()):
            raise ValueError("CTEs are not supported by metadata extraction")

        aliases = _aliases(tree)
        physical = []
        derived = {}

        for expression in tree.expressions:
            if isinstance(expression, exp.Column):
                if expression.is_star:
                    raise ValueError("SELECT * is not allowed")

                physical.append({
                    "name": expression.name,
                    "table": _resolve_column(
                        expression,
                        aliases,
                        allowed_columns,
                    ),
                })
                continue

            target = (
                expression.this
                if isinstance(expression, exp.Alias)
                else expression
            )

            name = (
                expression.alias
                if isinstance(expression, exp.Alias)
                else expression.sql(dialect="mysql")
            )

            sources = [
                {
                    "name": column.name,
                    "table": _resolve_column(
                        column,
                        aliases,
                        allowed_columns,
                    ),
                }
                for column in target.find_all(exp.Column)
                if not column.is_star
            ]

            derived[name] = {
                "source_columns": sources,
                "expression": target.sql(dialect="mysql"),
            }

        where = tree.args.get("where")
        filter_derivations = []

        if where is not None:
            predicate = where.this

            sources = [
                {
                    "name": column.name,
                    "table": _resolve_column(
                        column,
                        aliases,
                        allowed_columns,
                    ),
                }
                for column in predicate.find_all(exp.Column)
                if not column.is_star
            ]

            if sources:
                filter_derivations.append({
                    "expression": predicate.sql(dialect="mysql"),
                    "source_columns": sources,
                })

        return {
            "physical_columns": physical,
            "derived_columns": derived,
            "filter_derivations": filter_derivations,
        }

    except Exception as exc:
        raise ValueError(
            f"Unable to extract query metadata: {exc}"
        ) from exc
