from flask_migrate import Migrate
from project.extensions import db
from app import create_app

app = create_app()
Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)
