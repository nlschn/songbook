from app import db
from app.songs import bp
from app.music import mbapi
from app.songs.forms import LyricsForm, LyricsFormAddToDb, SongSearchForm
from app.music.new_builder import create_song
from app.models import Song

import ast
import os
from flask import render_template, flash, redirect, url_for, request, session, send_file
from flask_login import current_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime


@bp.route("/collection")
@login_required
def collection():
    songs = sorted(list(current_user.songs.all()), key=lambda x: x.title)

    return render_template(
        'songs/collection.html',
        user=current_user, title="Manage your collection",
        subtitle="Songbook",
        view="collection",
        songs=songs)


@bp.route("/add", methods=["POST", "GET"])
@login_required
def add():
    form = SongSearchForm()

    if form.is_submitted():
        song_title = form.title.data
        song_artist = form.artist.data
        song_release = form.release.data
        songs = mbapi.search(song_title, song_artist, song_release)

        return render_template('songs/add.html',
                               user=current_user,
                               title="Add a new song",
                               subtitle=f'Results for "{song_title}" by "{song_artist}"',
                               view="add",
                               form=form,
                               songs=songs,
                               song_title=song_title,
                               song_artist=song_artist)

    return render_template('songs/add.html',
                           user=current_user,
                           title="Add a new song",
                           subtitle="Songbook",
                           view="add",
                           form=form,
                           songs=None,
                           song_title=None,
                           song_artist=None)


@bp.route("/choose", methods=["POST"])
@login_required
def choose():
    args = list(request.form.items())

    form = LyricsForm()
    form_add = LyricsFormAddToDb()

    if len(args) == 1:  # if the argument is a song, we came from the search page
        song_dict = ast.literal_eval(args[0][0])
        song = mbapi.SongInfo(song_dict["id"], song_dict["title"], song_dict["artist"], song_dict["release"],
                              song_dict["year"], song_dict["cover_url"])

        delete_user_temp_files()

        session["current_song"] = song

        return render_template('songs/configure_song.html',
                               user=current_user,
                               title="Add a new song",
                               subtitle=f"{song.title} by {song.artist}",
                               view="new",
                               song=song,
                               form=form,
                               form_add=form_add,
                               img_paths=None,
                               pdf_path=None,
                               pages=None,
                               pages_str=None)

    else:
        song = session["current_song"]

        if form.validate_on_submit():  # we pressed the build button
            session["lyrics"] = form.lyrics.data
            session["notes"] = form.notes.data
            session["capo"] = form.capo.data
            
            song.capo = form.capo.data
            song.notes = form.notes.data
            song.lyrics = form.lyrics.data

            pdf_path, img_paths, pages, small_font = build_song(song)

            song = Song(user_id=current_user.id,
                        mbid=song.id,
                        cover_url=form.cover_url.data,
                        title=form.title.data,
                        artist=form.artist.data,
                        release=form.release.data,
                        year=form.year.data,
                        lyrics=session["lyrics"],
                        notes=session["notes"],
                        capo=session["capo"],
                        added=datetime.now(),
                        last_changed=datetime.now(),
                        num_pages = pages,
                        small_font = small_font)

            session["current_song"] = song

            if pdf_path == None or img_paths == None:
                flash("Your input is malformatted.")
                return render_template('songs/configure_song.html',
                                       user=current_user,
                                       title="Add a new song",
                                       subtitle=f"{song.title} by {song.artist}",
                                       view="new",
                                       song=song,
                                       form=form,
                                       form_add=form_add,
                                       img_paths=None,
                                       pdf_path=None,
                                       pages=None,
                                       pages_str=None)

            return render_template('songs/configure_song.html',
                                   user=current_user,
                                   title="Add a new song",
                                   subtitle=f"{song.title} by {song.artist}",
                                   view="new",
                                   song=song,
                                   form=form,
                                   form_add=form_add,
                                   img_paths=img_paths,
                                   pdf_path=pdf_path,
                                   pages=len(img_paths),
                                   pages_str=str(len(img_paths)))

        elif form_add.validate_on_submit():  # else we pressed the add to collection button
            db_song = Song(user_id=current_user.id,
                           mbid=song.mbid,
                           cover_url=song.cover_url,
                           title=song.title,
                           artist=song.artist,
                           release=song.release,
                           year=song.year,
                           lyrics=session["lyrics"],
                           notes=session["notes"],
                           capo=session["capo"],
                           added=datetime.now(),
                           last_changed=datetime.now(),
                           num_pages = song.num_pages,
                           small_font = song.small_font)

            already_in_collection = False
            for s in current_user.songs:
                if s.equal(db_song):
                    flash("A song with this metadata is already in your collection.")
                    already_in_collection = True
                    break

            if not already_in_collection:
                db.session.add(db_song)
                db.session.commit()
                flash(f"Successfully added song {song.title} by {song.artist} to your collection.")

            return redirect(url_for("songs.collection"))

        # We came here from the selection page
        return render_template('songs/configure_song.html',
                               user=current_user,
                               title="Add a new song",
                               subtitle=f"{song.title} by {song.artist}",
                               view="new",
                               song=song,
                               form=form,
                               form_add=form_add,
                               img_paths=None,
                               pdf_path=None,
                               pages=None,
                               pages_str=None)


