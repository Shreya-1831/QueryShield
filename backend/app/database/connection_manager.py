from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from app.database.connection import settings

QUERY_TIMEOUT_MS = 10000


class ConnectionManager:
    def __init__(self):
        self.engines = {
            "Admin": self._create_engine(
                settings.QS_ADMIN_USER, settings.QS_ADMIN_PASSWORD
            ),
            "Employee": self._create_engine(
                settings.QS_EMPLOYEE_USER, settings.QS_EMPLOYEE_PASSWORD
            ),
        }

    def _create_engine(self, username, password):
        url = URL.create(
            "mysql+pymysql",
            username=username,
            password=password,
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            database=settings.MYSQL_DATABASE,
        )
        engine = create_engine(url, pool_pre_ping=True)

        @event.listens_for(engine, "connect")
        def set_query_timeout(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute(
                f"SET SESSION MAX_EXECUTION_TIME={QUERY_TIMEOUT_MS}"
            )
            cursor.close()

        return engine

    def connect(self, role):
        if role not in self.engines:
            raise ValueError(f"Unsupported role: {role}")
        return self.engines[role].connect()


db_manager = ConnectionManager()