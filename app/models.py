from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from datetime import datetime


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


# Import every class in env.py

# In order to update database:
# > flask db migrate -m "[message]"
# > flask db upgrade

from json import JSONEncoder
from typing import Any, Type

class SongPlaylistAssociationTable(db.Model):
    __tablename__ = "song_playlist_association"
    __table_args__ = {'extend_existing': True} # for PythonAnywhere

    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.id"), primary_key = True)
    song_id = db.Column(db.Integer, db.ForeignKey("song.id"), primary_key = True)


class Playlist(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    name = db.Column(db.String(100), index=True)
    added = db.Column(db.DateTime, default = datetime.now)
    last_changed = db.Column(db.DateTime, default = datetime.now)

    share = db.Column(db.Boolean, default = False)
    share_link = db.Column(db.String(50), index = True)

    songs = db.relationship("Song", secondary = "song_playlist_association", back_populates = "playlists")

class Song(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    mbid = db.Column(db.String(200), index=True)
    release_id = db.Column(db.String(500), index=True)
    cover_url = db.Column(db.String(1000))

    title = db.Column(db.String(300), index=True)
    artist = db.Column(db.String(300), index=True)
    release = db.Column(db.String(300), index=True)
    year = db.Column(db.Integer, index=True)
    
    lyrics = db.Column(db.String(1000000), index=True)
    notes = db.Column(db.String(500), index=True)
    capo = db.Column(db.String(100), index=True)

    added = db.Column(db.DateTime, default = datetime.now)
    last_changed = db.Column(db.DateTime, default = datetime.now)

    playlists = db.relationship(Playlist, secondary = "song_playlist_association", back_populates = "songs")

    def to_dict(self):
        return {
            'id' : self.id,
            'user_id' : self.user_id,
            'mbid' : self.mbid,
            'release_id' : self.release_id,
            'cover_url' : self.cover_url,
            'title' : self.title,
            'artist' : self.artist,
            'release' : self.release,
            'year' : self.year,
            # 'lyrics' : self.lyrics,
            # 'notes' : self.notes,
            'capo' : self.capo,
            'added' : str(self.added),
            'last_changed' : str(self.last_changed),
            'playlists' : list(map(lambda p : p.id, self.playlists))
        }

    def equal(self, other):
        return (
            self.title == other.title and
            self.artist == other.artist and
            self.release == other.release and
            self.year == other.year)

    def copy(other):
        return Song(
            mbid = other.mbid,
            release_id = other.release_id,
            cover_url = other.cover_url,
            title = other.title,
            artist = other.artist,
            release = other.release,
            year = other.year,
            lyrics = other.lyrics,
            notes = other.notes,
            capo = other.capo
        )

class User(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    prename = db.Column(db.String(64), index=True, unique=True)
    surname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default = datetime.now)
    registered = db.Column(db.DateTime, default = datetime.now)

    songs = db.relationship('Song', backref='user', lazy='dynamic')
    playlists = db.relationship('Playlist', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

