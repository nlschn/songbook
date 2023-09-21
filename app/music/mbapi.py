import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

auth_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(auth_manager=auth_manager)


class SongInfo:
    def __init__(self, id, title, artist, release, year, cover_url):
        self.id = id
        self.title = title
        self.artist = artist
        self.release = release
        self.year = year
        self.cover_url = cover_url


def search(title, artist, release):
    artist = f"artist:{artist}" if artist else ""
    release = f"album:{release}" if release else ""
    result = sp.search(q=f"track:{title} {artist} {release}", type="track", limit=50)

    songs = []
    for track in result["tracks"]["items"]:
        id = str(track["id"])
        title = track["name"]
        artist = track["artists"][0]["name"]
        album = track["album"]["name"]
        year = track["album"]["release_date"].split("-")[0]

        cover_url = None
        if track["album"]["images"]:
            cover_url = track["album"]["images"][0]["url"]

        s = SongInfo(id, title, artist, album, year, cover_url)
        songs.append(s)

    return songs
