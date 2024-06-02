import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import random
import math

client_id = "287b3a7af7ba4a9ebb150c3c3a2ac422"
client_secret = "ae332416541d4257826c5304953cb959"
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id, client_secret))

def addArtist(artistID, songDict):
    types = ["album", "single", "compilation"]
    for albumType in types: #look at all album types
        albums = sp.artist_albums(artistID, album_type=albumType)
        
        for album in albums["items"]:
            albumName =  album["name"].upper()
            if "LIVE" not in albumName:
                albumID = album["uri"]
                addAlbum(albumID, songDict)
    
def addAlbum(albumID, songDict):
    print("FROM " + sp.album(albumID)["name"].upper() + ":")
    songs = sp.album_tracks(albumID)
    for song in songs["items"]:
        addSong(song["id"], songDict)
            
def addPlaylist(playlistID, songDict):
    print("FROM " + sp.playlist(playlistID)["name"].upper() + ":")
    songs = sp.playlist_tracks(playlistID)
    #print(songs)
    for song in songs["items"]:
        song = song["track"]
        addSong(song["id"], songDict)
            
    
#database entry order: {name:-:artists:-:album:-:preview:-:}
def addSong(songID, songDict):
    song = sp.track(songID)
    songName = re.split(' - | \(', song["name"])[0].strip()

    singers = ""
    for singer in song["artists"]:
        singers += singer["name"] + ","
    singers = singers[:-1]

    #add album cover
    if type(song['preview_url']) == type(None):
        songURL = "https://no_preview/"
    else:
        songURL = song['preview_url']

    #add song preview
    if type(song['album']['images'][0]['url']) == type(None):
        albumURL = "https://www.tndui.com/wp-content/uploads/2022/05/placeholder.jpg"
    else:
        albumURL = song['album']['images'][0]['url']

    songDict.update({songName + ":-:" + singers : [0, songURL, albumURL, songID]})
    print("added " + songName)
    
    
def Probability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating2 - rating1) / 25))

def updateELO(song1, song2, songDict, answer, matches):
    K = 25;
    prob1win = Probability(songDict[song1][0], songDict[song2][0])
    prob2win = Probability(songDict[song2][0], songDict[song1][0])
    #update elo ratings

    if answer == "1":
        winningSong = song1
        losingSong = song2
    elif answer == "2":
        winningSong = song2
        losingSong = song1
    else:
        winningSong == "none"


    if winningSong != "none":
        matches[winningSong][0].add(losingSong)
        matches[losingSong][1].add(winningSong)

        loserLosesTo = set(matches[winningSong][1])
        winnerWinsTo = set(matches[losingSong][0])

        while len(winnerWinsTo) > 0:
            addSong = list(winnerWinsTo).pop()
            matches[winningSong][0].add(addSong)
            winnerWinsTo.update(matches[addSong][0])
            winnerWinsTo.remove(addSong)

        while len(loserLosesTo) > 0:
            addSong = list(loserLosesTo).pop()
            matches[losingSong][1].add(addSong)
            loserLosesTo.update(matches[addSong][1])
            loserLosesTo.remove(addSong)


    else:
        matches[winningSong][2].add(losingSong)
        matches[losingSong][2].add(winningSong)


    if answer == "1":
        songDict[song1][0] = songDict[song1][0] + K*(1-prob1win)
        songDict[song2][0] = songDict[song2][0] + K*(0-prob2win)
        if prob1win > 0.5:
            return True
    elif answer == "2":
        songDict[song1][0] = songDict[song1][0] + K*(0-prob1win)
        songDict[song2][0] = songDict[song2][0] + K*(1-prob2win)
        if prob2win > 0.5:
            return True
    else:
        return True

    return False
    
def compare(song1, song2, songDict, matches):   
    answer = input("\tanswer (1, 2, skip, help): ")
    while answer != "1" and answer != "2" and answer != "skip":
        print("\tvote for your favorite song! Use the following links to listen to samples:")
        print("\t(1) " + songDict[song1][1])
        print("\t(2) " + songDict[song2][1])
        answer = input("\tanswer (1, 2, skip, help): ")        
        
    print("\n")
    
    return updateELO(song1, song2, songDict, answer, matches)
        

