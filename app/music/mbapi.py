import musicbrainzngs
import requests

musicbrainzngs.set_useragent("Songbook", "0.0.0", "taylornx77@gmail.com")

class SongInfo:
    def __init__(self, mbid, release_id, title, artist, release, year, cover_url):
        self.mbid = mbid
        self.release_id = release_id
        self.title = title
        self.artist = artist
        self.release = release
        self.year = year
        self.cover_url = cover_url

def get_cover_url(mbid):
    r = requests.get(f'http://coverartarchive.org/release/{mbid}/')

    if r.status_code == 404: return None
    
    images = r.json()["images"]

    for image in images:
        if "Front" in image["types"]:
            return image["image"]
    return None

def search(title, artist):
    result = musicbrainzngs.search_recordings(title, artist = artist)
    
    songs = []

    for recording in result['recording-list']:
        if "release-list" not in recording.keys(): continue

        release_list = recording["release-list"]

        id = recording['id']
        title = recording['title']
        artist = recording['artist-credit'][0]['name']
        
        # print(f"{title} - {artist}")
        for release in release_list:
            if not "release-group" in release.keys(): continue
            if not "type" in release['release-group'].keys(): continue
            type = release['release-group']['type'] 
            if not type in ["Album", "Single"]: continue

            album = release['title']                    
            year = None

            if "date" not in release.keys(): continue
            year = release['date'].split("-")[0]
            if not year.isnumeric(): continue

            year = int(year)
  

            s = SongInfo(id, release["id"], title, artist, album, year, None)
            
            identical_songs = list(filter(lambda x : x.title == s.title and x.artist == s.artist and x.release == x.release, songs))
            
            if len(identical_songs) == 0:
                songs.append(s)
            elif len(identical_songs) == 1:
                i = identical_songs[0]
                if s.year < i.year: 
                    songs.remove(i)
                    songs.append(s)

    songs.sort(key = lambda s : s.year)

    # for s in songs:
        # s.cover_url =  get_cover_url(s.release_id)    
        # print(f"{s.title} - {s.artist} - {s.release} ({s.year})'")
    return songs
