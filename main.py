from datetime import datetime
from dateutil import parser
from functools import cmp_to_key
from io import BytesIO
import os
import base64
import asyncio
import random
import requests

from PIL import Image
import discord
import spotipy
from spotipy.oauth2 import SpotifyOauthError
from modifiedSpotifyAuth import ModifiedSpotifyAuth

import json
from dotenv import load_dotenv

load_dotenv()


def getEnvVar(name):
    try:
        return json.loads(os.environ[name])
    except:
        return os.environ[name]


CLIENT_ID = getEnvVar("CLIENT_ID")
CLIENT_SECRET = getEnvVar("CLIENT_SECRET")
DISCORD_TOKEN = getEnvVar("DISCORD_TOKEN")
DISCORD_CHANNEL = int(getEnvVar("DISCORD_CHANNEL"))
PLAYLIST_ARE_PUBLIC = bool(getEnvVar("PLAYLIST_ARE_PUBLIC"))
PLAYLISTS_TO_SHUFFLE = getEnvVar("PLAYLISTS_TO_SHUFFLE")
PLAYLISTS_TO_NEWEST = getEnvVar("PLAYLISTS_TO_NEWEST")

file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)

client = discord.Client()


def addImageToPlaylist(sp, img_url, patch_img_path, playlist_id):
    response = requests.get(img_url)
    img = Image.open(BytesIO(response.content))
    shuffle_img = Image.open(patch_img_path)

    width, height = img.size

    shuffle_img.thumbnail((width / 3, width / height * shuffle_img.size[0]))

    img.paste(
        shuffle_img,
        (
            round((img.size[0] - img.size[1]) / 2 + img.size[1] / 50),
            round(img.size[1] - shuffle_img.size[1] - img.size[1] / 50),
        ),
        shuffle_img,
    )

    buffered = BytesIO()
    img.thumbnail((300, 300))
    # img.show()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())

    sp.playlist_upload_cover_image(playlist_id, img_str)


def get_shuffled_generated_playlist(sp, original_playlist_id):
    results = sp.user_playlists(sp.me()["id"])

    playlists = results["items"]
    while results["next"]:
        results = sp.next(results)
        playlists.extend(results["items"])

    for playlist in playlists:
        if original_playlist_id + "?" in playlist["description"]:
            return playlist

    original_playlist = sp.playlist(original_playlist_id)

    description = "Shuffled version of {0}   ???   {1}? <-- DO NOT DELETE THIS ID".format(
        original_playlist["name"], original_playlist_id)

    return sp.user_playlist_create(
        sp.me()["id"],
        original_playlist["name"] + " Shuffled",
        public=PLAYLIST_ARE_PUBLIC,
        description=description,
    )


def get_newest_generated_playlist(sp, original_playlist_id):
    results = sp.user_playlists(sp.me()["id"])

    playlists = results["items"]
    while results["next"]:
        results = sp.next(results)
        playlists.extend(results["items"])

    for playlist in playlists:
        if original_playlist_id + "+" in playlist["description"]:
            return playlist

    original_playlist = sp.playlist(original_playlist_id)

    description = "Newest version of {0}   ???   {1}+ <-- DO NOT DELETE THIS ID".format(
        original_playlist["name"], original_playlist_id)

    return sp.user_playlist_create(
        sp.me()["id"],
        original_playlist["name"] + " Newest",
        public=PLAYLIST_ARE_PUBLIC,
        description=description,
    )


def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i: i + n]


def get_playlist_songs(sp, playlist_id):
    results = sp.user_playlist_tracks(sp.me()["id"], playlist_id)

    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])

    return tracks


