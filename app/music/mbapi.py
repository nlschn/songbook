import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def read_credentials():
    with open("credentials.txt") as file:
        lines = file.readlines()
        client_id = lines[0].strip()
        client_secret = lines[1].strip()
        return client_id, client_secret
    
client_id, client_secret = read_credentials()

auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
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
