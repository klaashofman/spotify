from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
import yaml
import readline
import argparse

COMMANDS = ['play', 'pause', 'next', 'previous', 'podcasts', 'playlists', 'artists', 'albums', 'exit']

# FAQ: finding spotify URI's and ID's
# https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids

# Function to handle autocompletion
def completer(text, state):
    options = [cmd for cmd in COMMANDS if cmd.startswith(text)] + [None]    
    return options[state]

@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str

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

        cfg = SpotifyConfig(client_id=client_id, 
                            client_secret=client_secret, 
                            redirect_uri=redirect_uri, 
                            scope=scope)

        for podcast in config['podcasts']:
            name = podcast
            uri = config['podcasts'][podcast]
            fav = Favourite(name=name, type='podcast', uri=uri, external_url='unknown')
            favs.append(fav)
        
        return cfg, favs

    except KeyError as e:
        print(f"Error loading config: {e}")
        return None,None

def connect(cfg: SpotifyClientCredentials) -> spotipy.Spotify:

    try:
        # TODO: remove this and use the client credentials flow
        auth_manager=SpotifyOAuth(client_id=cfg.client_id,
                                    client_secret=cfg.client_secret,
                                    redirect_uri=cfg.redirect_uri, 
                                    scope=cfg.scope)
        return spotipy.Spotify(auth_manager=auth_manager)
    except Exception as e:
        print(f"Error connecting to Spotify: {e}")
        return None


def get_current_user_playlist(sp):
    playlists = sp.current_user_playlists()
    for i, item in enumerate(playlists['items']):
        print("%d %s" % (i, item['name']))

def play(sp: spotipy.Spotify):
    sp.start_playback() 

def pause(sp: spotipy.Spotify): 
    sp.pause_playback()

def next(sp: spotipy.Spotify):
    sp.next_track()

def previous(sp: spotipy.Spotify):  
    sp.previous_track()

def get_favourite_podcasts(sp: spotipy.Spotify):
    pass

def handle_command(sp, command):
    if command == 'play':
        play(sp)
    elif command == 'pause':
        pause(sp)
    elif command == 'next':
        next(sp)
    elif command == 'previous':
        previous(sp)
    elif command == 'podcasts':
        get_favourite_podcasts(sp)
    elif command == 'playlists':
        get_current_user_playlist(sp)
    elif command == 'artists':
        print("Artists")
    elif command == 'albums':
        print("Albums")
    elif command == 'exit':
        print("Exiting...")
    else:
        print("Invalid command")


def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="CLI with autocomplete")
    parser.add_argument('command', help="Command to run", choices=COMMANDS)
    
    # Configure readline to use the completer function    
    # for nix    
    # for macosx: 
    # readline.parse_and_bind("tab complete")
    readline.parse_and_bind ("bind ^I rl_complete")
    readline.set_completer_delims(' \t\n')
    readline.set_completer(completer)

    config, favs = load_config()

    sp = connect(config)
    if (sp is None):
        return

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
                parsed_args = parser.parse_args(args)
                handle_command(sp, parsed_args.command)
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except SystemExit:
            # This is raised by argparse when there's a parsing error
            pass

if __name__ == '__main__':
    main()