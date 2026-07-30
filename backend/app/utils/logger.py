import logging
import sys
from flask import Flask


def setup_logger(app: Flask) -> None:
    """
    Configures structured logging for the Flask application.
    """
    log_level = logging.DEBUG if app.debug else logging.INFO

    # Custom log format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s in %(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console log handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)

    # Attach stream handler to app logger
    app.logger.handlers.clear()
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(log_level)

    app.logger.info(f"Logging initialized with level: {logging.getLevelName(log_level)}")
