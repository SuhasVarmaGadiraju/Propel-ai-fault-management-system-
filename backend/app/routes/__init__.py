from flask import Flask
from .health import health_bp
from .pole_registry import pole_registry_bp
from .telemetry import telemetry_bp
from .network_graph import network_graph_bp
from .faults import faults_bp
from .tickets import tickets_bp


def register_routes(app: Flask) -> None:
    """
    Register all application Blueprints with API versioning prefix.
    """
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(pole_registry_bp, url_prefix="/api/v1/pole-registry")
    app.register_blueprint(telemetry_bp, url_prefix="/api/v1/telemetry")
    app.register_blueprint(network_graph_bp, url_prefix="/api/v1/network")
    app.register_blueprint(faults_bp, url_prefix="/api/v1/faults")
    app.register_blueprint(tickets_bp, url_prefix="/api/v1/tickets")
