from app import db
from app.models import Playlist, Song
from app.playlists import bp
from app.playlists.forms import AddSongToPlaylistForm, NewPlaylistForm

from flask import render_template, flash, redirect, url_for, request, session, send_file
from flask_login import current_user, login_required
from datetime import datetime

import os

@bp.route("/playlists", methods = ["GET", "POST"])
@login_required
def playlists():
    from app.songs.routes import delete_user_temp_files
    delete_user_temp_files()

    create_form = NewPlaylistForm()

    if create_form.validate_on_submit():
        playlist = Playlist(name = create_form.name.data)

        db.session.add(playlist)
        current_user.playlists.append(playlist)
        db.session.commit()

        flash(f'Playlist "{playlist.name}" successfully created.')

    playlists = current_user.playlists.all()
    lengths =  {p.name : len(p.songs) for p in playlists}

    # Calculate preview string
    max_length = 200
    playlist_preview = {}
    j = 0

    for p in playlists:
        if len(p.songs) == 0: 
            preview = "0"
        else:
            song_str = ""
            char_count = 0
            for i in range(len(p.songs)):
                song = p.songs[i]           
                song_str += song.title
                char_count += len(song.title)

                j += 1

                if char_count < max_length and i < len(p.songs) - 1:
                    song_str += ", "

                if char_count >= max_length and j != len(p.songs):
                    song_str += f", and {len(p.songs) - j} more"
                    break

            preview = f"{len(p.songs)} ({song_str})"
        playlist_preview[p.id] = preview

    # Show the default page
    return render_template(
        'playlists/playlists.html', 
        user = current_user, title = "Manage your playlists", 
        subtitle = "Songbook", 
        view = "playlists",
        playlists = playlists,
        lengths = lengths,
        playlist_preview = playlist_preview,
        create_form = create_form)


@bp.route('/edit', methods = ["GET", "POST"])
@login_required
def edit():
    args = list(request.form.items())
    
    if len(args) == 1: # if we come from the playlists page
        playlist_db_id = args[0][0]
        session["current_playlist_db_id"] = playlist_db_id
    else: # we get the form parameters
        playlist_db_id = session["current_playlist_db_id"]

    playlist = Playlist.query.get(playlist_db_id)
    songs = playlist.songs
    collection = current_user.songs.all()
    collection_by_id = {f'{x.id}' : x.to_dict() for x in collection}

    form = AddSongToPlaylistForm()
    
    submit_pressed = len(list(filter(lambda y : y[0] == "submit", args))) == 1 # make sure to not update when select or deselect is pressed
    
    if form.validate_on_submit() and submit_pressed: # We click "Add selected songs"
        # Add songs and show default page
        checked_song_ids = list(map(lambda x : int(x[0]), filter(lambda y : y[1] == "on", args)))
        
        for song_id in checked_song_ids:
            song_to_add = Song.query.get(song_id)

            if song_to_add not in playlist.songs:
                playlist.songs.append(song_to_add)
        db.session.commit()

        songs = playlist.songs

    # Show the default page
    return render_template(
        'playlists/edit.html', 
        user = current_user, title = 'Edit playlist', 
        subtitle = playlist.name, 
        view = "playlists",
        playlist = playlist,
        songs = songs,
        form = form,
        collection = collection,
        collection_by_id = collection_by_id)


@bp.route('/delete', methods = ["POST"])
@login_required
def delete():
    args = list(request.form.items())
    
    playlist_db_id = args[0][0]

    playlist = Playlist.query.get(playlist_db_id)
    db.session.delete(playlist)
    db.session.commit()

    flash(f'Successfully removed the playlist "{playlist.name}".')

    return redirect(url_for("playlists.playlists"))


@bp.route('/remove', methods = ["POST"])
@login_required
def remove():
    playlist_db_id = session["current_playlist_db_id"]
    playlist = Playlist.query.get(playlist_db_id)

    args = list(request.form.items())
    id_to_remove = args[0][0]
    song_to_remove = Song.query.get(id_to_remove)
    playlist.songs.remove(song_to_remove)
    
    db.session.commit()
    
    return redirect(url_for("playlists.edit"))


@bp.route('/download', methods = ["POST"])
def download():
    from app.songs.routes import delete_user_temp_files
    delete_user_temp_files()

    args = list(request.form.items())
    playlist_db_id = args[0][0]

    playlist = Playlist.query.get(playlist_db_id)

    pdf_path = build_songbook(playlist)
    path = os.path.join(*pdf_path.split("/")[1:])
    return send_file(path, as_attachment=True)


def build_songbook(playlist):
    from app.songs.routes import get_user_path
    path = get_user_path("")

    if not os.path.exists("app/static"):
        os.mkdir("app/static")
    if not os.path.exists("app/static/tmp"):
        os.mkdir("app/static/tmp")
    if not os.path.exists(path):
        os.mkdir(path)

    from app.music.builder import build_songbook as build_songbook_pdf
    return build_songbook_pdf(playlist, current_user, path)