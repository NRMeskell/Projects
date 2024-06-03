import re
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

client_id = "287b3a7af7ba4a9ebb150c3c3a2ac422"
client_secret = "ae332416541d4257826c5304953cb959"
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id, client_secret))

conn = sqlite3.connect("songs.db", check_same_thread=False)

'''
    CODE FOR MANIPULATING THE SONG DATABASE
    spotify user is a flag for which table in
    the songs.db database you are adding/removing songs from

    SONGS.DB has a table of songs for each current user
             which tracks the songs they are currently sorting
'''


'''
    This section focuses on adding/removing songs from the
    database - (usually user inputs)
'''

def addArtist(artistID, spotifyUser):
    name = sp.artist(artistID)["name"].upper()
    types = ["album", "single", "compilation"]
    for albumType in types: #look at all album types
        albums = sp.artist_albums(artistID, album_type=albumType)

        for album in albums["items"]:
            albumName =  album["name"].upper()
            if "LIVE" not in albumName:
                albumID = album["uri"]
                addAlbum(albumID, dataBase)


def addAlbum(albumID, spotifyUser):
    name = sp.album(albumID)["name"].upper()
    comments.append("FROM " + name + ":")
    songs = sp.album_tracks(albumID)
    for song in songs["items"]:
        addSong(song["id"], dataBase)


def addPlaylist(playlistID, spotifyUser):
    name = sp.playlist(playlistID)["name"].upper()
    comments.append("FROM " + name + ":")
    songs = sp.playlist_tracks(playlistID)
    for song in songs["items"]:
        song = song["track"]
        addSong(song["id"], dataBase)


def addSong(songID, spotifyUser):
    song = sp.track(songID)
    title = re.split(' - | \(', song["name"])[0].strip()
    
    #concat artists (and remove ',')
    artists = ""
    for artist in song["artists"]:
        artists += artist["name"] + ","
    artists = artists[:-1]

    album = song["album"]["name"]

    #add song preview
    if type(song['preview_url']) == type(None):
        preview = "https://no_preview/"
    else:
        preview = song['preview_url']

    #add album cover
    if type(song["album"]["images"][0]["url"]) == type(None):
        cover = "https://www.tndui.com/wp-content/uploads/2022/05/placeholder.jpg"
    else:
        cover = song['album']['images'][0]['url']

    songString = "'"+songID+"','"+title+"','"+artists+"','"+album+"','"+cover+"','"+preview+"'"
    print(songString)
    insert_cmd = "INSERT INTO " + spotifyUser + f" VALUES ({songString})"

    conn.execute(insert_cmd)
    conn.commit()


'''
    This section focuses on adding/removing tables, and handling
    user info (usually background requests)
'''

def tableExists(spotifyUser):
    tableList = conn.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()
    tables = [item[1] for item in tableList]
    return spotifyUser in tables


def createTable(spotifyUser):
    collumns = "songID TEXT UNIQUE, title TEXT, artist TEXT, album TEXT, cover TEXT, preview TEXT"
    conn.execute("CREATE TABLE " + spotifyUser + " (" + collumns + ");")

    conn.commit()


def getSongList(user):
    return False
    



    

    
    



