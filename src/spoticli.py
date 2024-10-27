from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yaml
import readline
import pyperclip
import argparse
import pprint


# FAQ: finding spotify URI's and ID's
# https://developer.spotify.com/documentation/web-api/concepts/spotify-uris-ids

class CommandCompleter:
    commands = []

    def __init__(self, commands):
        self.commands = commands
        self.init = self.commands

    def update_commands(self, commands):
        # self.commands.append(commands)
        # put the added commands at the beginning
        self.commands.insert(0, commands)

    def clear_commands(self):
        # self.commands.clear()
        pass

    def reset_commands(self):
        # self.commands = self.init
        pass
    
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

class SpotiCli:

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
                    fav = Favourite(name=name, type='podcast', uri=uri, external_url='unknown')
                    self.favs.append(fav)
            if 'artists' in config:
                for artist in config['artists']:
                    name = artist
                    uri = config['artists'][artist]
                    fav = Favourite(name=name, type='artist', uri=uri, external_url='unknown')
                    self.favs.append(fav)

            if 'albums' in config:
                for album in config['albums']:
                    name = album
                    uri = config['albums'][album]
                    fav = Favourite(name=name, type='album', uri=uri, external_url='unknown')
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
    
    def handle_command(self, args, completer, cmds):
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
        elif command == 'podcasts':        
            for fav in self.favs:
                if fav.type == 'podcast':
                    # update the completer 
                    completer.update_commands(fav.name) 
                    cmd = { fav.name: fav.uri }
                    # update the command
                    cmds.add(cmd)
                        
        elif command == 'playlists':
            playlists = self.get_current_user_playlists()
            for i, item in enumerate(playlists['items']):
                print("%d %s" % (i, item['name']))

        elif command == 'artists':
            for artist in self.favs:
                if artist.type == 'artist':
                    completer.update_commands(artist.name)
                    cmd = { artist.name: artist.uri }
                    cmds.add(cmd)
            
        elif command == 'albums':
            for album in self.favs:
                if album.type == 'album':
                    completer.update_commands(album.name)
                    cmd = { album.name: album.uri }
                    cmds.add(cmd)

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

        elif command == 'exit':
            print("Exiting...")
        else:
            # got through the dynamic-added-commands
            for cmd in cmds.get():
                if command in cmd:
                    print(f"Playing {command}")
                    uri = cmd[command]
                    self.play(self.dev_id, uri)
                    self.current_uri = uri
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
    
    COMMANDS = ['play', 'pause', 'next', 'previous', 'podcasts', 'playlists', 'artists', 'albums', 'search', 'exit']
    completer = CommandCompleter(COMMANDS)
    readline.set_completer(completer.complete)

    spotiCli = SpotiCli()
    
    if spotiCli.find_device_id(spotiCli.cfg.device_name) is None:
        return
        
    cmds = Commands()

    # Get input from the user
    while True:
        try:                        
            # Prompt user input
            user_input = input("spoticli> ")
            
            # Split the input into a command and its arguments (if any)
            args = user_input.split()
            
            # If user types 'exit', break the loop
            if user_input.strip() == 'exit':
                print("Exiting...")
                break
            
            # Parse the user input using argparse
            if args:
                spotiCli.handle_command(args, completer, cmds)
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except SystemExit:
            # This is raised by argparse when there's a parsing error
            pass

if __name__ == '__main__':
    main()