import pyaudio
from pydub import AudioSegment
import wave
import os
from ShazamAPI import Shazam
import tkinter
from tkinter import *
import spotipy
from spotipy.oauth2 import SpotifyOAuth

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 15
WAVE_OUTPUT_FILENAME = "output.wav"

root = tkinter.Tk()
root.title('Shazamify')
root.geometry("700x600")
globalSelectedPlaylist = None

# ---- functions ----

def startRecording():
   p = pyaudio.PyAudio()
   stream = p.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK)
   print("* recording")
   frames = []
   for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
      data = stream.read(CHUNK)
      frames.append(data)
   print("* done recording")
   stream.stop_stream()
   stream.close()
   p.terminate()
   wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
   wf.setnchannels(CHANNELS)
   wf.setsampwidth(p.get_sample_size(FORMAT))
   wf.setframerate(RATE)
   wf.writeframes(b''.join(frames))
   wf.close()

   wavPath = os.path.abspath('output.wav')
   AudioSegment.from_wav(wavPath).export("output.mp3", format="mp3")
   mp3_file_content_to_recognize = open('output.mp3', 'rb').read()
   shazam = Shazam(mp3_file_content_to_recognize)
   recognize_generator = shazam.recognizeSong()
   track = next(recognize_generator)[1].get("track")

   try:
      title = track.get("title")
      print("\nTitle: " + title)
      artist = track.get("subtitle")
      print("Artist: " + artist)
   except AttributeError:
      title = "Track not found"
      artist = "Track not found"

   titleVar.set(title)
   artistVar.set(artist)

   os.remove("output.wav")
   os.remove("output.mp3")

def quit_me():
    root.quit()
    root.destroy()

def connectSpotify():
   sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="ea71108300284538951bd823df008e86",
                                               client_secret="b39e31042fef4f90bb77c350bd055b1e",
                                               redirect_uri="https://localhost:3000/callback",
                                               scope="playlist-read-private playlist-modify-private"))
   results = sp.current_user_playlists(limit=50)
   playlistList = []
   items = results['items']
   for item in items:
      playlistName = item['name']
      if playlistName != '':
         playlistList.append(playlistName)
   
   selectedPlaylist = StringVar()
   selectedPlaylist.set(playlistList[0])

   connectedUser.set(sp.current_user().get('id'))
   global userSelectedPlaylist
   userSelectedPlaylist = False

   def chosenPlaylist():
      global globalSelectedPlaylist
      globalSelectedPlaylist = str(selectedPlaylist.get())
      userSelectedPlaylist = True
      print("you chose : " + str(selectedPlaylist.get()))
   
   yNum = 75
   for item in playlistList:
      button = Radiobutton(root, text=item, variable=selectedPlaylist, value=item, command=chosenPlaylist).place(x = 440,y = yNum)
      yNum += 20

      
def addToSpotify():
   sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="ea71108300284538951bd823df008e86",
                                               client_secret="b39e31042fef4f90bb77c350bd055b1e",
                                               redirect_uri="https://localhost:3000/callback",
                                               scope="playlist-read-private playlist-modify-private"))
   results = sp.current_user_playlists(limit=50)
   items = results['items']
   finalSelectedID = ""
   finalPlaylistName = ""
   if userSelectedPlaylist == False:
      item = items[0]
      playlistName = item['name']
      finalSelectedID = item['id']
      finalPlaylistName = playlistName
   else:
      for item in items:
         playlistName = item['name']
         if playlistName == globalSelectedPlaylist:
            finalSelectedID = item['id']

   

   #ID of the playlist selected
   print(finalSelectedID)

   artist = artistVar.get()
   track = titleVar.get()
   print(artist + " : " + track)
   track_id = sp.search(q='artist:' + artist + ' track:' + track, type='track', limit=1, market="GB")
   print(track_id)
   trackList = []
   if track == "Track not found":
      status.set("There was an error adding the song to \nthe playlist")
   else:
      try:
         trackList.append(track_id.get('tracks').get('items')[0].get('id'))
         sp.user_playlist_add_tracks(sp.current_user().get('id'), playlist_id = finalSelectedID, tracks = trackList)
         try:
            status.set(str(track) + " has been added to " + globalSelectedPlaylist)
         except TypeError:
            status.set(str(track) + " has been added to " + finalPlaylistName)
      except IndexError:
         status.set("Could not find song in Spotify!")


# ---- main ----

#buttons
start = Button(root, text = "Record (15 sec)", command = startRecording ).place(x = 25,y = 25)
connectSpotifyButton = Button(root, text = "Connect Spotify Account", command = connectSpotify).place(x=440,y=40)
addToSpotifyButton = Button(root, text = "Add song to selected Spotify playlist", command = addToSpotify).place(x=25, y=150)

#labels
songTitle = Label(root, text = "Title: ").place(x=25,y=55)
titleVar = StringVar()
titleVar.set("")
titleLabel = Label(root, textvariable = titleVar, fg="red").place(x=60,y=55)

songArtist = Label(root, text = "Artist: ").place(x=25,y=80)
artistVar = StringVar()
artistVar.set("")
artistLabel = Label(root, textvariable = artistVar, fg="red").place(x=60,y=80)

connectedUserLabel = Label(root, text = "Connected User: ").place (x=420,y=10)
connectedUser = StringVar()
connectedUser.set("")
connectedUserName = Label(root,textvariable=connectedUser, fg = "blue").place(x=515,y=10)

status = StringVar()
status.set("")
statusLabel = Label(root, textvariable=status, fg = "red").place(x=25,y=180)

root.protocol("WM_DELETE_WINDOW", quit_me)
root.mainloop()