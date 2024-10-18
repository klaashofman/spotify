from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yaml
import readline
import argparse

COMMANDS = ['play', 'pause', 'next', 'previous', 'podcasts', 'playlists', 'artists', 'albums', 'exit']

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

def connect(cfg: SpotifyConfig) -> spotipy.Spotify:
    try:
        # TODO: remove this and use the client credentials flow
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=cfg.client_id,
                                    client_secret=cfg.client_secret,
                                    redirect_uri=cfg.redirect_uri, 
                                    scope=cfg.scope))
        return sp
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

def handle_command(sp, command, completer, favs, cmds):
    
    if command == 'play':
        play(sp)
    elif command == 'pause':
        pause(sp)
    elif command == 'next':
        next(sp)
    elif command == 'previous':
        previous(sp)
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
        get_current_user_playlist(sp)
    elif command == 'artists':
        print("Artists")
    elif command == 'albums':
        print("Albums")
    elif command == 'exit':
        print("Exiting...")
    else:
        for cmd in cmds.get():
            if command in cmd:
                print(f"Playing {command}")
                completer.reset_commands()
                break


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
    

    completer = CommandCompleter(COMMANDS)
    readline.set_completer(completer.complete)


    config, favs = load_config()

    sp = connect(config)
    if (sp is None):
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
                parsed_args = parser.parse_args(args)
                handle_command(sp, parsed_args.command, completer, favs, cmds)
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except SystemExit:
            # This is raised by argparse when there's a parsing error
            pass

if __name__ == '__main__':
    main()