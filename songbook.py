from app import create_app, db, cli
from app.models import User

app = create_app()
cli.register(app)

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure