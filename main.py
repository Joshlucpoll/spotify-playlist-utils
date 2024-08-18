from datetime import datetime
from dateutil import parser
from functools import cmp_to_key
from io import BytesIO
import os
import base64
import asyncio
import random
import requests
from enum import Enum

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from PIL import Image
import discord
import spotipy
from spotipy.oauth2 import SpotifyOauthError
from tenacity import retry, stop_after_attempt, wait_fixed
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
PLAYLISTS_TO_RANDOM_INTERVAL = getEnvVar("PLAYLISTS_TO_RANDOM_INTERVAL")
CRON_STRING = getEnvVar("CRON_STRING")


file_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(file_path)

started = False
client = discord.Client()


class GeneratedType(Enum):
    SHUFFLED = 1
    NEWEST = 2
    RANDOM_INTERVAL = 3


def addImageToPlaylist(sp, img_url, patch_img_path, playlist_id):
    response = requests.get(img_url)
    img = Image.open(BytesIO(response.content))
    sticker_img = Image.open(patch_img_path)

    width, height = img.size

    sticker_img.thumbnail((width / 3, width / height * sticker_img.size[0]))

    img.paste(
        sticker_img,
        (
            round((img.size[0] - img.size[1]) / 2 + img.size[1] / 50),
            round(img.size[1] - sticker_img.size[1] - img.size[1] / 50),
        ),
        sticker_img,
    )

    buffered = BytesIO()
    img.thumbnail((300, 300))
    # img.show()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())

    sp.playlist_upload_cover_image(playlist_id, img_str)


@retry(wait=wait_fixed(30), stop=stop_after_attempt(3))
def get_generated_playlist(sp, original_playlist_id: str, type: GeneratedType):
    # Get all the playlists for the user
    results = sp.user_playlists(sp.me()["id"])

    # Get all the playlists
    playlists = results["items"]
    while results["next"]:
        results = sp.next(results)
        playlists.extend(results["items"])

    # Check if the playlist already exists
    for playlist in playlists:
        if original_playlist_id + str(type.value) in playlist["description"]:
            return playlist

    original_playlist = sp.playlist(original_playlist_id)
    description = f"{type.name.replace('_', ' ').title()} version of {original_playlist['name']}   •   {original_playlist_id + str(type.value)}? <-- DO NOT DELETE THIS ID"

    # If the playlist doesn't exist create it
    return sp.user_playlist_create(
        sp.me()["id"],
        original_playlist["name"] + " " + type.name.replace("_", " ").title(),
        public=PLAYLIST_ARE_PUBLIC,
        description=description,
    )


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]


@retry(wait=wait_fixed(30), stop=stop_after_attempt(3))
def update_shuffle_playlist(sp, playlist_id, tracks):
    # Get the track ids
    tracks_id = list(map(lambda track: track["track"]["id"], tracks))

    # Remove any None values
    tracks_id = list(filter(lambda track: track, tracks_id))
    random.shuffle(tracks_id)
    tracksGrouped = list(divide_chunks(tracks_id, 100))

    # Get the generated playlist
    generated_playlist = get_generated_playlist(sp, playlist_id, GeneratedType.SHUFFLED)

    # Clean generated playlist by removing all the tracks from the generated playlist
    for trackGroup in tracksGrouped:
        sp.playlist_remove_all_occurrences_of_items(
            generated_playlist["id"], trackGroup
        )

    # Add the shuffled tracks to the generated playlist
    tracks_id = tracks_id[:50]
    sp.playlist_add_items(generated_playlist["id"], tracks_id)

    addImageToPlaylist(
        sp,
        sp.playlist(playlist_id)["images"][0]["url"],
        "shuffle.png",
        generated_playlist["id"],
    )


@retry(wait=wait_fixed(30), stop=stop_after_attempt(3))
def update_newest_playlist(sp, playlist_id, tracks):
    # Remove any None values
    tracks = list(filter(lambda track: track["track"]["id"] != None, tracks))

    def compareDateAdded(a, b):
        return parser.parse(a["added_at"]) < parser.parse(b["added_at"])

    # Sort the tracks by date added (newest first)
    tracks = sorted(tracks, key=cmp_to_key(compareDateAdded), reverse=False)
    tracks.reverse()

    # Get the track ids
    track_ids = list(map(lambda track: track["track"]["id"], tracks))
    tracksGrouped = list(divide_chunks(track_ids, 100))

    # Get the generated playlist
    generated_playlist = get_generated_playlist(sp, playlist_id, GeneratedType.NEWEST)

    # Clean generated playlist by removing all the tracks from the generated playlist
    for trackGroup in tracksGrouped:
        sp.playlist_remove_all_occurrences_of_items(
            generated_playlist["id"], trackGroup
        )

    # Add the shuffled tracks to the generated playlist
    for trackGroup in tracksGrouped:
        sp.playlist_add_items(generated_playlist["id"], trackGroup)

    addImageToPlaylist(
        sp,
        sp.playlist(playlist_id)["images"][0]["url"],
        "new.png",
        generated_playlist["id"],
    )


