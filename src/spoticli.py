from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yaml
import readline
import argparse

COMMANDS = ['play', 'pause', 'next', 'previous', 'podcasts', 'playlists', 'artists', 'albums', 'search', 'exit']

# FAQ: finding spotify URI's and ID's
# https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids

class CommandCompleter:
    commands = []

    def __init__(self, commands):
        self.commands = commands
        self.init = commands

    def update_commands(self, commands):
        self.commands.append(commands)

    def clear_commands(self):
        self.commands.clear()

    def reset_commands(self):
        self.commands = self.init
    
    def complete(self, text, state):
        options = [cmd for cmd in self.commands if cmd.startswith(text)] + [None]
        return options[state]

class Commands:
    def __init__(self):
        self.commands = []

    def add(self, command):
        self.commands.append(command)

    def remove(self, command):
        self.commands.remove(command)

    def get(self):
        return self.commands

    def reset(self):
        self.commands = []

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
    type: str
    uri: str
    external_url: str

def load_config():
    favs = []
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

        cfg = SpotifyConfig(client_id=client_id, 
                            client_secret=client_secret, 
                            redirect_uri=redirect_uri, 
                            scope=scope,
                            device_name=device_name)
        
        if 'podcasts' in config:
            for podcast in config['podcasts']:
                name = podcast
                uri = config['podcasts'][podcast]
                fav = Favourite(name=name, type='podcast', uri=uri, external_url='unknown')
                favs.append(fav)
        if 'artists' in config:
            for artist in config['artists']:
                name = artist
                uri = config['artists'][artist]
                fav = Favourite(name=name, type='artist', uri=uri, external_url='unknown')
                favs.append(fav)

        if 'albums' in config:
            for album in config['albums']:
                name = album
                uri = config['albums'][album]
                fav = Favourite(name=name, type='album', uri=uri, external_url='unknown')
                favs.append(fav)
        
        return cfg, favs

    except KeyError as e:
        print(f"Error loading config: {e}")
        return None,None

def init(cfg: SpotifyConfig) -> spotipy.Spotify:
    try:
        # TODO: remove this and use the client credentials flow
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cfg.client_id,
                                    client_secret=cfg.client_secret,
                                    redirect_uri=cfg.redirect_uri, 
                                    scope="user-library-read"),
                    client_credentials_manager=SpotifyOAuth(client_id=cfg.client_id,
                                    client_secret=cfg.client_secret,
                                    redirect_uri=cfg.redirect_uri, 
                                    scope="user-read-playback-state,user-modify-playback-state"))
    
        return sp
    except Exception as e:
        print(f"Error connecting to Spotify: {e}")
        return None

def find_device_id(sp: spotipy.Spotify, device_name):
    """ Find the device id by name
    """
    devices = sp.devices()
    for device in devices['devices']:
        if device['name'] == device_name:
            return device['id']
    
    print(f"Device {device_name} not found")
    return None

def get_current_user_playlists(sp):
    playlists = sp.current_user_playlists()
    for i, item in enumerate(playlists['items']):
        print("%d %s" % (i, item['name']))
        
def play(sp: spotipy.Spotify, dev_id, uri):
    # sp.start_playback(uris=[uri]) 
    sp.start_playback(device_id=dev_id, context_uri=uri)

def pause(sp: spotipy.Spotify, dev_id): 
    sp.pause_playback(device_id=dev_id)

def next(sp: spotipy.Spotify, dev_id):
    sp.next_track(device_id=dev_id)

def previous(sp: spotipy.Spotify, dev_id):  
    sp.previous_track(device_id=dev_id)

def search_uri_by_name(sp, name, type='show', limit=1):
    # soptify uses 'show' instead of 'podcast'
    type = 'show' if type == 'podcast' else type
    return sp.search(q=name, limit=limit, type=type)
    
def handle_command(sp, args, completer, favs, cmds,dev_id):
    command = args[0]

    if command == 'play':
        play(sp,dev_id)
    elif command == 'pause':
        pause(sp,dev_id)
    elif command == 'next':
        next(sp, dev_id)
    elif command == 'previous':
        previous(sp, dev_id)
    elif command == 'podcasts':        
        # add the podcasts to the completer
        completer.clear_commands()
        for fav in favs:
            if fav.type == 'podcast':
                # update the completer 
                completer.update_commands(fav.name) 
                cmd = { fav.name: fav.uri }
                # update the command
                cmds.add(cmd)
                    
    elif command == 'playlists':
        playlists = get_current_user_playlists(sp)
        for i, item in enumerate(playlists['items']):
            print("%d %s" % (i, item['name']))

    elif command == 'artists':
        for artist in favs:
            if artist.type == 'artist':
                completer = CommandCompleter(artist.name)
                cmd = { artist.name: artist.uri }
                cmds.add(cmd)
        
    elif command == 'albums':
        for album in favs:
            if album.type == 'album':
                completer = CommandCompleter(album.name)
                cmd = { album.name: album.uri }
                cmds.add(cmd)

    elif command == 'search':
        # concat the search string
        search = ' '.join(args[1:])
        result = search_uri_by_name(sp, search, 'artist,track,album,episode,show')        

        print(f"Artists") if result['artists']['items'] else None    
        for item in result['artists' ]['items']:
            print('\t ' + item['name'] + ' - ' + item['uri'])
            
        print(f"Albums") if result['albums']['items'] else None
        for item in result['albums' ]['items']:
            print('\t ' + item['name'] + ' - ' + item['uri'])            
        
        print(f"Tracks") if result['tracks']['items'] else None
        for item in result['tracks' ]['items']:
            print('\t ' + item['name'] + ' - ' + item['uri'])
        
        print(f"Shows") if result['shows']['items'] else None
        for item in result['shows' ]['items']:
            print('\t ' + item['name'] + ' - ' + item['uri'])
        
        print(f"Episodes") if result['episodes']['items'] else None
        for item in result['episodes' ]['items']:
            print('\t ' + item['name'] + ' - ' + item['uri'])

    elif command == 'exit':
        print("Exiting...")
    else:
        # got through the dynamic-added-commands
        for cmd in cmds.get():
            if command in cmd:
                print(f"Playing {command}")
                completer.reset_commands()
                play(sp, dev_id, uri=cmd[command])
                break


def main():
    # Create argument parser
    # parser = argparse.ArgumentParser(description="control spotify")
    # parser.add_argument('command', help="Command to run", choices=COMMANDS)
    
    # Configure readline to use the completer function    
    # for nix    
    # for macosx: 
    # readline.parse_and_bind("tab complete")
    readline.parse_and_bind ("bind ^I rl_complete")
    readline.set_completer_delims(' \t\n')
    
    completer = CommandCompleter(COMMANDS)
    readline.set_completer(completer.complete)

    config, favs = load_config()

    sp = init(config)
    if (sp is None):
        return
    
    dev_id = find_device_id(sp, config.device_name)
    if (dev_id is None):
        return
    
    cmds = Commands()

    # Get input from the user
    while True:
        try:                        
            # Prompt user input
            user_input = input("spotify-cli> ")
            
            # Split the input into a command and its arguments (if any)
            args = user_input.split()
            
            # If user types 'exit', break the loop
            if user_input.strip() == 'exit':
                print("Exiting...")
                break
            
            # Parse the user input using argparse
            if args:
                handle_command(sp, args, completer, favs, cmds, dev_id)
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except SystemExit:
            # This is raised by argparse when there's a parsing error
            pass

if __name__ == '__main__':
    main()