import getpass

from sqlalchemy import text

from app.database.connection import engine
from app.policy.policy_service import get_user_policy


class IdentityService:

    def get_windows_username(self) -> str:
        return getpass.getuser().strip().lower()

    def resolve(self) -> dict | None:
        # Trusted identity obtained directly from Windows
        windows_username = self.get_windows_username()

        # Match Windows username against the users table
        with engine.connect() as db:
            row = db.execute(
                text("""
                    SELECT
                        user_id,
                        employee_id,
                        username,
                        is_active
                    FROM users
                    WHERE LOWER(windows_username) = :username
                    LIMIT 1
                """),
                {
                    "username": windows_username
                },
            ).mappings().first()

        # No matching username = NOT authenticated
        if not row:
            return None

        # Matching username but inactive = NOT authenticated
        if not row["is_active"]:
            return None

        # Employee ID is derived from the matched username
        employee_id = row["employee_id"]

        # Role/policy is derived from the trusted Employee ID
        policy = get_user_policy(employee_id)

        if not policy:
            return None

        return {
            "user_id": row["user_id"],
            "employee_id": employee_id,
            "username": row["username"],
            "role": policy["role"],
        }


identity_service = IdentityService()