import math
import random
import string
from flask import Flask, render_template, request, url_for, redirect, session
import SongHandler as sh
import RankingHandler as rh

app = Flask(__name__)
app.secret_key = 'rGRs001XJ1Y1M7jo'

app.config["DEBUG"] = True

#WEBPAGE CODE
#====================================================================================================================
@app.route("/", methods=["GET", "POST"])
def home():    
    #refresh page
    if request.method == "GET":
        #initialize user id and table (not logged in! create random client_id)
        if session.get("user") == None:
            session["user"] = "user" + ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(16))
        if not sh.tableExists(session["user"]):
            sh.createTable(session["user"])

        if session.get("question") == None:
            session["question"] = 0
            
        #refresh user entry data and sweep users
        sh.updateUser(session["user"])
        sh.sweepData()
                
        
        #get message to display on website
        if session.get("message") == None:
            mess = ""
        else:
            mess = session["message"]
            session["message"] = ""
            
        #get list of songs added by user
        songList = sh.getSongList(session["user"])
        
        #render HTML page for user
        return render_template("main_page.html", songs=songList, message=mess, cont=(session["question"]!=0))
    #button was pressed
    else:
        #Add songs buttons
        if request.form["cmd"] == "Add Content": 
            #add content to list
            try:
                sh.addArtist(request.form["contents"], session["user"])
                session["message"] = ""
                session["question"] = 0
            except:
                try:
                    sh.addAlbum(request.form["contents"], session["user"])
                    session["message"] = ""
                    session["question"] = 0
                except:
                    try:
                        sh.addPlaylist(request.form["contents"], session["user"])
                        session["message"] = ""
                        session["question"] = 0
                    except:
                        try:
                            sh.addSong(request.form["contents"], session["user"])
                            session["message"] = ""
                            session["question"] = 0
                        except:
                            session["message"] = "URL is not found! Double check the spelling, and make sure you have access to the URL."

        #remove a single song from list
        elif request.form["cmd"] == "remove":
            session["message"] = "song removed!"
            session["question"] = 0
            sh.removeSong(request.form["contents"], session["user"])


        #clear list of all songs
        elif request.form["cmd"] == "Clear List":
            session["message"] = "songs cleared!"
            session["question"] = 0
            sh.removeAllSongs(session["user"])


        #Continue ranking songs
        elif request.form["cmd"] == "Continue Ranking":
            if session.get("question") == None or session["question"] == 0:
                session["message"] = "No ranking session found!"
            else:
                return redirect(url_for('rank'))
                
        #Begin ranking songs
        elif request.form["cmd"] == "Begin Ranking":
            if sh.songNumber(session["user"]) > 3:
                session["start"], session["c0"], session["c1"], session["size"] = rh.startRanking(session["user"])
                session["question"] = 1
                return redirect(url_for('rank'))
            else:
                session["message"] = "Please add at least 4 songs!"

        return redirect(url_for('home'))

#--------------------------------------------------------

#ranking page
@app.route("/rank", methods=["GET", "POST"])
def rank():
    if request.method == "GET":
        #if ranking still needs to be done
        if session["size"] <= sh.songNumber(session["user"]):
            
            #get next songs to compare
            s0 = sh.getSongOfRank(session["user"], session["c0"])
            s1 = sh.getSongOfRank(session["user"], session["c1"])

            #determine accuracy
            compsLeft = 0;
            i = session["size"]
            c0rel = session["c0"]-session["start"]
            c1rel = session["c1"]-session["size"]-session["start"]
            s = session["start"]+max(c0rel, c1rel)
            while i < sh.songNumber(session["user"]):
                compsLeft += (sh.songNumber(session["user"])-s)/i
                i *= 2
                s = 0
            accuracy = round(100*(session["question"]-1)/(compsLeft + session["question"]-1))
    
            #go to ranking page
            return render_template("rank_page.html", song0=s0, song1=s1, question=session["question"], accuracy = accuracy)
        #ranking finished! go to ranking page!
        else:
            return redirect(url_for('final'))
    else:
        if request.form["cmd"] == "SONG 1":
            reorder = False
        else:
            reorder = True
        
        session["question"] += 1
        session["start"], session["c0"], session["c1"], session["size"] = rh.rankStep(session["start"], session["c0"], session["c1"], session["size"], sh.songNumber(session["user"]), reorder, session["user"])  
        return redirect(url_for('rank'))


def sortSongs(val):
    return val[6]
    
@app.route("/final", methods=["GET", "POST"])
def final():
    finalList = sh.getSongList(session["user"])
    finalList.sort(key=sortSongs)
    #final page
    return render_template("final_page.html", songs=finalList)


