from app import db
from app.main import bp

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from datetime import datetime


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now()
        db.session.commit()


@bp.route('/')
@bp.route('/index')
def index():
    return render_template("index.html", centered = True)


@bp.route("/profile")
@login_required
def profile():
    return render_template('main/profile.html', user = current_user, subtitle = current_user.username, view = "overview")


@bp.route("/songs")
@login_required
def songs():
    return render_template('main/songs.html', user = current_user, title = "Manage Songs", subtitle = current_user.username, view = "songs")