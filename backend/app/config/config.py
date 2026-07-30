import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the backend package
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file if present
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)


def get_database_uri() -> str:
    """Build PostgreSQL URI dynamically from environment variables."""
    explicit_uri = os.getenv("DATABASE_URL")
    if explicit_uri:
        return explicit_uri

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "propel_fault_db")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


class Config:
    """Base Configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key-change-me")
    DEBUG = False
    TESTING = False

    # PostgreSQL Database configuration
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CORS configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


class DevelopmentConfig(Config):
    """Development Environment Configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing Environment Configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "sqlite:///:memory:"
    )


class ProductionConfig(Config):
    """Production Environment Configuration."""
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
