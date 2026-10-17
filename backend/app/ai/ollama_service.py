import os
import time

import requests
from dotenv import load_dotenv
from sqlalchemy import text

from app.ai.schema_context import build_schema_context
from app.database.connection import engine


load_dotenv()

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434"
)

OLLAMA_URL = f"{OLLAMA_HOST.rstrip('/')}/api/generate"

DEFAULT_OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5-coder:7b"
)

def get_active_model() -> str:
    """Return the single active, approved model.

    Fail closed if the registry has no active model or is inconsistent.
    """
    with engine.connect() as db:
        rows = db.execute(
            text("""
                SELECT model_id, model_name, version, approved
                FROM model_registry
                WHERE status = 'ACTIVE'
                ORDER BY model_id
                LIMIT 2
            """)
        ).mappings().all()

    if not rows:
        raise RuntimeError(
            "No active model is configured in model_registry"
        )

    if len(rows) > 1:
        raise RuntimeError(
            "Multiple active models found in model_registry; "
            "exactly one active model is required"
        )

    model = rows[0]

    if not model["approved"]:
        raise RuntimeError(
            "The active model is not approved in model_registry"
        )

    return f"{model['model_name']}:{model['version']}"


def is_model_available(model: str) -> bool:
    """Check whether an exact model tag is installed in local Ollama."""
    response = requests.get(
        f"{OLLAMA_HOST.rstrip('/')}/api/tags",
        timeout=5,
    )
    response.raise_for_status()

    models = response.json().get("models", [])

    return any(
        entry.get("name") == model
        or entry.get("model") == model
        for entry in models
    )


def update_model_latency(model: str, latency_ms: float) -> None:
    """Update the registered model's running average latency."""

    model_name, version = model.rsplit(":", 1)

    with engine.begin() as db:
        row = db.execute(
            text("""
                SELECT avg_latency_ms, latency_sample_count
                FROM model_registry
                WHERE model_name = :model_name
                  AND version = :version
                FOR UPDATE
            """),
            {
                "model_name": model_name,
                "version": version,
            },
        ).mappings().first()

        if not row:
            return

        previous_latency = row["avg_latency_ms"]
        sample_count = row["latency_sample_count"]

        if previous_latency is None or sample_count == 0:
            new_latency = latency_ms
            new_count = 1
        else:
            new_count = sample_count + 1
            new_latency = (
                (float(previous_latency) * sample_count + latency_ms)
                / new_count
            )

        db.execute(
            text("""
                UPDATE model_registry
                SET avg_latency_ms = :latency,
                    latency_sample_count = :sample_count
                WHERE model_name = :model_name
                  AND version = :version
            """),
            {
                "latency": round(new_latency),
                "sample_count": new_count,
                "model_name": model_name,
                "version": version,
            },
        )


