from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy ORM instance
db = SQLAlchemy()

# Initialize Flask-Migrate instance
migrate = Migrate()
