import pandas as pd
from app import db
from app.playlists import bp
from app.music import mbapi
from app.playlists.forms import NewPlaylistForm
from app.music.builder import build_tex
from app.models import Playlist, Song

import ast
import os
from flask import render_template, flash, redirect, url_for, request, session, send_file
from flask_login import current_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
from app.models import Playlist


@bp.route("/playlists", methods = ["GET", "POST"])
@login_required
def playlists():
    playlists = current_user.playlists.all()
    create_form = NewPlaylistForm()

    if create_form.validate_on_submit():
        print ("lihfskd")
        playlist = Playlist(name = create_form.name.data)

        db.session.add(playlist)

        # current_user.playlists.append(playlist)

        db.session.commit()

        flash(f'Playlist "{playlist.name}" successfully created.')

    # Show the default page
    return render_template(
        'playlists/playlists.html', 
        user = current_user, title = "Manage your playlists", 
        subtitle = "Songbook", 
        view = "playlists",
        playlists = playlists,
        create_form = create_form)