def generate_sql(employee_id: str, prompt: str) -> str:
    schema = build_schema_context(employee_id)

    model = get_active_model()

    system_prompt = f"""
You are QueryShield's SQL generator.

Your task is to convert the user's natural-language request into a safe,
semantically correct MySQL SELECT statement.

Verified employee ID: {employee_id}

Authorized schema:
{schema}

STRICT RULES:

1. AUTHORIZED SCHEMA
- Use ONLY tables and columns explicitly present in the authorized schema.
- Never invent tables, columns, relationships, values, or mappings.
- Treat the authorized schema as the complete set of data available to you.
- If the requested information cannot be obtained from the authorized schema,
  do not invent an alternative field.

2. SEMANTIC UNDERSTANDING
- Understand what information the user is actually asking for.
- Select columns based on their meaning and relationship to the user's request,
  not merely because their names contain similar words.
- Prefer the column that most directly represents the requested information.
- When both a human-readable/descriptive column and a technical
  identifier/code/key column represent the same concept, prefer the
  human-readable/descriptive column unless the user explicitly asks for
  the identifier, code, key, or ID.
- Do not expose an internal identifier when an authorized descriptive
  representation is available.
- Do not assume that a column ending in "_id" is the desired answer unless
  the user explicitly requests an ID or identifier.
- Apply this reasoning dynamically to ANY table and ANY column.
- Do not rely on hardcoded domain-specific mappings.

3. USER INTENT
- Return the information that best answers the user's actual request.
- If the user asks "What is my X?", return the most meaningful authorized
  value representing X.
- If the user asks for an ID, identifier, code, key, or technical reference,
  return the corresponding authorized identifier.
- If the user asks for a name, label, description, category, location,
  department, designation, or other descriptive attribute, prefer the
  corresponding descriptive value when available.
- These are semantic examples, NOT hardcoded column mappings.

4. EMPLOYEE IDENTITY
- The verified employee ID is authoritative.
- When the user asks for their own information, use the verified employee ID
  exactly: {employee_id}.
- Never guess, substitute, convert, or numerically reinterpret the verified
  employee ID.
- Never use another employee ID in place of the verified employee ID.

5. EMPLOYEE SCOPE
- If the user asks for all employees, everyone, all employee records,
  or multiple employees, preserve that requested scope.
- Do not silently reinterpret "all", "everyone", or "multiple employees"
  as "my".
- Authorization is handled separately by QueryShield.

6. SQL SAFETY
- Return ONLY SQL.
- Generate SELECT statements only.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE,
  GRANT, REVOKE, or any other write/DDL statement.
- Never use SELECT *.
- Do not include markdown.
- Do not include explanations.

7. QUERY CORRECTNESS
- Use appropriate WHERE conditions to answer the user's request.
- Use the verified employee ID when the request concerns the authenticated employee.
- Do not add unnecessary columns.
- Do not return technical/internal fields unless they are required to answer
  the request or explicitly requested.
- Use a JOIN only when the required tables and the exact relationship are
  explicitly provided in the AUTHORIZED RELATIONSHIPS section.
- Never invent a JOIN condition.
- Never infer a relationship merely because two columns have similar names.
- Never JOIN a table that is not present in the authorized schema.
- When an authorized relationship provides a more meaningful representation
  of the requested information, use that relationship.

8. AGGREGATIONS
- For aggregate queries, select the dimensions and measures that directly
  answer the user's request.
- Use meaningful aliases for calculated values where appropriate.
- Prefer descriptive grouping attributes over technical IDs when the user
  requests a human-readable breakdown and an authorized descriptive
  attribute is available.
- Do not replace a requested identifier with a descriptive value when the
  user explicitly requested the identifier.

9. DYNAMIC SCHEMA REASONING
- The schema may represent ANY business domain.
- Do not assume the database contains employees, departments, salaries,
  or any other specific business entity unless they appear in the schema.
- Apply the same semantic reasoning to arbitrary authorized schemas.

- The AUTHORIZED SCHEMA lists the tables and columns you are allowed to use.
- The AUTHORIZED RELATIONSHIPS section lists database-defined relationships
  between authorized tables.
- Treat AUTHORIZED RELATIONSHIPS as the only valid source for JOIN conditions.
- If a requested value exists in another authorized table and an authorized
  relationship connects the required tables, use that relationship.
- If no authorized relationship exists, do not invent one.

10. OUTPUT MINIMIZATION
- Return only the fields necessary to answer the user's request.
- If a descriptive value answers the request, do not also return its
  identifier unless the user explicitly asks for both.
- If the user asks for an identifier, return the identifier.
- Do not expose unrelated authorized columns merely because they are available.

11. DERIVED VALUES
- When the requested information is not stored directly, determine whether it can be deterministically derived from the authorized schema.
- Use authorized source columns only as inputs to the derivation and return the derived value rather than exposing source columns that were not requested.
- Translate the user's natural-language conditions into the corresponding SQL expression and apply the condition to the derived value.
- Preserve the meaning, operators, boundaries, and scope expressed by the user.
- Do not expose intermediate or sensitive source values unless they are explicitly requested.
- Do not invent derived fields, formulas, operators, or source columns.
- Do not add unrelated tables, joins, columns, or calculations.

Generate the safest and most semantically appropriate SELECT query possible.
"""

    full_prompt = f"{system_prompt}\nUser request: {prompt}"

    print("QueryShield prompt characters:", len(full_prompt))
    print("QueryShield prompt words:", len(full_prompt.split()))

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 256
            }
        },
        timeout=120
    )

    latency_ms = round(
        (time.perf_counter() - start) * 1000,
        2
    )

    response.raise_for_status()

    # Record model performance only after a successful Ollama response.
    update_model_latency(model, latency_ms)

    sql = response.json()["response"].strip()

    if sql.startswith("```"):
        sql = (
            sql
            .replace("```sql", "")
            .replace("```", "")
            .strip()
        )

    return sql