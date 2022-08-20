# import logging
# from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_kvsession import KVSessionExtension
from simplekv.memory.redisstore import RedisStore
import redis

from config import Config


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.signin'


@login.user_loader
def load_user(user_id):
    import models
    return models.User.get(user_id)
    

def create_app(config_class = Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    store = RedisStore(redis.StrictRedis())
    KVSessionExtension(store, app)

    db.init_app(app)
    migrate.init_app(app, db)
    
    login.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.songs import bp as songs_bp
    app.register_blueprint(songs_bp, url_prefix='/songs')

    from app.playlists import bp as playlists_bp
    app.register_blueprint(playlists_bp, url_prefix='/playlists')

    # if not app.debug:
    #     if app.config['MAIL_SERVER']:
    #         auth = None
    #         if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
    #             auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    #         secure = None
    #         if app.config['MAIL_USE_TLS']:
    #             secure = ()
    #         mail_handler = SMTPHandler(
    #             mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
    #             fromaddr='no-reply@' + app.config['MAIL_SERVER'],
    #             toaddrs=app.config['ADMINS'], subject='Microblog Failure',
    #             credentials=auth, secure=secure)
    #         mail_handler.setLevel(logging.ERROR)
    #         app.logger.addHandler(mail_handler)
        
    #     if not os.path.exists('logs'):
    #         os.mkdir('logs')
    #     file_handler = RotatingFileHandler('logs/songbook.log', maxBytes = 10240, backupCount = 10)
    #     file_handler.setFormatter(
    #         logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    #     file_handler.setLevel(logging.INFO)
    #     app.logger.addHandler(file_handler)

    #     app.logger.setLevel(logging.INFO)
    #     app.logger.info('Songbook startup')
    
    return app

from app import models