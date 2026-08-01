import os
from flask import Flask
from flask_cors import CORS

from app.config import config_by_name
from app.database import db, migrate
from app.routes import register_routes
from app.middleware import register_error_handlers
from app.utils import setup_logger
import app.models  # Ensure all ORM models are registered


def create_app(config_name: str = None) -> Flask:
    """
    Application Factory Pattern for Flask.
    Creates and configures the Flask application instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)

    # Load configuration
    config_cls = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_cls)

    # Setup Logging
    setup_logger(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # Register Blueprints / Routes
    register_routes(app)

    # Register Middleware / Global Error Handlers
    register_error_handlers(app)

    app.logger.info(f"Flask App initialized under [{config_name}] environment.")

    return app