@retry(wait=wait_fixed(30), stop=stop_after_attempt(3))
def update_random_interval_playlist(sp, playlist_id, tracks):
    # Remove any None values
    tracks = list(filter(lambda track: track["track"]["id"] != None, tracks))

    def compareDateAdded(a, b):
        return parser.parse(a["added_at"]) < parser.parse(b["added_at"])

    # Sort the tracks by date added (newest first)
    tracks = sorted(tracks, key=cmp_to_key(compareDateAdded), reverse=False)
    tracks.reverse()

    # Get the track ids
    track_ids = list(map(lambda track: track["track"]["id"], tracks))

    # divide songs into chunks of 100 for api limit
    tracksGrouped = list(divide_chunks(track_ids, 100))

    # Get the generated playlist
    generated_playlist = get_generated_playlist(
        sp, playlist_id, GeneratedType.RANDOM_INTERVAL
    )

    # Clean generated playlist by removing all the tracks from the generated playlist
    for taskGroup in tracksGrouped:
        sp.playlist_remove_all_occurrences_of_items(generated_playlist["id"], taskGroup)

    # Get 50 songs starting from a random index
    random_index = random.randint(0, len(track_ids) - 50)
    interval_track_ids = track_ids[random_index : random_index + 50]

    # Add the shuffled tracks to the generated playlist
    sp.playlist_add_items(generated_playlist["id"], interval_track_ids)

    addImageToPlaylist(
        sp,
        sp.playlist(playlist_id)["images"][0]["url"],
        "random_interval.png",
        generated_playlist["id"],
    )


@retry(wait=wait_fixed(30), stop=stop_after_attempt(3))
def get_playlist_songs(sp: spotipy.Spotify, playlist_id):
    print(f"Getting playlist songs for {playlist_id}, user: {sp.me()['id']}")
    results = sp.playlist_items(playlist_id)

    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])

    return tracks


def get_all_playlists(sp):
    playlist_ids = set(
        [
            *PLAYLISTS_TO_RANDOM_INTERVAL,
            *PLAYLISTS_TO_RANDOM_INTERVAL,
            *PLAYLISTS_TO_NEWEST,
        ]
    )

    # Remove any None values and blanks
    playlist_ids = list(filter(lambda playlist: playlist, playlist_ids))

    playlists = {}

    for playlist_id in playlist_ids:
        tracks = []

        for track in get_playlist_songs(sp, playlist_id):
            tracks.append(track)

        playlists[playlist_id] = tracks

    return playlists


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
            print("Waiting for access token...")

            def check(m):
                return m.channel == channel

            try:
                msg = await client.wait_for("message", check=check, timeout=120.0)
            except asyncio.TimeoutError:
                await channel.send("You took too long I'll try again later")
                print("Access Token Timeout")
                return False

            else:
                if msg.content == "q" or msg.content == "Q":
                    await channel.send("I'll try again later")
                    print("User cancelled")
                    return False
                try:
                    auth.get_access_token(code=msg.content)
                    print("Got access token!")
                    return True
                except SpotifyOauthError:
                    print("Incorrect access code")
                    await channel.send(
                        "Incorrect access code, try again (type 'q' if you want to cancel)"
                    )


async def run(channel):
    try:
        print("Running job...")
        auth = ModifiedSpotifyAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri="https://redirect-uri-capture.joshlucpoll.dev/spotify-callback",
            scope="playlist-modify-private playlist-read-private playlist-modify-public ugc-image-upload",
        )

        sp = spotipy.Spotify(auth_manager=auth, requests_timeout=20)

        got_token = await get_access_token_discord(sp, auth, channel)

        if got_token:

            all_playlists = get_all_playlists(sp)

            for playlist_id, tracks in all_playlists.items():
                if playlist_id in PLAYLISTS_TO_SHUFFLE:
                    update_shuffle_playlist(sp, playlist_id, tracks)
                    print(f"Updating shuffle playlist {playlist_id}")

                if playlist_id in PLAYLISTS_TO_NEWEST:
                    update_newest_playlist(sp, playlist_id, tracks)
                    print(f"Updating newest playlist {playlist_id}")

                if playlist_id in PLAYLISTS_TO_RANDOM_INTERVAL:
                    update_random_interval_playlist(sp, playlist_id, tracks)
                    print(f"Updating random interval playlist {playlist_id}")

            await channel.send("Success! Playlists updated")
            print("Job done!")

    except Exception as e:
        embed = discord.Embed(
            title="An error occurred",
            description=e,
            timestamp=datetime.utcnow(),
            color=0xFF0000,
        )
        await channel.send(embed=embed)
        print(e)


def parse_cron(cron_string):
    # splits the string into a list
    cron_list = cron_string.split()

    # creates a dictionary with the minute and the hour for APScheduler
    out = {
        "minute": cron_list[0] if cron_list[0] != "*" else None,
        "hour": cron_list[1] if cron_list[1] != "*" else None,
        "day": cron_list[2] if cron_list[2] != "*" else None,
        "month": cron_list[3] if cron_list[3] != "*" else None,
        "day_of_week": cron_list[4] if cron_list[4] != "*" else None,
    }

    # remove None values from the dictionary
    out = {k: v for k, v in out.items() if v is not None}

    return out


@client.event
async def on_ready():
    global started

    if not started:
        channel = client.get_channel(int(DISCORD_CHANNEL))

        scheduler = AsyncIOScheduler()
        print("Initialising scheduler...")

        # get cron schedule
        cron_schedule = parse_cron(CRON_STRING)

        # Add a job to be run using cron string
        scheduler.add_job(run, args=[channel])
        scheduler.add_job(
            run, trigger="cron", **cron_schedule, args=[channel], coalesce=True
        )
        print("Scheduling jobs...")

        scheduler.start()
        started = True

        print("Scheduler running!")


@client.event
async def on_message(message):
    channel = message.channel

    # we do not want the bot to reply to itself
    if "update" in message.content and message.author != client.user:
        print("Updating playlists manually...")
        await channel.send("Updating playlists, please wait...")
        await run(channel)


client.run(DISCORD_TOKEN)
