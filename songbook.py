from app import create_app, db, cli
from app.models import User

app = create_app()
cli.register(app)
