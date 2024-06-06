import SongHandler as sh
import math

def rankStep(start, c0, c1, subSize, listSize, reorder, userID):
    #rearrange list
    if reorder:
        sh.updateSongRank(userID, c1, -1)
        for i in reversed(range(c0, c1)):
            sh.updateSongRank(userID, i, i+1)
        sh.updateSongRank(userID, -1, c0)
        c0 += 1
        c1 += 1
    else:
        c0 += 1
        
    #check if sublist is sorted
    if c1 == start+2*subSize or c0 == c1:
        start = start+2*subSize
        c0 = start
        c1 = start + subSize

    #check if end of list reached (recursive call complete)
    if c1 >= listSize:
        subSize *= 2
        start = 0
        c0 = 0
        c1 = subSize

    return start, c0, c1, subSize

#start the ranking process
def startRanking(userID):
    sh.initSongRank(userID)
    return 0, 0, 1, 1


def approxQuestions(start, c0, c1, subSize, listSize):
    #determine current position
    compsLeft = 0;
    i = subSize
    c0rel = c0-start
    c1rel = c1-subSize-start
    s = start+max(c0rel, c1rel)

    #count remaining songs
    while i < listSize:
        compsLeft += 3*(listSize-s)/5
        i *= 2
        s = 0

    return compsLeft
    
        
        
        
    
