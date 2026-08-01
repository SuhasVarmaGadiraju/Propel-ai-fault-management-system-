import os
from app import create_app
from app.database.init_db import init_db

# Instantiate Flask application using Application Factory
app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    init_db(app)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
