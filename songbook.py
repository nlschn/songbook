from app import create_app, cli

app = create_app()
cli.register(app)

# https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xv-a-better-application-structure