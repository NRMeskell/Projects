import re
import sqlite3
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime

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

def san(string):
    string = string.replace("'", "''")
    return string

def addArtist(artistID, userID):
    name = sp.artist(artistID)["name"].upper()
    types = ["album", "single", "compilation"]
    for albumType in types: #look at all album types
        albums = sp.artist_albums(artistID, album_type=albumType)

        for album in albums["items"]:
            albumName =  album["name"].upper()
            if "LIVE" not in albumName:
                albumID = album["uri"]
                try:
                    addAlbum(albumID, userID)
                except:
                    pass

def addAlbum(albumID, userID):
    name = sp.album(albumID)["name"].upper()
    songs = sp.album_tracks(albumID)
    for song in songs["items"]:
        try:
            addSong(song["id"], userID)
        except:
            pass


def addPlaylist(playlistID, userID):
    name = sp.playlist(playlistID)["name"].upper()
    songs = sp.playlist_tracks(playlistID)
    for song in songs["items"]:
        song = song["track"]
        try:
            addSong(song["id"], userID)
        except:
            pass

def songAdded(songID, userID):
    songList = conn.execute("SELECT * FROM " + userID).fetchall()
    songs = [item[0] for item in songList]
    return songID in songs


def addSong(songID, userID):
    if songAdded(songID, userID):
        return
    
    song = sp.track(songID)
    title = re.split(' - | \(', song["name"])[0].strip()
    
    #concat artists (and remove ',')
    artists = ""
    for artist in song["artists"]:
        artists += artist["name"] + ", "
    artists = artists[:-2]

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

    songString = "'"+san(songID)+"','"+san(title)+"','"+san(artists)+"','"+san(album)+"','"+san(cover)+"','"+san(preview)+"',0"
    
    conn.execute("INSERT INTO " + san(userID) + f" VALUES ({songString})")
    conn.commit()


def removeSong(songID, userID):
    if songAdded(songID, userID):
        conn.execute("DELETE FROM "+san(userID)+" WHERE songID='"+san(songID)+"';")
        conn.commit()    


def removeAllSongs(userID):
    songList = conn.execute("SELECT * FROM " + san(userID)).fetchall()
    songs = [item[0] for item in songList]
    for song in songs:
        removeSong(song, userID)


    
'''
    This section focuses on adding/removing tables, and handling
    user info (usually background requests)
'''

def tableExists(userID):
    tableList = conn.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()
    tables = [item[1] for item in tableList]
    return userID in tables 


def createTable(userID):
    collumns = "songID TEXT UNIQUE, title TEXT, artist TEXT, album TEXT, cover TEXT, preview TEXT, rank INTEGER"
    conn.execute("CREATE TABLE " + san(userID) + " (" + collumns + ");")

    conn.execute("INSERT INTO users VALUES ('"+san(userID)+"',0);")
    conn.commit()


def getSongList(userID):
    songsBasic = conn.execute("SELECT * FROM " + san(userID)).fetchall()
    songs = []
    for song in songsBasic:
        songs.append((song[0], song[1], song[2], song[3], song[4], song[5], song[6]))
    return songs


def songNumber(userID):
    songsBasic = conn.execute("SELECT * FROM " + san(userID)).fetchall()
    return len(songsBasic)


#Update the current users last login day
def updateUser(userID):
    date = datetime.now()
    conn.execute("UPDATE users SET active="+str(date.day)+" WHERE user='"+san(userID)+"';")
    conn.commit()
    

#This is a mark and sweep functionality 
def sweepData():
    date = datetime.now()

    #create mark dictionary for all currently active user tables
    tableList = conn.execute("SELECT * FROM sqlite_master WHERE type='table'").fetchall()
    tables = {item[1]: False for item in tableList}
    tables.pop("users")
    
    #mark live tables and remove dead users from user list
    users = conn.execute("SELECT * FROM users").fetchall()
    for user in users:
        if (user[0] in tables) and abs(user[1] - date.day) <= 7:
            tables[user[0]] = True
        else:
            conn.execute("DELETE FROM users WHERE user='" + san(user[0]) + "'")

    #remove unmarked users from data table
    for table in tables:
        if tables[table] == False:
            conn.execute("DROP TABLE " + san(table))

    #finalize changes
    conn.commit()

#rerank song pOld to rank of pNew
def updateSongRank(userID, pOld, pNew):
    conn.execute("UPDATE "+userID+" SET rank="+str(pNew)+" WHERE rank="+str(pOld)+";")
    conn.commit()


#initialize ranking of songs randomly
def initSongRank(userID):
    songList = conn.execute("SELECT * FROM " + userID).fetchall()
    songs = [item[0] for item in songList]
    for i in range(len(songs)):
        conn.execute("UPDATE "+userID+" SET rank="+str(i)+" WHERE songID='"+san(songs[i])+"';")
    conn.commit()

    
def getSongOfRank(userID, rank):
    songsOfRank = conn.execute("SELECT * FROM " + userID + " WHERE rank=" + str(rank)).fetchall()

    #get first song of correct rank
    return songsOfRank[0]
    
    