def sortList(songDict, accuracy):
    matches = {}
    for key in songDict:
        matches[key] = (set(), set(), set())
    
    numInRow = 0
    i = 0
    questions = 0
    size = 0
    maxSize = 0
    
    while numInRow < accuracy + 1: #keep asking questions
        songs = sorted(songDict.items(), key=lambda x:x[1])
        size = len(matches[songs[len(songs)-1][0]][0]) + len(matches[songs[len(songs)-1][0]][1]) + len(matches[songs[len(songs)-1][0]][2])
        
        #GET SONGS TO CHECK
        pos1 = i
        pos2 = random.randint(0, len(songs)-1)
        while pos1 == pos2 or abs(pos1 - pos2) > max(2, len(songs)/((maxSize+1)/2)):
           pos2 = random.randint(0, len(songs)-1) 
        
        song1 = songs[pos1][0]
        song2 = songs[pos2][0]
        
        #update ELO
        if song2 in matches[song1][0]: #song1 already wins
            if updateELO(song1, song2, songDict, "1", matches):
                numInRow += 1
            else:
                numInRow = 0
            
        elif song2 in matches[song1][1]: #song2 already wins
            if updateELO(song1, song2, songDict, "2", matches):
                numInRow += 1
            else:
                numInRow = 0
                
        elif song2 in matches[song1][2]: #songs already tied
            numInRow += 1
            
        else: #user needs to decide
            questions += 1
            questionNum = str(questions) + ":"
            questionStr1 = "(1) " + song1# + "\t" + str(matches[song1][0]) + ": " + str(matches[song1][1])
            questionStr2 = "(2) " + song2# + str(matches[song2][0])  + ": " + str(matches[song2][1])
            
            print("Qeustion:", questionNum)
            print(questionStr1)
            print(questionStr2)
            
            outAnswer = compare(song1, song2, songDict, matches)
            
            
            for key in matches:
                wins = matches[key][0].copy()
                losses = matches[key][1].copy()
                for win in wins:
                    updateELO(key, win, songDict, "1", matches)
                for loss in losses:
                    updateELO(key, loss, songDict, "2", matches)
            
            if outAnswer:
                numInRow += 1
            else:
                numInRow = 0
                
            if size > maxSize:
                maxSize = size
                if maxSize != len(songs)+1:
                    print("----------------------------------")
                    print("about " +  str(round(maxSize/(len(songs)+1)*100)) + "% complete!")
                    print("----------------------------------\n")

        i+=1
        if i >= len(songs):
            i = maxSize // 4
    

def main():
    songDict = dict()
    inputType = "";
    while inputType != "done":
        print("\nChoose entry type or stop adding songs (done)")
        inputType = input("type of entry (artist, album, playlist, song, done): ")
        print("--------------------------------------")
        if inputType == "artist" or inputType == "album" or inputType == "song" or inputType == "playlist":
            url = input("spotify " + inputType + " url: ")
            print("\n")
            #try:
            if inputType == "artist":
                artist = sp.artist(url)
                artist_uri = artist["uri"]
                addArtist(artist_uri, songDict)
            elif inputType == "album":
                album = sp.album(url)
                album_uri = album["uri"]
                addAlbum(album_uri, songDict)
            elif inputType == "playlist":
                playlist = sp.playlist(url)
                playlist_uri = playlist["uri"]
                addPlaylist(playlist_uri, songDict)
            elif inputType == "song":
                song = sp.track(url)
                song_uri = song["uri"]
                addSong(song_uri, songDict)
            #except:
                #print("Invalid URL")
        elif inputType == "done":
            break
        else:
            print("Invalid input!")
        print("--------------------------------------")
            
    print("total songs:", len(songDict))
    accuracy = len(songDict)-1
    
    print("\n============================================\n")
    print("STARTING QUESTIONS!")
    print("-------------------")
    
    sortList(songDict, accuracy)

    sortedSongs = sorted(songDict.items(), key=lambda x:x[1])
    print("\n--------RANKING COMPLETE!--------\n")
    minScore = sortedSongs[0][1][0]
    maxScore = sortedSongs[len(sortedSongs)-1][1][0] - minScore
    
    for i in range(len(sortedSongs)):
        entry = sortedSongs[len(sortedSongs)-1-i]
        entryName = str(i+1) + ') ' + entry[0]
        skipSize = 65 - len(entryName)
        entryName = entryName + ' '*skipSize
        entryScore = round((entry[1][0] - minScore)/maxScore*100)
        
        print(f"{entryName}{entryScore:>10}")
    
    
main()