import math
import random
import string
from flask import Flask, render_template, request, url_for, redirect, session
import SongHandler as sh
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)
app.secret_key = 'rGRs001XJ1Y1M7jo'

app.config["DEBUG"] = True

comments = []
songDict = dict()
matches = dict()
songs = []

songFull = ["", ""]
songNames = ["", ""]
songCovers = ["", ""]
songSamples = ["", ""]
songArtists = ["", ""]

songNum = 0
maxSongNum = 0
questionNum = 0

finalList = []

#WEBPAGE CODE
#====================================================================================================================
@app.route("/", methods=["GET", "POST"])
def home():
    global questionNum
    
    #refresh page
    if request.method == "GET":
        #initialize user id (not logged in! create random client_id)
        if session.get("user") == None:
            session["user"] = "user" + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(16))
            if not sh.tableExists(session["user"]):
                sh.createTable(session["user"])

        
        #get message to display on website
        if session.get("message") == None:
            mess = ""
        else:
            mess = session["message"]
            session["message"] = ""         

        #render HTML page for user
        return render_template("main_page.html", comments=comments, message=mess, numsongs=str(len(songDict)))
    #button was pressed
    else:
        #Add songs buttons
        if request.form["cmd"] == "Add Content":

            #try logging user in
            try:
                sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(session["client_id"], session["client_secret"]))
            except:
                sp = spotipy.Spotify()

            #add content to list
            try:
                sh.addArtist(request.form["contents"], session["user"])
                session["message"] = ""
            except:
                try:
                    sh.addAlbum(request.form["contents"], session["user"])
                    session["message"] = ""
                except:
                    try:
                        sh.addPlaylist(request.form["contents"], session["user"])
                        session["message"] = ""
                    except:
                        try:
                            sh.addSong(request.form["contents"], session["user"])
                            session["message"] = ""
                        except:
                            session["message"] = "URL is not found! Double check the spelling, and make sure you have access to the URL."

        #clear list
        if request.form["cmd"] == "Reset List" or request.form["cmd"] == "Start Again":
            refreshVars()
            return redirect(url_for('home'))


        #Begin ranking songs
        if request.form["cmd"] == "Begin Ranking":
            if len(songDict) > 0:
                beginRanking()
                return redirect(url_for('rank'))
            else:
                session["message"] = "No songs selected!"

#RANKING PAGES

        if request.form["cmd"] == "Song 1":
            if updateChoice("1"):
                return redirect(url_for('rank'))
            else:
                finishRanking()
                return redirect(url_for('final'))

        if request.form["cmd"] == "Song 2":
            if updateChoice("2"):
                return redirect(url_for('rank'))
            else:
                finishRanking()
                return redirect(url_for('final'))

        if request.form["cmd"] == "Skip Question":
            if updateChoice("skip"):
                return redirect(url_for('rank'))
            else:
                finishRanking()
                return redirect(url_for('final'))

        return redirect(url_for('home'))

#--------------------------------------------------------

@app.route("/rank", methods=["GET", "POST"])
def rank():
    global maxSongNum, songNum
    accuracy = min(95, round(maxSongNum/len(songDict)*100))
    #ranking page
    return render_template("rank_page.html", songNum=songNum, accuracy=accuracy, numsongs=str(len(songDict)), name1=songNames[0], name2=songNames[1], album1=songCovers[0], album2=songCovers[1], preview1=songSamples[0], preview2=songSamples[1], artist1=songArtists[0], artist2=songArtists[1], question=questionNum, )

@app.route("/final", methods=["GET", "POST"])
def final():
    #final page
    return render_template("final_page.html", final=finalList)


#SORTING PYTHON CODE
#====================================================================================================================

def refreshVars():
    global songNum, maxSongNum, questionNum

    comments.clear()
    songDict.clear()

    songNames.clear()
    songNames.append("")
    songNames.append("")

    songCovers.clear()
    songCovers.append("")
    songCovers.append("")


    songSamples.clear()
    songSamples.append("")
    songSamples.append("")

    songArtists.clear()
    songArtists.append("")
    songArtists.append("")

    finalList.clear()

    songNum = 0
    maxSongNum = 0
    questionNum = 0

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

def beginRanking():
    global songNum, questionNum, maxSongNum

    questionNum = 0
    maxSongNum = 0
    songNum = 0
    matches.clear()
    for key in songDict:
        matches[key] = (set(), set(), set())

    songs.clear()
    songs.extend([item[0] for item in sorted(songDict.items(), key=lambda x:x[1])])

    getNewSongs()

def updateList():
    for key in matches:
        wins = matches[key][0].copy()
        losses = matches[key][1].copy()
        for win in wins:
            updateELO(key, win, songDict, "1", matches)
        for loss in losses:
            updateELO(key, loss, songDict, "2", matches)

    songs.clear()
    songs.extend([item[0] for item in sorted(songDict.items(), key=lambda x:x[1])])


def getNewSongs():
    global questionNum, maxSongNum

    updateList()
    songNum = 0

    song1 = songs[songNum]
    song2 = songs[songNum+1]

    while (song2 in matches[song1][0]) or (song2 in matches[song1][1]) or (song2 in matches[song1][2]):
        #update ELO
        if song2 in matches[song1][0]: #song1 already wins
            if Probability(songDict[song1][0], songDict[song2][0]) > 0.5:
                songNum += 1
            else:
                songNum = 0
                updateELO(song1, song2, songDict, "1", matches)

        elif song2 in matches[song1][1]: #song2 already wins
            if Probability(songDict[song2][0], songDict[song1][0]) > 0.5:
                songNum += 1
            else:
                songNum = 0
                updateELO(song1, song2, songDict, "2", matches)

        if songNum >= len(songDict)-1:
            return False
        else:
            songs.clear()
            songs.extend([item[0] for item in sorted(songDict.items(), key=lambda x:x[1])])
            song1 = songs[songNum]
            song2 = songs[songNum+1]


    if songNum > maxSongNum:
        maxSongNum = songNum

    questionNum += 1
    songFull[0] = song1
    songFull[1] = song2

    songNames[0] = song1.split(":-:")[0]
    songNames[1] = song2.split(":-:")[0]

    songArtists[0] = song1.split(":-:")[1]
    songArtists[1] = song2.split(":-:")[1]

    songSamples[0] = songDict[song1][1]
    songSamples[1] = songDict[song2][1]

    songCovers[0] = songDict[song1][2]
    songCovers[1] = songDict[song2][2]

    return True


def updateChoice(answer):
    global songNum

    if updateELO(songFull[0], songFull[1], songDict, answer, matches):
        songNum += 1
    else:
        songNum = 0


    return getNewSongs()


def finishRanking():
    finalList.clear()
    sortedSongs = sorted(songDict.items(), key=lambda x:x[1])
    minScore = sortedSongs[0][1][0]
    maxScore = sortedSongs[len(sortedSongs)-1][1][0] - minScore

    for i in range(len(sortedSongs)):
        entry = sortedSongs[len(sortedSongs)-1-i]
        songName = str(i+1) + ') ' + entry[0].split(":-:")[0]
        entryScore = round((entry[1][0] - minScore)/maxScore*100)
        finalList.append(songName + " - " + str(entryScore))
