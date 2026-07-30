from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app: Flask) -> None:
    """
    Registers global error handlers to return standardized JSON error responses.
    """

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        """Handle HTTP errors standardizing output to JSON."""
        response = {
            "error": {
                "code": e.code,
                "name": e.name,
                "description": e.description,
            }
        }
        return jsonify(response), e.code

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e: Exception):
        """Catch-all error handler for unexpected server errors."""
        app.logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
        response = {
            "error": {
                "code": 500,
                "name": "Internal Server Error",
                "description": "An unexpected error occurred on the server.",
            }
        }
        return jsonify(response), 500
