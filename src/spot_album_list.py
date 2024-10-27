import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pprint
import yaml

sp = spotipy.Spotify()

def load_config():
    try:
        with open('config.yaml') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print("Config file not found")
        return None, None
    
    client_id = config['spotify']['client_id']
    client_secret = config['spotify']['client_secret']
    redirect_uri = config['spotify']['redirect_uri']
    sp.auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope="user-library-read")

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


load_config()

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