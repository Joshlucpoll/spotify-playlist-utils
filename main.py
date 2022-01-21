import json
import requests
import asyncio
import threading
from config import CLIENT_ID, CLIENT_SECRET, DISCORD_TOKEN, DISCORD_CHANNEL

import discord
import spotipy
from spotipy.oauth2 import SpotifyOAuth

client = discord.Client()


async def get_code(link):
    channel = client.get_channel(DISCORD_CHANNEL)
    await channel.send(f"Click [this link]({link}) to authenticate with spotify, so I can see your playlists")

    def check(m):
        return m.channel == channel

    try:
        msg = await client.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await channel.send("You took too long I'll try again later")
    else:
        return msg.content

# asyncio.run(get_code('https://joshlucpoll.com'))
loop = asyncio.get_event_loop()
loop.run_until_complete
client.start()


class ModifiedSpotifyAuth(SpotifyOAuth):
    def __init__(
            self, client_id=None, client_secret=None, redirect_uri=None,
            state=None, scope=None, cache_path=None, username=None,
            proxies=None, show_dialog=False, requests_session=True,
            requests_timeout=None, open_browser=True, cache_handler=None):
        super().__init__(client_id, client_secret, redirect_uri, state, scope,
                         cache_path, username, proxies, show_dialog, requests_session,
                         requests_timeout, open_browser, cache_handler)

    def get_access_token(self, code=None, as_dict=True, check_cache=True):
        """ Gets the access token for the app given the code

            Parameters:
                - code - the response code
                - as_dict - a boolean indicating if returning the access token
                            as a token_info dictionary, otherwise it will be returned
                            as a string.
        """
        if check_cache:
            token_info = self.validate_token(
                self.cache_handler.get_cached_token())
            if token_info is not None:
                if self.is_token_expired(token_info):
                    token_info = self.refresh_access_token(
                        token_info["refresh_token"]
                    )
                return token_info if as_dict else token_info["access_token"]

        payload = {
            "redirect_uri": self.redirect_uri,
            "code": code or input("Enter code:\n"),
            "grant_type": "authorization_code",
        }
        if self.scope:
            payload["scope"] = self.scope
        if self.state:
            payload["state"] = self.state

        headers = self._make_authorization_headers()

        try:
            response = self._session.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
                verify=True,
                proxies=self.proxies,
                timeout=self.requests_timeout,
            )
            response.raise_for_status()
            token_info = response.json()
            token_info = self._add_custom_values_to_token_info(token_info)
            self.cache_handler.save_token_to_cache(token_info)
            return token_info if as_dict else token_info["access_token"]
        except requests.exceptions.HTTPError as http_error:
            if code == 'q':
                self._handle_oauth_error(http_error)
            else:
                print('incorrect code')
                return self.get_access_token()

# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri="http://127.0.0.1:9090",
#                      scope="playlist-modify-private playlist-read-private playlist-modify-public ugc-image-upload"))


# playlists = sp.current_user_playlists()
# playlists = list(map(lambda x: x['name'], playlists['items']))
# print(json.dumps(playlists, indent=4, sort_keys=True))
'''

auth = ModifiedSpotifyAuth(
    client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
    redirect_uri="https://redirect-uri-capture.joshlucpoll.dev/spotify-callback",
    scope="playlist-modify-private playlist-read-private playlist-modify-public ugc-image-upload")

print(auth.get_authorize_url(auth.state))

sp = spotipy.Spotify(auth_manager=auth)

playlists = sp.current_user_playlists()
playlists = list(map(lambda x: x['name'], playlists['items']))
print(json.dumps(playlists, indent=4, sort_keys=True))
'''

# discord_thread = threading.Thread(target=client.run, args=(DISCORD_TOKEN))
# discord_thread.start()
