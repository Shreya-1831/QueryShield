from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.query.query_service import execute_query
from app.privacy.privacy_service import PrivacyContext


def run_query(role, employee_id, prompt, sql, rows):

    policy = {
        "employee_id": employee_id,
        "role": role,
        "tables": {
            "employees": {
                "allowed_columns": {"employee_id","name","salary","department_id","joining_date","date_of_birth",},
                "row_condition": (
                    "employee_id = '{employee_id}'"
                    if role == "Employee" else None
                ),
                "privacy": {
                    "salary": {
                        "sensitivity": "sensitive",
                        "action": "allow"
                    },
                    "department_id": {
                        "sensitivity": "low",
                        "action": "allow"
                    },
                    "joining_date": {
                        "sensitivity": "low",
                        "action": "allow"
                    },
                    "date_of_birth": {
                        "sensitivity": "sensitive",
                        "action": "allow"
                    }
                }
            }
        }
    }

    opa = {
        "allowed": True,
        "actions": {
            "employee_id": "allow",
            "name": "allow",
            "salary": "allow",
            "department_id": "allow",
            "joining_date": "allow",
            "joining_year": "allow",
            "date_of_birth": "allow",
            "employee_count": "allow",
            "total_salary": "allow",
            "average_salary": "allow",
            "minimum_salary": "allow",
            "maximum_salary": "allow",
            "salary_difference": "allow",
            "age": "allow",
        }
    }

    class Scan:
        allowed = True
        reason = None
        categories = []
        risk_level = type("Risk", (), {"value": "low"})()

    class Result:
        def mappings(self):
            return self

        def all(self):
            return rows

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, query):
            return Result()

    context = PrivacyContext(
        employee_id=employee_id,
        role=role,
        allowed_columns={
            "employees": policy["tables"]["employees"]["allowed_columns"]
        },
        privacy_rules={
            "employees": policy["tables"]["employees"]["privacy"]
        },
    )

    with patch(
        "app.query.query_service.scan_prompt",
        return_value=Scan(),
    ), patch(
        "app.query.query_service.get_user_policy",
        return_value=policy,
    ), patch(
        "app.query.query_service.generate_sql",
        return_value=sql,
    ), patch(
        "app.query.query_service.db_manager.connect",
        return_value=Connection(),
    ), patch(
        "app.query.query_service.opa_service.evaluate",
        return_value=opa,
    ), patch(
        "app.query.query_service.build_privacy_context",
        return_value=context,
    ), patch(
        "app.query.query_service.presidio_service.protect_text",
        side_effect=lambda x: {
            "text": x,
            "pii_detected": False,
            "entities": [],
        },
    ):
        return execute_query(employee_id, prompt, role)


