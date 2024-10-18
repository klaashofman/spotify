import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pprint

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="b8b75255c5154d3f90297b6015746cbc",
                                               client_secret="8332d09016be4c3495875bedc750cbbb",
                                               redirect_uri="http://localhost:1234",
                                               scope="user-library-read"))


# Function to get all albums from an artist
def get_artist_albums(artist_uri):
    results = sp.artist_albums(artist_uri, album_type='album')
    albums = results['items']
    while results['next']:
        results = sp.next(results)
        albums.extend(results['items'])
    return albums

def get_current_user_playlist():
    playlists = sp.current_user_playlists()
    for i, item in enumerate(playlists['items']):
        print("%d %s" % (i, item['name']))

# name: name to search for
# type: type of item to search for artist’, ‘album’, ‘track’, ‘playlist’, ‘show’, and ‘episode’.
def search_uri_by_name(name, type, limit=1):
    # just show the first hit for now
    result = sp.search(q=name, limit=limit, type=type)
    # pprint.pprint(result)    
    for item in result[type + 's' ]['items']:
        print(item['name'])
        print(item['uri'])
        print(item['external_urls']['spotify'])
        print()
    return result


taylor_uri = 'spotify:artist:06HL4z0CvFAxyc27GXpf02'

print("Albums by Taylor Swift:")
for album in get_artist_albums(taylor_uri):
    print(album['name'])

get_current_user_playlist()
# just return the uri of the show
search_uri_by_name("Nerdland", "show")
search_uri_by_name("90 minutes", "show", limit = 5)
# same for artist
search_uri_by_name("Future Sound of London", "artist")
# same show but return the episodes
search_uri_by_name("Nerdland", "episode", 5)