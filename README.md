# spotify-playlist-utils

## Contents
- [spotify-playlist-utils](#spotify-playlist-utils)
  - [Contents](#contents)
  - [What is this](#what-is-this)
  - [Setting up](#setting-up)
    - [Before you get started](#before-you-get-started)
    - [Download the repository](#download-the-repository)
      - [The Config File](#the-config-file)
      - [Create a Spotify Application](#create-a-spotify-application)
      - [Create Discord Bot](#create-discord-bot)
    - [Selecting the Playlists](#selecting-the-playlists)
      - [Getting Playlist ID](#getting-playlist-id)
    - [Extra Parameters](#extra-parameters)
  - [Try it out!](#try-it-out)
  - [Automation](#automation)
      - [Windows](#windows)
      - [Linux](#linux)
  - [The Redirect URI](#the-redirect-uri)

## What is this

This script is able to create a reordered playlist from your existing Spotify playlists. It was created for two reasons:

- Spotify shuffle tends to repeat the same songs over and over -- therefore this script can shuffle a playlist
- Devices that don't have an ordering function for Spotify playlists default to oldest added first (e.g. Android Auto) -- therefore this script can order a playlist with your most recent songs first

There are two playlist types the script can create:
- Shuffled
- Newest (songs added most recently are at the top by default)

This script only modifies its own playlists that it creates, that is to say the playlists you have made are not modified.

This script uses Discord as an interface for communication and authentication purposes.

## Setting up

### Before you get started

#### Download the repository

If you have `git` installed:
```
git clone https://github.com/Joshlucpoll/spotify-playlist-utils
```
else you can [download the zip](https://github.com/Joshlucpoll/spotify-playlist-utils/archive/refs/heads/main.zip) and extract it

#### The Config File

This script comes with a `config.py` file that holds all the configuration parameters

#### Create a Spotify Application

For this script to work you will need to create a Spotify application from the Spotify Developer Dashboard

1) [Create a Spotify developer account](https://developer.spotify.com/dashboard) if you have not already
2) [Visit your application dashboard](https://developer.spotify.com/dashboard/applications) and create a new app, name and description aren't important (this app is only for your personal use)
3) Click 'Edit Settings' and add this website url to the Redirect URIs section: `https://redirect-uri-capture.joshlucpoll.dev/spotify-callback` *[sidenote](##the-redirect-uri)*
4) On the dashboard for your app copy your 'Client ID' and paste it into the `config.py` file so it has this line:
   ```
   CLIENT_ID = "<Client ID>"
   ```
   where `<Client ID>` is the Client ID
5) Do the same with your 'Client Secret' (you will have to click show Client Secret):
   ```
   CLIENT_SECRET = "<Client Secret>"
   ```
   where `<Client Secret>` is the Client Secret

#### Create Discord Bot

This script uses a discord bot to gain the access token and log events, so you'll have to create one:

1) Make sure you have a Discord server and channel set up for the bot
2) [Go to your application tab](https://discord.com/developers/applications) in the Discord Developer  portal
3) Create a new application and name is appropriately
4) Go to the bot tab and create a new bot (I would recommend unchecking public bot -- so only you can use it)
5) Copy your bot token and paste it into the `config.py` file:
   ```
   DISCORD_TOKEN = "<bot token>"
   ```
   where `<bot token>` is replaced with your bot token

Now to add your bot to your server: 
1) Go to the OAuth2 tab and copy your Client ID
2) Paste this URL into your browser, replacing `<CLIENT_ID>` with the client ID from the discord bot
   ```
   https://discordapp.com/api/oauth2/authorize?client_id=<CLIENT_ID>&permissions=75840&scope=bot
   ```
3) Select server to add bot
4) In the server you just added the bot right click the channel your want the bot to use and Copy ID
5) Paste this ID into the `config.py` file:
   ```
   DISCORD_CHANNEL = <ID>
   ```
   where `<ID>` is replace with the channel ID

### Selecting the Playlists

You will need the ID of the playlists you want the script to use

#### Getting Playlist ID

To get the id of a playlist, right click it then `Share > Copy link to playlist`. This will give you a link to your playlist in the format:
```
https://open.spotify.com/playlist/<PLAYLIST_ID>?si=<SI>
```
where `<PLATLIST_ID>` and `<SI>` are random strings of characters

Copy your playlist id and paste it into the `config.py` file:
```
PLAYLISTS_TO_SHUFFLE = ["<PLAYLIST_ID_1>", "<PLAYLIST_ID_2>", "<PLAYLIST_ID_3>"]
PLAYLISTS_TO_NEWEST = ["<PLAYLIST_ID_1>", "<PLAYLIST_ID_2>"]
```
where `<PLAYLIST_ID_x>` are your playlist IDs

**note** `PLAYLISTS_TO_SHUFFLE` and `PLAYLISTS_TO_NEWEST` can have zero or more values -- if there are zero values: `PLAYLISTS_TO_SHUFFLE = []`

### Extra Parameters

In the `config.py` file you will also find a `PLAYLIST_ARE_PUBLIC` constant. This alters the the output playlist visibility, either `True` or `False`

## Try it out!

Run the `main.py` script (if you don't have python installed, you can follow [this guide](https://realpython.com/installing-python/))

The first time you run it you should get a discord message asking for an access code. Click the link and sign in with your Spotify account. Copy the access code from the capture website and paste it back into the same channel.

If successful you should have new playlists create within your account!

## Automation

It is possible to automatically update these playlists on a regular basis using a schedular

Depending on if you are on [Windows](#windows) or [Linux](#linux) this is achieved in different ways.

#### Windows

1. Create a `.bat` file in the same directory as `main.py` and enter `<Your Python.exe Path> <Path to main.py>` into it.

e.g. `"C:\Users\username\AppData\Local\Programs\Python\Python39" "C:\Users\username\Documents\spotify-playlist-utils\main.py"`

1. Search for Task Scheduler, and open it:
![](https://miro.medium.com/max/700/1*mZQ2Zy5su6r8QzCaGpLckw.png)

3. Click 'Create Basic Task' and name the task something appropriate:
![](https://miro.medium.com/max/700/1*rcZMqC46mIHnEkvTCNY87w.png)

4. Then choose daily as the trigger and leave the start date and time as is
![](https://miro.medium.com/max/700/1*xVl7Y3UWv4dGDV9GFCE8Ww.png)

5. Select 'Start a program' as the action:
![](https://miro.medium.com/max/700/1*qvt7Z6rQE_MpoNqONhXd8w.png)

6. Browse for the `.bat` file you just created and select it. **Make sure you include the 'Start in' parameter**, input the path to the folder where the `main.py` file is located:
e.g. `C:\Users\username\Documents\spotify-playlist-utils`
![](https://i.imgur.com/k3gKasO.png)

7. Click Finish! Now Task Schedular should execute the script every day.


#### Linux

1. Open crontab file: `crontab -e`
If this command fails, it's likely that cron is not installed. If you use a Debian based system (Debian, Ubuntu), try the following commands first: 
`sudo apt-get update`
`sudo apt-get install cron`
2. A text-editor will appear, add this line to file:
`0 8 * * * python3 <Path to main.py>`
3. Save file and exit.

This cron job executes daily at 8:00 am. You can adjust the time at which it executes by changing values as such:
`<minute> <hour> * * * python3 <Path to main.py>`

And your done! Cron should execute the script every day.



## The Redirect URI

For the script to read your playlists it needs to gain an access token from Spotify. This is done by creating a URL that points to Spotify asking you to authenticate. Once you sign in spotify sends an access code to a callback URL. Therefore, to capture this code, I have created a simple [website](https://redirect-uri-capture.joshlucpoll.dev/spotify-callback) that extracts the code allowing your to copy it back into discord. This website's source code in [available here](https://github.com/joshlucpoll/redirect-uri-capture)

