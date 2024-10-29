from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yaml
import readline
import pyperclip
import questionary
from questionary import prompt, Validator, ValidationError
from prompt_toolkit import prompt


# FAQ: finding spotify URI's and ID's
# https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids

@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    device_name: str

@dataclass
class Favourite:
    name: str
    description: str
    type: str
    uri: str
    external_url: str

class Spoticli:

    favs = []
    cfg: SpotifyConfig
    sp : spotipy.Spotify
    current_uri: str
    dev_id: str

    def __init__(self) -> spotipy.Spotify:
        self.load_config()
        try:
            # TODO: remove this and use the client credentials flow
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.cfg.client_id,
                                        client_secret=self.cfg.client_secret,
                                        redirect_uri=self.cfg.redirect_uri, 
                                        scope="user-library-read"),
                        client_credentials_manager=SpotifyOAuth(client_id=self.cfg.client_id,
                                        client_secret=self.cfg.client_secret,
                                        redirect_uri=self.cfg.redirect_uri, 
                                        scope="user-read-playback-state,user-modify-playback-state"))
            
            # pprint.pprint(self.sp.devices())
        
        except Exception as e:
            print(f"Error connecting to Spotify: {e}")

    
    def load_config(self):
        try:
            with open('config.yaml') as file:
                config = yaml.safe_load(file)
        except FileNotFoundError:
            print("Config file not found")
            return None, None
        
        try:
            client_id = config['spotify']['client_id']
            client_secret = config['spotify']['client_secret']
            redirect_uri = config['spotify']['redirect_uri']
            scope = config['spotify']['scope']
            device_name = config['spotify']['device_name']

            self.cfg = SpotifyConfig(client_id=client_id, 
                                client_secret=client_secret, 
                                redirect_uri=redirect_uri, 
                                scope=scope,
                                device_name=device_name,
                    )
            
            if 'podcasts' in config:
                for podcast in config['podcasts']:
                    name = podcast
                    uri = config['podcasts'][podcast]
                    fav = Favourite(name=name, type='podcast', uri=uri, external_url='unknown', description='')
                    self.favs.append(fav)
            if 'artists' in config:
                for artist in config['artists']:
                    name = artist
                    uri = config['artists'][artist]
                    fav = Favourite(name=name, type='artist', uri=uri, external_url='unknown', description='')
                    self.favs.append(fav)

            if 'albums' in config:
                for album in config['albums']:
                    name = album
                    uri = config['albums'][album]
                    fav = Favourite(name=name, type='album', uri=uri, external_url='unknown', description='')
                    self.favs.append(fav)

        except KeyError as e:
            print(f"Error loading config: {e}")
            return None,None

    def find_device_id(self, device_name):
        """ Find the device id by name
        """
        devices = self.sp.devices()
        for device in devices['devices']:
            if device['name'] == device_name:
                self.dev_id = device['id']
                return device['id']            
        
        print(f"Device {device_name} not found")
        return None
    
    def load_user_playlists(self):
        playlists = self.sp.current_user_playlists()
        for i, item in enumerate(playlists['items']):
            fav = Favourite(name=item['name'], type='playlist', uri=item['uri'], external_url=item['external_urls']['spotify'], description='')
            self.favs.append(fav)
        albums = self.get_current_user_saved_albums()
        for i, item in enumerate(albums['items']):
            fav = Favourite(name=item['album']['name'], type='album', uri=item['album']['uri'], external_url=item['album']['external_urls']['spotify'], description='')
            self.favs.append(fav)
        podcasts = self.get_current_user_saved_shows()
        for i, item in enumerate(podcasts['items']):
            fav = Favourite(name=item['show']['name'], type='podcast', uri=item['show']['uri'], external_url=item['show']['external_urls']['spotify'], description=item['show']['description'])
            self.favs.append(fav)
        

    def get_current_user_saved_albums(self, lmit=10):
        return self.sp.current_user_saved_albums(limit=lmit)
    
    def get_current_user_saved_tracks(self, lmit=10):
        return self.sp.current_user_saved_tracks(limit=lmit)
    
    def get_current_user_saved_shows(self, lmit=10):
        return self.sp.current_user_saved_shows(limit=lmit)
    
    def get_current_user_saved_episodes(self, lmit=10):
        return self.sp.current_user_saved_episodes(limit=lmit)

    def get_current_user_playlists(self):
        playlists = self.sp.current_user_playlists()
        for i, item in enumerate(playlists['items']):
            print("%d %s" % (i, item['name']))
        
    def play(self, dev_id, uri=None):
        if uri is not None:
            self.sp.start_playback(device_id=dev_id, context_uri=uri)

    def pause(self, dev_id): 
        self.sp.pause_playback(device_id=dev_id)

    def next(self, dev_id):
        self.sp.next_track(device_id=dev_id)

    def previous(self, dev_id):  
        self.sp.previous_track(device_id=dev_id)

    def search_uri_by_name(self, name, type='show', limit=1):
        # soptify uses 'show' instead of 'podcast'
        type = 'show' if type == 'podcast' else type
        return self.sp.search(q=name, limit=limit, type=type)
    
    def handle_command(self, args):
        command = args[0]

        if command == 'play':
            if pyperclip.paste() != '':
                self.current_uri = pyperclip.paste()
            self.play(self.dev_id, self.current_uri)
        elif command == 'pause':
            self.pause(self.dev_id)
        elif command == 'next':
            self.next(self.dev_id)
        elif command == 'previous':
            self.previous(self.dev_id)                        
        elif command == 'playlists':
            playlists = self.get_current_user_playlists()
            for i, item in enumerate(playlists['items']):
                print("%d %s" % (i, item['name']))

        elif command == 'search':
            # concat the search string
            category  = args[1]
            search = ' '.join(args[2:])
            result = self.search_uri_by_name(search, 'artist,track,album,episode,show')        

            if category == 'artist':
                print(f"Artists") if result['artists']['items'] else None    
                for item in result['artists' ]['items']:
                    print('\t ' + item['name'] + ' - ' + item['uri'])
                    pyperclip.copy(item['uri'])
                    
            if category == 'album':
                print(f"Albums") if result['albums']['items'] else None
                for item in result['albums' ]['items']:
                    print('\t ' + item['name'] + ' - ' + item['uri'])            
                    pyperclip.copy(item['uri'])

            if category == 'track':
                print(f"Tracks") if result['tracks']['items'] else None
                for item in result['tracks' ]['items']:
                    print('\t ' + item['name'] + ' - ' + item['uri'])
                    pyperclip.copy(item['uri'])
            
            if category == 'show' or category == 'podcast':
                print(f"Shows") if result['shows']['items'] else None
                for item in result['shows' ]['items']:
                    print('\t ' + item['name'] + ' - ' + item['uri'])
                    pyperclip.copy(item['uri'])
            
            if category == 'episode':
                print(f"Episodes") if result['episodes']['items'] else None
                for item in result['episodes' ]['items']:
                    print('\t ' + item['name'] + ' - ' + item['uri'])
                    pyperclip.copy(item['uri'])

