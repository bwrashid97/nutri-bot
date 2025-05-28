import pytest
from app import create_app
from project.extensions import db

@pytest.fixture(scope='module')
def test_client():
    flask_app = create_app()
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            db.create_all()
        yield testing_client
        with flask_app.app_context():
            db.drop_all()
