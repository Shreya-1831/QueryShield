
import sqlglot
from sqlglot import exp


MAX_ROWS = 500
MAX_JOINS = 3
MAX_SUBQUERIES = 2

# These functions are not needed for ordinary analytical SELECT queries.
# Keep this denylist conservative and expand it based on supported use cases.
BLOCKED_FUNCTIONS = {
    "SLEEP",
    "BENCHMARK",
    "LOAD_FILE",
    "GET_LOCK",
    "RELEASE_LOCK",
    "RELEASE_ALL_LOCKS",
    "IS_FREE_LOCK",
    "MASTER_POS_WAIT",
    "WAIT_FOR_EXECUTED_GTID_SET",
}

# Unsupported constructs are rejected until their behavior is explicitly
# validated for this application's MySQL and SQLGlot versions.
BLOCKED_NODE_TYPES = {
    "Into",
    "Lock",
    "Locking",
}


def _node_type_name(node):
    return type(node).__name__


def _has_blocked_construct(tree):
    """Reject known side-effect, locking, and unsupported SQL constructs."""
    for node in tree.walk():
        node_type = _node_type_name(node)

        if node_type in BLOCKED_NODE_TYPES:
            return True

        # MySQL-specific clauses can be stored as Select arguments rather
        # than appearing as a distinct AST node in every SQLGlot version.
        if isinstance(node, exp.Select):
            args = node.args

            if args.get("into") or args.get("locks") or args.get("lock"):
                return True

        # Reject CTEs until the authorization layer implements explicit
        # CTE scope and column-lineage validation.
        if isinstance(node, exp.CTE):
            return True

    return False


def _function_name(node):
    """Get a function name without assuming all functions are represented alike."""
    try:
        name = node.sql_name()
        if name:
            return str(name).upper()
    except Exception:
        pass

    try:
        name = node.name
        if name:
            return str(name).upper()
    except Exception:
        pass

    return ""


def _contains_blocked_function(tree):
    for node in tree.walk():
        if isinstance(node, exp.Func):
            if _function_name(node) in BLOCKED_FUNCTIONS:
                return True

    return False


def _count_joins(tree):
    return sum(1 for node in tree.walk() if isinstance(node, exp.Join))


def _count_subqueries(tree):
    return sum(
        1 for node in tree.walk()
        if isinstance(node, exp.Subquery)
    )


def _clamp_limit(select, maximum):
    """
    Ensure a SELECT has a positive, bounded integer LIMIT.

    Unsupported expressions are rejected rather than assumed safe.
    """
    limit = select.args.get("limit")

    if limit is None:
        select.set(
            "limit",
            exp.Limit(expression=exp.Literal.number(maximum)),
        )
        return None

    expression = limit.expression

    if not isinstance(expression, exp.Literal) or not expression.is_int:
        return "Only integer literal LIMIT values are supported"

    try:
        value = int(expression.this)
    except (TypeError, ValueError):
        return "Invalid LIMIT value"

    if value < 0:
        return "LIMIT cannot be negative"

    # LIMIT 0 is valid SQL but usually not useful for interactive queries.
    # Preserve its semantics rather than silently changing the request.
    if value > maximum:
        limit.set("expression", exp.Literal.number(maximum))

    return None


def harden_sql(sql: str) -> tuple[bool, str, str | None]:
    """
    Apply conservative safety and complexity checks to a single SELECT.

    Authorization of tables, columns, and row policies must happen
    separately before this function is called.
    """
    try:
        statements = sqlglot.parse(sql, read="mysql")
        statements = [
            statement for statement in statements
            if statement is not None
        ]

        if len(statements) != 1:
            return False, "Exactly one SQL statement is required", None

        tree = statements[0]

        # Reject non-SELECT roots, including DML and set-operation roots.
        if not isinstance(tree, exp.Select):
            return False, "Only SELECT queries are allowed", None

        if not tree.expressions:
            return False, "SELECT list cannot be empty", None

        # Reject SELECT * at every SELECT level.
        for select in tree.find_all(exp.Select):
            for expression in select.expressions:
                if isinstance(expression, exp.Star):
                    return False, "SELECT * is not allowed", None

                if (
                    isinstance(expression, exp.Column)
                    and expression.is_star
                ):
                    return False, "SELECT * is not allowed", None

        if _has_blocked_construct(tree):
            return False, "Unsupported or unsafe SQL construct", None

        if _contains_blocked_function(tree):
            return False, "Query uses a prohibited function", None

        if _count_joins(tree) > MAX_JOINS:
            return False, "Query is too complex", None

        if _count_subqueries(tree) > MAX_SUBQUERIES:
            return False, "Too many subqueries", None

        # Keep CTE and derived-table support disabled until their scopes
        # and column lineage are validated by the authorizer.
        for node in tree.walk():
            if isinstance(node, exp.CTE):
                return False, "CTE queries are not currently supported", None

        # Apply a limit to each SELECT scope. This bounds returned rows
        # per SELECT but does NOT guarantee bounded database scan work.
        for select in tree.find_all(exp.Select):
            reason = _clamp_limit(select, MAX_ROWS)
            if reason:
                return False, reason, None

        # The root SELECT is included by find_all in normal SQLGlot ASTs.
        # Verify it explicitly to avoid relying on traversal assumptions.
        reason = _clamp_limit(tree, MAX_ROWS)
        if reason:
            return False, reason, None

        hardened_sql = tree.sql(dialect="mysql")

        # Parse the serialized result again to catch serialization issues.
        check_statements = sqlglot.parse(hardened_sql, read="mysql")
        check_statements = [
            statement for statement in check_statements
            if statement is not None
        ]

        if (
            len(check_statements) != 1
            or not isinstance(check_statements[0], exp.Select)
        ):
            return False, "Hardened SQL failed validation", None

        return True, "Query hardened", hardened_sql

    except Exception:
        return False, "Invalid SQL", None
