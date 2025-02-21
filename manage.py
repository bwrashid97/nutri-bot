from flask_migrate import Migrate
from project.extensions import db
from app import create_app  # Certifique-se de que 'app.py' está na raiz e possui a função create_app()

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(debug=True)