def test_employee_own_data():

    result = run_query(
        "Employee",
        "EMP002",
        "Show my name and salary",
        "SELECT employee_id, name, salary FROM employees",
        [
            {
                "employee_id": "EMP002",
                "name": "Employee 2",
                "salary": 75000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["salary"] == 75000


def test_employee_cannot_access_other_employee():

    result = run_query(
        "Employee",
        "EMP002",
        "Show EMP001 salary",
        "SELECT employee_id, name, salary FROM employees "
        "WHERE employee_id = 'EMP001'",
        [],
    )

    assert result["success"] is True
    assert result["row_count"] == 0
    assert result["data"] == []


def test_admin_can_access_all_employees():

    result = run_query(
        "Admin",
        "EMP001",
        "Show all employees with salary",
        "SELECT employee_id, name, salary FROM employees",
        [
            {
                "employee_id": "EMP001",
                "name": "Employee 1",
                "salary": 65000,
            },
            {
                "employee_id": "EMP002",
                "name": "Employee 2",
                "salary": 75000,
            },
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 2
    assert len(result["data"]) == 2

def test_employee_broad_query_blocked():
    with patch(
        "app.query.query_service.generate_sql"
    ) as generate_sql:
        result = run_query(
            "Employee",
            "EMP002",
            "Show all employees",
            "SELECT employee_id, name, salary FROM employees",
            [],
        )

    assert result["success"] is False
    generate_sql.assert_not_called()

def test_employee_broad_query_provides_safe_alternative():
    with patch(
        "app.query.query_service.generate_sql"
    ) as generate_sql:
        result = run_query(
            "Employee",
            "EMP002",
            "Show all employees",
            "SELECT employee_id, name, salary FROM employees",
            [],
        )

    assert result["success"] is False
    assert result["stage"] == "authorization"
    assert "safe_alternative" in result
    assert result["safe_alternative"] == (
        "You can ask for your own employee information."
    )
    generate_sql.assert_not_called()

def test_employee_broad_query_stops_before_sql():
    policy = {
        "employee_id": "EMP002",
        "role": "Employee",
        "tables": {
            "employees": {
                "allowed_columns": {"employee_id", "name", "salary","department_id","joining_date","age"},
                "row_condition": "employee_id = '{employee_id}'",
                "privacy": {},
            }
        },
    }

    scan = SimpleNamespace(
        allowed=True,
        reason=None,
        risk_level=SimpleNamespace(value="low"),
    )

    generate_sql = MagicMock()
    connect = MagicMock()

    with patch("app.query.query_service.scan_prompt", return_value=scan), \
         patch("app.query.query_service.get_user_policy", return_value=policy), \
         patch("app.query.query_service.generate_sql", generate_sql), \
         patch("app.query.query_service.db_manager.connect", connect):

        result = execute_query("EMP002", "Show all employees", "Employee")

    assert result["success"] is False
    generate_sql.assert_not_called()
    connect.assert_not_called()

def test_blocked_query_creates_security_audit():
    with patch(
        "app.query.query_service.audit_service.record_security_event"
    ) as record_event:
        result = execute_query(
            "EMP002",
            "Show all employees",
            "Employee",
        )

    assert result["success"] is False
    record_event.assert_called_once()
    assert record_event.call_args.args[1] == "BROAD_DATA_REQUEST"

def test_sql_authorization_failure_stops_database():
    scan = SimpleNamespace(
        allowed=True,
        reason=None,
        risk_level=SimpleNamespace(value="low"),
    )

    connect = MagicMock()

    with patch("app.query.query_service.scan_prompt", return_value=scan), \
         patch("app.query.query_service.get_user_policy", return_value={
             "employee_id": "EMP002",
             "role": "Employee",
             "tables": {
                 "employees": {
                     "allowed_columns": {"employee_id", "name"},
                     "row_condition": "employee_id = '{employee_id}'",
                     "privacy": {}
                 }
             }
         }), \
         patch("app.query.query_service.generate_sql",
               return_value="SELECT salary FROM employees"), \
         patch("app.query.query_service.db_manager.connect", connect):

        result = execute_query(
            "EMP002",
            "Show my salary",
            "Employee"
        )

    assert result["success"] is False
    assert result["stage"] == "sql_authorization"
    connect.assert_not_called()

def test_sql_hardening_failure_stops_database():
    scan = SimpleNamespace(
        allowed=True,
        reason=None,
        risk_level=SimpleNamespace(value="low"),
    )

    connect = MagicMock()

    with patch("app.query.query_service.scan_prompt", return_value=scan), \
         patch("app.query.query_service.get_user_policy", return_value={
             "employee_id": "EMP002",
             "role": "Employee",
             "tables": {
                 "employees": {
                     "allowed_columns": {"employee_id", "name"},
                     "row_condition": "employee_id = '{employee_id}'",
                     "privacy": {}
                 }
             }
         }), \
         patch("app.query.query_service.generate_sql",
               return_value="SELECT name FROM employees"), \
         patch("app.query.query_service.authorize_sql",
               return_value=(True, "Query authorized",
                             "SELECT name FROM employees")), \
         patch("app.query.query_service.harden_sql",
               return_value=(False, "Query is too complex", None)), \
         patch("app.query.query_service.db_manager.connect", connect):

        result = execute_query(
            "EMP002",
            "Show my name",
            "Employee"
        )

    assert result["success"] is False
    assert result["stage"] == "sql_hardening"
    connect.assert_not_called()

def test_aggregation_query_through_pipeline():
    result = run_query(
        "Admin",
        "EMP001",
        "How many employees are there?",
        "SELECT COUNT(employee_id) AS employee_count FROM employees",
        [
            {
                "employee_count": 25,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["employee_count"] == 25

def test_grouped_aggregation_query_through_pipeline():
    result = run_query(
        "Admin",
        "EMP001",
        "Show employee count by department",
        """
        SELECT department_id, COUNT(employee_id) AS employee_count
        FROM employees
        GROUP BY department_id
        """,
        [
            {
                "department_id": 1,
                "employee_count": 10,
            },
            {
                "department_id": 2,
                "employee_count": 8,
            },
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 2
    assert result["data"][0]["employee_count"] == 10

def test_analytics_order_by_query_through_pipeline():
    result = run_query(
        "Admin",
        "EMP001",
        "Show departments ordered by employee count",
        """
        SELECT department_id, COUNT(employee_id) AS employee_count
        FROM employees
        GROUP BY department_id
        ORDER BY employee_count DESC
        """,
        [
            {
                "department_id": 1,
                "employee_count": 10,
            },
            {
                "department_id": 2,
                "employee_count": 8,
            },
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 2
    assert result["data"][0]["employee_count"] >= result["data"][1]["employee_count"]

def test_filtered_aggregation_query_through_pipeline():
    result = run_query(
        "Admin",
        "EMP001",
        "How many employees are in department 1?",
        """
        SELECT COUNT(employee_id) AS employee_count
        FROM employees
        WHERE department_id = 1
        """,
        [
            {
                "employee_count": 10,
            }
        ],
    )

    assert result["success"] is True
    assert result["data"][0]["employee_count"] == 10

def test_employee_aggregation_respects_row_policy():
    result = run_query(
        "Employee",
        "EMP002",
        "How many employees are there?",
        """
        SELECT COUNT(employee_id) AS employee_count
        FROM employees
        """,
        [
            {
                "employee_count": 1,
            }
        ],
    )

    assert result["success"] is True
    assert result["data"][0]["employee_count"] == 1

def test_sum_aggregation_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "What is the total salary?",
        """
        SELECT SUM(salary) AS total_salary
        FROM employees
        """,
        [
            {
                "total_salary": 175000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["total_salary"] == 175000

def test_avg_aggregation_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "What is the average salary?",
        """
        SELECT AVG(salary) AS average_salary
        FROM employees
        """,
        [
            {
                "average_salary": 70000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["average_salary"] == 70000

def test_min_aggregation_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "What is the minimum salary?",
        """
        SELECT MIN(salary) AS minimum_salary
        FROM employees
        """,
        [
            {
                "minimum_salary": 65000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["minimum_salary"] == 65000

def test_max_aggregation_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "What is the maximum salary?",
        """
        SELECT MAX(salary) AS maximum_salary
        FROM employees
        """,
        [
            {
                "maximum_salary": 75000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["maximum_salary"] == 75000

def test_higher_than_comparison_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employees with salary higher than 70000",
        """
        SELECT employee_id, name, salary
        FROM employees
        WHERE salary > 70000
        """,
        [
            {
                "employee_id": "EMP002",
                "name": "Employee 2",
                "salary": 75000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["salary"] > 70000

def test_lower_than_comparison_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employees with salary lower than 70000",
        """
        SELECT employee_id, name, salary
        FROM employees
        WHERE salary < 70000
        """,
        [
            {
                "employee_id": "EMP001",
                "name": "Employee 1",
                "salary": 65000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["salary"] < 70000

def test_difference_comparison_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "What is the difference between the maximum and minimum salary?",
        """
        SELECT
            MAX(salary) - MIN(salary) AS salary_difference
        FROM employees
        """,
        [
            {
                "salary_difference": 10000,
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["salary_difference"] == 10000

def test_compare_departments_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Compare average salary between departments",
        """
        SELECT
            department_id,
            AVG(salary) AS average_salary
        FROM employees
        GROUP BY department_id
        ORDER BY average_salary DESC
        """,
        [
            {
                "department_id": 1,
                "average_salary": 75000,
            },
            {
                "department_id": 2,
                "average_salary": 65000,
            },
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 2

    assert (
        result["data"][0]["average_salary"]
        > result["data"][1]["average_salary"]
    )

def test_date_before_comparison_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employees who joined before 2025",
        """
        SELECT employee_id, name, joining_date
        FROM employees
        WHERE joining_date < '2025-01-01'
        """,
        [
            {
                "employee_id": "EMP001",
                "name": "Employee 1",
                "joining_date": "2024-06-15",
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["joining_date"] < "2025-01-01"

def test_date_after_comparison_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employees who joined after 2025",
        """
        SELECT employee_id, name, joining_date
        FROM employees
        WHERE joining_date > '2025-01-01'
        """,
        [
            {
                "employee_id": "EMP002",
                "name": "Employee 2",
                "joining_date": "2025-07-10",
            }
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["joining_date"] > "2025-01-01"

def test_date_range_query_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employees who joined between 2024 and 2025",
        """
        SELECT employee_id, name, joining_date
        FROM employees
        WHERE joining_date BETWEEN '2024-01-01' AND '2025-12-31'
        """,
        [
            {
                "employee_id": "EMP001",
                "name": "Employee 1",
                "joining_date": "2024-06-15",
            },
            {
                "employee_id": "EMP002",
                "name": "Employee 2",
                "joining_date": "2025-07-10",
            },
        ],
    )

    assert result["success"] is True
    assert result["row_count"] == 2

    for row in result["data"]:
        assert "joining_date" in row

def test_yearly_joining_analysis_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employee count by joining date",
        """
        SELECT
            YEAR(joining_date) AS joining_year,
            COUNT(employee_id) AS employee_count
        FROM employees
        GROUP BY YEAR(joining_date)
        ORDER BY YEAR(joining_date)
        """,
        [
            {
                "joining_year": 2024,
                "employee_count": 10,
            },
            {
                "joining_year": 2025,
                "employee_count": 15,
            },
        ],
    )

    print("\nDEBUG YEARLY RESULT:", result)
    assert result["success"] is True
    assert result["row_count"] == 2
    assert result["data"][0]["joining_year"] == 2024
    assert result["data"][1]["joining_year"] == 2025

def test_age_calculation_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employee ages",
        """
        SELECT
            employee_id,
            name,
            TIMESTAMPDIFF(
                YEAR,
                date_of_birth,
                CURDATE()
            ) AS age
        FROM employees
        """,
        [
            {
                "employee_id": "EMP001",
                "name": "Employee 1",
                "age": 25,
            },
            {
                "employee_id": "EMP002",
                "name": "Employee 2",
                "age": 24,
            },
        ],
    )

    print("\nDEBUG AGE RESULT:", result)
    assert result["success"] is True
    assert result["row_count"] == 2
    assert result["data"][0]["age"] == 25
    assert result["data"][1]["age"] == 24

def test_age_comparison_through_pipeline():

    result = run_query(
        "Admin",
        "EMP001",
        "Show employees older than 25",
        """
        SELECT
            employee_id,
            name,
            TIMESTAMPDIFF(
                YEAR,
                date_of_birth,
                CURDATE()
            ) AS age
        FROM employees
        WHERE TIMESTAMPDIFF(
            YEAR,
            date_of_birth,
            CURDATE()
        ) > 25
        """,
        [
            {
                "employee_id": "EMP001",
                "name": "Employee 1",
                "age": 26,
            }
        ],
    )

    print("\nDEBUG AGE COMPARISON RESULT:", result)
    assert result["success"] is True
    assert result["row_count"] == 1
    assert result["data"][0]["age"] > 25