def ask_root_command(**kwargs):
    question = questionary.autocomplete(
        "Spotify-cli>",
        validate=None,
        meta_information=  {
                "podcats": "select and play your favorite podcats",
                "playlists": "select and play your favorite playlists",
                "artists": "select and play your favorite artists",
                "albums": "select and play your favorite albums",
                "search": "search for your favorite songs",
                "play": "play the current song",
                "pause": "pause the current song",
                "previous": "play the previous song",
                "next": "play the next song",
            },
        choices=[
            "podcats",
            "playlists",
            "artists",
            "albums",
            "search",
            "play",
            "pause",
            "previous",
            "next",
        ],
        ignore_case=False,
        style=None,
        **kwargs,
    )    
    return question

def ask_podcast_command(choices, **kwargs):
    question = questionary.autocomplete(
        "Select a f{}",
        validate=None,
        choices=choices,
        ignore_case=False,
        style=None,
        **kwargs,
    )    
    return question

def main():
    
    spoticli = Spoticli()
    
    if spoticli.find_device_id(spoticli.cfg.device_name) is None:
        return    

    spoticli.load_user_playlists()

    while True:
        cmd = ask_root_command().ask()
        if cmd == 'exit':
            break
        if cmd == 'podcats':
            choices = [ fav.name for fav in spoticli.favs if fav.type == 'podcast' ]
            choices.append('exit')
            description = [ fav.description for fav in spoticli.favs if fav.type == 'podcast' ]
            podcast = questionary.select("Select a podcast", choices=choices, ).ask()
            if podcast == 'exit':
                continue
            spoticli.current_uri = [ fav.uri for fav in spoticli.favs if fav.name == podcast ][0]
            spoticli.play(spoticli.dev_id, spoticli.current_uri)
        if cmd == 'artists':
            choices = [ fav.name for fav in spoticli.favs if fav.type == 'artist' ]
            choices.append('exit')
            artist = questionary.select("Select an artist", choices=choices).ask()
            if podcast == 'exit':
                continue
            spoticli.current_uri = [ fav.uri for fav in spoticli.favs if fav.name == artist ][0]
            spoticli.play(spoticli.dev_id, spoticli.current_uri)
        if cmd == 'albums':
            choices = [ fav.name for fav in spoticli.favs if fav.type == 'album' ]
            choices.append('exit')
            album = questionary.select("Select an album", choices=choices).ask()
            if album == 'exit':
                continue
            spoticli.current_uri = [ fav.uri for fav in spoticli.favs if fav.name == album ][0]
            spoticli.play(spoticli.dev_id, spoticli.current_uri)
        if cmd == 'playlists':
            choices = [ fav.name for fav in spoticli.favs if fav.type == 'playlist' ]
            choices.append('exit')
            playlist = questionary.select("Select a playlist", choices=choices).ask()
            if playlist == 'exit':
                continue
            spoticli.current_uri = [ fav.uri for fav in spoticli.favs if fav.name == playlist ][0]
            spoticli.play(spoticli.dev_id, spoticli.current_uri)
        if cmd == 'play':
            spoticli.play(spoticli.dev_id, spoticli.current_uri)
        if cmd == 'pause':
            spoticli.pause(spoticli.dev_id)
        if cmd == 'next':
            spoticli.next(spoticli.dev_id)
        if cmd == 'previous':
            spoticli.previous(spoticli.dev_id)

        

if __name__ == '__main__':
    main()