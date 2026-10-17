from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    QS_ADMIN_USER: str
    QS_ADMIN_PASSWORD: str
    QS_EMPLOYEE_USER: str
    QS_EMPLOYEE_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        extra="ignore"
    )


settings = Settings()

db_url = URL.create(
    "mysql+pymysql",
    username=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    database=settings.MYSQL_DATABASE,
)

engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)


def check_db():
    with engine.connect() as db:
        return db.execute(text("SELECT 1")).scalar() == 1