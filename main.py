from datetime import datetime
import json
import asyncio

import discord
import spotipy
from spotipy.oauth2 import SpotifyOauthError
from modifiedSpotifyAuth import ModifiedSpotifyAuth

from config import CLIENT_ID, CLIENT_SECRET, DISCORD_TOKEN, DISCORD_CHANNEL

client = discord.Client()


async def get_access_token_discord(sp, auth, channel):
    while True:
        try:
            sp.current_user()
        except SpotifyOauthError:
            link = auth.get_authorize_url(auth.state)
            embed = discord.Embed(
                title="I need an access token",
                description="To edit your playlists I need an access token. Click the title link and sign in with spotify. Paste the 'code' parameter back into this channel",
                url=link,
                timestamp=datetime.utcnow(),
                color=0x1DB954
            )
            await channel.send(embed=embed)

            def check(m):
                return m.channel == channel

            try:
                msg = await client.wait_for('message', check=check, timeout=120.0)
            except asyncio.TimeoutError:
                await channel.send("You took too long I'll try again later")
                return False

            else:
                if msg.content == 'q' or msg.content == 'Q':
                    await channel.send("I'll try again later")
                    return False
                try:
                    auth.get_access_token(code=msg.content)
                    return True
                except SpotifyOauthError:
                    await channel.send("Incorrect access code, try again (type 'q' if you want to cancel)")


@client.event
async def on_ready():
    auth = ModifiedSpotifyAuth(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
        redirect_uri="https://redirect-uri-capture.joshlucpoll.dev/spotify-callback",
        scope="playlist-modify-private playlist-read-private playlist-modify-public ugc-image-upload")

    sp = spotipy.Spotify(auth_manager=auth)
    channel = client.get_channel(int(DISCORD_CHANNEL))

    got_token = await get_access_token_discord(sp, auth, channel)

    if got_token:
        playlists = sp.current_user_playlists()
        playlists = list(map(lambda x: x['name'], playlists['items']))
        await channel.send(json.dumps(playlists, indent=4, sort_keys=True))

    await client.close()


client.run(DISCORD_TOKEN)
