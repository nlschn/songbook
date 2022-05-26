from app import db
from app.playlists import bp
from app.playlists.forms import NewPlaylistForm
from app.models import Playlist

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
    create_form = NewPlaylistForm()

    if create_form.validate_on_submit():
        playlist = Playlist(name = create_form.name.data)

        db.session.add(playlist)

        current_user.playlists.append(playlist)

        db.session.commit()

        flash(f'Playlist "{playlist.name}" successfully created.')

    playlists = current_user.playlists.all()
    lengths =  {p.name : len(p.songs) for p in playlists}

    # Show the default page
    return render_template(
        'playlists/playlists.html', 
        user = current_user, title = "Manage your playlists", 
        subtitle = "Songbook", 
        view = "playlists",
        playlists = playlists,
        lengths = lengths,
        create_form = create_form)


@bp.route('/delete', methods = ["POST"])
def delete():
    args = list(request.form.items())
    print(args)
    playlist_db_id = args[0][0]

    playlist = Playlist.query.get(playlist_db_id)
    db.session.delete(playlist)
    db.session.commit()

    flash(f'Successfully removed the playlist "{playlist.name}".')

    return redirect(url_for("playlists.playlists"))