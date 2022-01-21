import os
import sys
import json
import webbrowser
from config import CLIENT_ID, CLIENT_SECRET

import spotipy
from spotipy.oauth2 import SpotifyOAuth

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
        redirect_uri="http://127.0.0.1:9090",
        scope="playlist-modify-private playlist-read-private playlist-modify-public ugc-image-upload"))

playlists = sp.current_user_playlists()
playlists = list(map(lambda x: x['name'], playlists['items']))
print(json.dumps(playlists, indent=4, sort_keys=True))

# with open(os.path.join(sys.path[0], ".cache"), "r") as f:
#     print(json.dumps(json.loads(f.read()), indent=4))
