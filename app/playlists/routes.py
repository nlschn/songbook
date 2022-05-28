from datetime import datetime
from app import db
from app.models import Playlist, Song
from app.playlists import bp
from app.playlists.forms import AddSongToPlaylistForm, NewPlaylistForm, OpenSharedPlaylistForm

from flask import render_template, flash, redirect, url_for, request, session, send_file
from flask_login import current_user, login_required

import os
import uuid

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
    if playlist == None:
        flash("Invalid operation.")
        return redirect(url_for("playlists.playlists"))
    
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


@bp.route('/publish', methods = ["POST"])
@login_required
def publish():
    args = list(request.form.items())    
    playlist_db_id = args[0][0]   
    playlist = Playlist.query.get(playlist_db_id)

    if playlist.share:
        playlist.share_link = None
        playlist.share = False
    else:
        playlist.share_link = str(uuid.uuid4().hex)
        playlist.share = True

    db.session.commit()
    
    return redirect(url_for("playlists.playlists"))


@bp.route('/download', methods = ["POST"])
@login_required
def download():
    from app.songs.routes import delete_user_temp_files
    delete_user_temp_files()

    args = list(request.form.items())
    playlist_db_id = args[0][0]

    playlist = Playlist.query.get(playlist_db_id)

    pdf_path = build_songbook(playlist)
    path = os.path.join(*pdf_path.split("/")[1:])
    return send_file(path, as_attachment=True)


@bp.route('/shared/<link>', methods = ["GET", "POST"])
def shared(link):   
    playlist = Playlist.query.where(Playlist.share_link == link).first()   

    if playlist == None or not playlist.share:
        form = OpenSharedPlaylistForm()
        flash("This link does not belong to a public playlist.")
        return redirect(url_for(
            "playlists.shared_without_args", form = form))

    session["view_playlist"] = playlist.id

    return redirect(url_for("playlists.view_playlist"), code=307)


@bp.route('/open', methods = ["GET", "POST"])
def shared_without_args():
    form = OpenSharedPlaylistForm()

    if form.validate_on_submit():
        link = form.id.data.replace(" ", "")
        return shared(link)

    return render_template(
        "playlists/enter_link.html",
        form = form)


@bp.route('/view_playlist', methods = ["GET", "POST"])
def view_playlist():
    playlist = Playlist.query.get(int(session["view_playlist"]))
    if playlist == None:
        form = OpenSharedPlaylistForm()
        flash("Invalid operation")
        return redirect(url_for(
            "playlists.shared_without_args", form = form))

    author = playlist.user
    
    args = list(request.form.items())
    if len(args) > 0:
        command = args[0][0]

        if command == "AddSelectedToCollection":
            checked_song_ids = list(map(lambda x : int(x[0]), filter(lambda y : y[1] == "on", args)))
            
            if len(checked_song_ids) > 0:
                added_songs, already_known_songs = add_list_of_songs_to_collection(checked_song_ids)
                flash(f"{len(added_songs)} new songs were added to your collection, {'1 was' if len(already_known_songs) == 1 else str(len(already_known_songs)) + ' were' } already present.")
            else:
                flash("Please select songs to add.")
        elif command == "Songbook":
            pdf_path = build_songbook(playlist)
            path = os.path.join(*pdf_path.split("/")[1:])
            return send_file(path, as_attachment=True)

    return render_template(
        "playlists/shared_playlist.html",
        playlist = playlist,
        author = author,
        title = "Shared playlist",
        subtitle = f'"{playlist.name}" by {author.username}',
        songs = playlist.songs)


def add_list_of_songs_to_collection(song_ids):
    already_known_songs = []
    added_songs = []

    for song_id in song_ids:
        song_to_add = Song.query.get(song_id)

        already_known = False
        for s in current_user.songs:
            if s.equal(song_to_add):
                already_known_songs.append(song_to_add)
                already_known = True
                break
        if not already_known:
            copy = Song.copy(song_to_add)
            copy.added = datetime.now()
            copy.last_changed = datetime.now()
            
            current_user.songs.append(copy)            
            db.session.add(copy)
            added_songs.add(copy)
            
    db.session.commit()
    return added_songs, already_known_songs


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