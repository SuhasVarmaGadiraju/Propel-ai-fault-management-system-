from flask import Flask
from .health import health_bp


def register_routes(app: Flask) -> None:
    """
    Register all application Blueprints with API versioning prefix.
    """
    app.register_blueprint(health_bp, url_prefix="/api/v1")