def update_shuffle_playlists(sp):
    for playlist_id in PLAYLISTS_TO_SHUFFLE:
        tracks_id = []
        generated_playlist = get_shuffled_generated_playlist(sp, playlist_id)

        for track in map(
                lambda track: track["track"]["id"],
                get_playlist_songs(sp, playlist_id)):
            tracks_id.append(track)

        tracks_id = list(filter(lambda track: track, tracks_id))
        random.shuffle(tracks_id)
        tracksGrouped = list(divide_chunks(tracks_id, 100))

        for trackGroup in tracksGrouped:
            sp.playlist_remove_all_occurrences_of_items(
                generated_playlist["id"], trackGroup
            )

        tracks_id = tracks_id[:50]
        tracksGrouped = list(divide_chunks(tracks_id, 100))
        for trackGroup in tracksGrouped:
            sp.playlist_add_items(generated_playlist["id"], trackGroup)

        addImageToPlaylist(
            sp,
            sp.playlist(playlist_id)["images"][0]["url"],
            "shuffle.png",
            generated_playlist["id"],
        )


def update_newest_playlists(sp):
    for playlist_id in PLAYLISTS_TO_NEWEST:
        tracks = []
        generated_playlist = get_newest_generated_playlist(sp, playlist_id)

        for track in get_playlist_songs(sp, playlist_id):
            tracks.append(track)

        tracks = list(
            filter(lambda track: track["track"]["id"] != None, tracks))

        def compareDateAdded(a, b):
            return parser.parse(a["added_at"]) < parser.parse(b["added_at"])

        tracks = sorted(tracks, key=cmp_to_key(
            compareDateAdded), reverse=False)

        tracks.reverse()

        tracks = list(map(lambda track: track["track"]["id"], tracks))

        tracksGrouped = list(divide_chunks(tracks, 100))

        for trackGroup in tracksGrouped:
            sp.playlist_remove_all_occurrences_of_items(
                generated_playlist["id"], trackGroup
            )

        for trackGroup in tracksGrouped:
            sp.playlist_add_items(generated_playlist["id"], trackGroup)

        addImageToPlaylist(
            sp,
            sp.playlist(playlist_id)["images"][0]["url"],
            "new.png",
            generated_playlist["id"],
        )


async def get_access_token_discord(sp: spotipy.Spotify, auth, channel):
    while True:
        try:
            sp.current_user()
            return True
        except SpotifyOauthError:
            link = auth.get_authorize_url(auth.state)
            embed = discord.Embed(
                title="I need an access token",
                description="To edit your playlists I need an access token. Click the title link and sign in with spotify. Paste the 'code' parameter back into this channel",
                url=link,
                timestamp=datetime.utcnow(),
                color=0x1DB954,
            )
            await channel.send(embed=embed)

            def check(m):
                return m.channel == channel

            try:
                msg = await client.wait_for("message", check=check, timeout=120.0)
            except asyncio.TimeoutError:
                await channel.send("You took too long I'll try again later")
                return False

            else:
                if msg.content == "q" or msg.content == "Q":
                    await channel.send("I'll try again later")
                    return False
                try:
                    auth.get_access_token(code=msg.content)
                    return True
                except SpotifyOauthError:
                    await channel.send(
                        "Incorrect access code, try again (type 'q' if you want to cancel)"
                    )


@client.event
async def on_ready():
    channel = client.get_channel(int(DISCORD_CHANNEL))
    try:
        auth = ModifiedSpotifyAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri="https://redirect-uri-capture.joshlucpoll.dev/spotify-callback",
            scope="playlist-modify-private playlist-read-private playlist-modify-public ugc-image-upload",
        )

        sp = spotipy.Spotify(auth_manager=auth)

        got_token = await get_access_token_discord(sp, auth, channel)

        if got_token:
            update_shuffle_playlists(sp)
            update_newest_playlists(sp)
            await channel.send("Success! Playlists updated")

    except Exception as e:
        embed = discord.Embed(
            title="An error occurred",
            description=e,
            timestamp=datetime.utcnow(),
            color=0xFF0000,
        )
        await channel.send(embed=embed)

    finally:
        await client.close()


client.run(DISCORD_TOKEN)
