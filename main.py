import pafy
from youtubesearchpython import VideosSearch
from playsound import playsound
from pydub import AudioSegment
import readline
import threading
import multiprocessing
import os
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
import sys

playerThread = None
downloaderThread = None
songQueue = []
urlQueue = []
session = None
history = None

# download song from youtube and convert to MP3
def getSong(video_id: str):

    global songQueue

    ## url of the video
    # ## calling the new method of pafy
    result = pafy.new(video_id)
    lowest = result.audiostreams[0]

    infile = result.title + "." + lowest.extension
    outfile = result.title + ".wav"

    if outfile not in os.listdir():
        if infile not in os.listdir():
            lowest.download(quiet=True)
            
        # convert to wav
        sound = AudioSegment.from_file(infile,format=lowest.extension)
        sound.export(outfile,format="wav")
        os.remove(infile)

    songQueue.append(outfile)

# runs the async thread for playing songs
def playSongs(skip=False):
    global songQueue
    global playerThread

    if skip:
        skip = False
        if playerThread:
            playerThread.terminate()
            playerThread = None

    if not playerThread: # start a new thread
        if len(songQueue) > 0:
            currentSong = songQueue.pop(0)
            # playerThread = threading.Thread(target=playsound, args=(currentSong,), daemon=True)
            playerThread = multiprocessing.Process(target=playsound,args=(currentSong,),daemon=True)
            playerThread.start()
    elif not playerThread.is_alive(): # close and kill the thread
        playerThread = None

# runs the async thread for downloading songs
def downloadSongs():

    global urlQueue
    global downloaderThread

    if not downloaderThread:
        if len(urlQueue) > 0:
            currentUrl = urlQueue.pop(0)
            downloaderThread = threading.Thread(target=getSong,args=(currentUrl,), daemon=True)
            downloaderThread.start()
    elif not downloaderThread.is_alive():
        downloaderThread = None

# continuously loads async threads in the background
def asyncLoop():

    while True:
        time.sleep(3)
        playSongs()
        downloadSongs()

# search loop
def search():

    search = ""

    while True:
        try:
            search = session.prompt("Search for a song: ")
        except KeyboardInterrupt:
            pass # Ctrl-C pressed, Try again
        else:
            break

    global history
    history.append_string(search)
    videosSearch = VideosSearch(search, limit = 10)
    videoList = videosSearch.result()["result"]

    for i in range(len(videoList)):
        print(f"[{i}] "  + videoList[i]["title"])

    text = session.prompt("Select a video: ")

    if text == "cancel":
        return
    
    video_id = videoList[int(text)]["id"]

    urlQueue.append(video_id)

# main interaction loop
def main():
    global session
    global playerThread
    global songQueue
    global history

    history = InMemoryHistory()
    history.append_string("search")
    history.append_string("skip")
    history.append_string("queue")
    history.append_string("exit")

    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
    )

    while True:

        while True:
            try:
                text = session.prompt("Enter a command: ")
            except KeyboardInterrupt:
                pass # Ctrl-C pressed, Try again
            else:
                break

        if text == "search":
            search()
        elif text == "skip":
            playSongs(True)
        elif text == "queue":
            print(songQueue)
            print(urlQueue)
        elif text == "exit":
            break




if __name__ == "__main__":
    # start the async thread
    threading.Thread(target=asyncLoop,daemon=True).start()
    main()





