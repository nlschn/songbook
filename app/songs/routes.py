from app import db
from app.songs import bp
from app.music import mbapi

from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from werkzeug.urls import url_parse

from app.songs.forms import SongSearchForm

@bp.route("/collection")
@login_required
def collection():
    return render_template('songs/collection.html', user = current_user, title = "Manage your collection", subtitle = "Songbook", view = "songs")


@bp.route("/add", methods = ["POST", "GET"])
@login_required
def add():
    form = SongSearchForm()

    if form.is_submitted():
        song_title = form.title.data
        song_artist = form.artist.data
        songs = mbapi.search(song_title, song_artist)

        return render_template('songs/add.html', 
            user = current_user, 
            title = "Add a new song", 
            subtitle = f'Results for "{song_title}" by "{song_artist}"', 
            view = "add", 
            form = form, 
            songs = songs, 
            song_title = song_title, 
            song_artist = song_artist)

    return render_template('songs/add.html', 
        user = current_user, 
        title = "Add a new song", 
        subtitle = "Songbook", 
        view = "add", 
        form = form, 
        songs = None, 
        song_title = None, 
        song_artist = None)