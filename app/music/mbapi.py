import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

auth_manager = SpotifyClientCredentials(client_id="cf64b192c99b401bbe9c208a2c3a6699", client_secret="e4cef14a4b31421482fbfd91ad7b9294")
sp = spotipy.Spotify(auth_manager=auth_manager)

IMAGE_INDEX = 1

class SongInfo:
    def __init__(self, id, title, artist, release, year, cover_url):
        self.id = id
        self.title = title
        self.artist = artist
        self.release = release
        self.year = year
        self.cover_url = cover_url
        self.capo = None
        self.lyrics = None
        self.notes = None
        
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
            cover_url = track["album"]["images"][IMAGE_INDEX]["url"]

        s = SongInfo(id, title, artist, album, year, cover_url)
        songs.append(s)

    return songs