@bp.route('/collection/edit', methods=["POST"])
def edit():
    # Load all data. If the page is called with one arg, take it as song id, else read it
    # from the session
    delete_user_temp_files()

    args = list(request.form.items())
    if len(args) == 1:
        song_db_id = args[0][0]
        session["current_song_db_id"] = song_db_id
    else:
        song_db_id = session["current_song_db_id"]

    song = Song.query.get(song_db_id)

    form = LyricsForm()
    form_add = None

    if form.validate_on_submit():  # we pressed the apply button
        song.title = form.title.data
        song.artist = form.artist.data
        song.release = form.release.data
        song.year = int(form.year.data)
        song.notes = form.notes.data
        song.capo = form.capo.data
        song.last_changed = datetime.now()
        song.cover_url = form.cover_url.data
        song.num_pages = song.num_pages
        song.small_font = song.small_font

        already_in_collection = False
        for s in current_user.songs:
            if s.equal(song) and s.id != song.id:
                flash("A song with this metadata is already in your collection.")
                already_in_collection = True
                break

        if already_in_collection:
            flash("A song with this metadata is already in your collection.")
        else:
            db.session.commit()

        session["lyrics"] = form.lyrics.data
        song.lyrics = form.lyrics.data
        
        pdf_path, img_paths, pages, small_font = build_song(song)

        if pdf_path == None or img_paths == None:
            flash("Your input is malformatted.")
            return render_template('songs/configure_song.html',
                                   user=current_user,
                                   title="Edit a song",
                                   subtitle=f"{song.title} by {song.artist}",
                                   view="edit",
                                   song=song,
                                   form=form,
                                   form_add=form_add,
                                   img_paths=None,
                                   pdf_path=None,
                                   pages=None,
                                   pages_str=None)

        
        song.num_pages = pages
        song.small_font = small_font

        db.session.commit()

        return render_template('songs/configure_song.html',
                               user=current_user,
                               title="Edit a song",
                               subtitle=f"{song.title} by {song.artist}",
                               view="edit",
                               song=song,
                               form=form,
                               form_add=form_add,
                               img_paths=img_paths,
                               pdf_path=pdf_path,
                               pages=len(img_paths),
                               pages_str=str(len(img_paths)))

    # if we call the page from the colletion page, show initial data
    session["lyrics"] = song.lyrics
    pdf_path, img_paths, pages, small_font = build_song(song)

    if pdf_path == None or img_paths == None:
        flash("Somethin went wrong. Could not build lyrics.")
        return redirect(url_for("songs.collection"))

    form.lyrics.data = song.lyrics
    form.capo.data = song.capo
    form.notes.data = song.notes

    return render_template('songs/configure_song.html',
                           user=current_user,
                           title="Edit a song",
                           subtitle=f"{song.title} by {song.artist}",
                           view="edit",
                           song=song,
                           form=form,
                           form_add=form_add,
                           img_paths=img_paths,
                           pdf_path=pdf_path,
                           pages=len(img_paths),
                           pages_str=str(len(img_paths)),
                           current_song_db_id=song_db_id)


@bp.route('/collection/download', methods=["POST"])
def download():
    delete_user_temp_files()

    args = list(request.form.items())
    song_db_id = args[0][0]

    song = Song.query.get(song_db_id)

    pdf_path, img_paths, pages, small_font = build_song(song)
    path = os.path.join(*pdf_path.split("/")[1:])
    return send_file(path, as_attachment=True)


@bp.route('/collection/delete', methods=["POST"])
def delete():
    delete_user_temp_files()

    args = list(request.form.items())
    song_db_id = args[0][0]

    song = Song.query.get(song_db_id)
    db.session.delete(song)
    db.session.commit()

    flash(f"Successfully removed song {song.title} by {song.artist} from your collection.")

    return redirect(url_for("songs.collection"))


def build_song(song):
    path = get_user_path("")

    if not os.path.exists("app/static"):
        os.mkdir("app/static")
    if not os.path.exists("app/static/tmp"):
        os.mkdir("app/static/tmp")
    if not os.path.exists(path):
        os.mkdir(path)

    return create_song(song, path)


def delete_user_temp_files():
    try:
        path = get_user_path("")
        if os.path.exists(path):
            for f in os.listdir(path):
                os.remove(os.path.join(path, f))
    except:
        print(f"ERROR Unable to delete user directory: {path}\nProbably latex was building...")


def get_user_path(file):
    split = file.split(".")[:-1]
    p = ".".join(split)
    s = file.split(".")[-1]

    return f"{get_user_file_name(p)}{f'.{s}' if len(split) > 1 else ''}"


def get_user_file_name(filename):
    ip = "noip"
    # if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
    #     ip = request.environ['REMOTE_ADDR']
    # else:
    #     ip = request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
    # info = ip

    if "userid" not in list(session.keys()):
        session["userid"] = current_user.id  # str(uuid.uuid4())

    info = session["userid"]

    return f"app/static/tmp/{filename}_{info}"
