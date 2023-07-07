import sys, os, logging, threading , time

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
#from PyQt5 import QtGui, QtCore

from mutagen.mp3 import MP3
from pygame import mixer as mx

from musicPlayer import *

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s -  %(message)s')
#logging.disable() #This statement disables all log messages without physically deleting them like you would do with print statements.
logging.debug('Start of program')

class MyForm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #initialize mixer
        mx.init()

        self.ui.statusbar.showMessage('Melody Player on standby.')

        # class variables
        self.playlist = []
        self.paused = False
        self.stop = False
        self.muted = False
        self.song_dir = ''
        self.timer_thread_running = False

        #check for this signal and assign slots
        self.ui.pushButtonAdd.clicked.connect(self.browse_songs)
        self.ui.listWidgetPlaylist.itemDoubleClicked.connect(lambda : self.signal_emitted("doubleClickedList"))
        self.ui.pushButtonPlay.clicked.connect(lambda : self.signal_emitted('clickedPlayButton'))
        self.ui.pushButtonMute_Unmute.clicked.connect(self.mute_song)
        self.ui.pushButtonStop.clicked.connect(self.stop_music)
        self.ui.pushButtonRewind.clicked.connect(self.rewind_song)
        self.ui.pushButtonDelete.clicked.connect(self.delete_a_song)
        self.ui.pushButtonDeleteAll.clicked.connect(self.delete_all_songs)
        self.ui.verticalSliderVolume.valueChanged.connect(self.volume_control)

        self.show()

    def browse_songs(self): #this fn browses for songs in the pc directory
        self.selected_song_path = QFileDialog.getOpenFileName(self, 'open file', '/home',"Audio(*.mp3)") #selected song path directory is stored in this variable
        logging.debug("song_path = "+str(self.selected_song_path))
        if self.selected_song_path[0]=='' and self.selected_song_path[1]=='': #check whether a song was selected from the directory
            logging.debug("song_path is empty = " + str(self.selected_song_path))
            logging.debug("No song was selected from the directory.")
        else:
            self.add_to_playlist(self.selected_song_path) #the full path of the song is passed to 'add_to_playlist()' fn

    def add_to_playlist(self, song_path): #this fn receive the full path of the song from 'browse_songs()' fn
        index = 0
        self.playlist.insert(index, self.selected_song_path[0]) #adds the full path of the song on top of the list
        self.ui.listWidgetPlaylist.insertItem(index, os.path.basename(song_path[0])) #adds the full path of the song on top of the listWidget
        logging.debug("songName -> " + os.path.basename(song_path[0]))
        logging.debug("Playlist -> "+str(self.playlist))

    def signal_emitted(self, event_name): #checks which signal is being emitted
        if event_name == 'doubleClickedList':
            self.get_song()
            self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/pause.png"))
        else:
            if self.paused:
                mx.music.unpause()
                self.paused = False
                self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/pause.png"))
                self.ui.statusbar.showMessage('Playing...' + str(os.path.basename(self.song_dir)))
            else:
                if mx.music.get_busy():
                    mx.music.pause()
                    self.paused = True
                    self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/play.png"))
                    self.ui.statusbar.showMessage('Pause...')
                else:
                    self.get_song()

    def get_song(self): #this function extracts the song highlighted on the listWidget for the ' play_song'  function to play it
        if self.ui.listWidgetPlaylist.count() == 0: #if there are no songs in the playlist,prompt the user to add some
            logging.debug("No songs are in the playlist.")
            logging.debug("Number of songs in the playlist = " + str(self.ui.listWidgetPlaylist.count()) + " songs")
            reply = QMessageBox.information(self, 'Melody Player Error', "There are no songs in the playlist."\
                                    "\nWould you like to load songs from your PC's directory?"
                                    ,QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes: #load songs into the playlist from PC's directory
                self.browse_songs()
        elif self.ui.listWidgetPlaylist.count() > 0:
            try:
                selected_song = self.ui.listWidgetPlaylist.currentItem().text()  # highligted song on the list widget is stored in this variable
                logging.debug("selected_song -> " + str(selected_song))
                self.search_playlist(selected_song)
                self.play_song(self.song_dir) #pass the song directory to the ' play_song() ' fn
                # self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/pause.png"))
            except:
                logging.debug("Number of songs in the playlist = "+str(self.ui.listWidgetPlaylist.count())+" songs")
                selected_song = self.ui.listWidgetPlaylist.item(0).text()
                self.search_playlist(selected_song)
                self.play_song(self.song_dir)  # pass the song directory to the ' play_song() ' fn

    def search_playlist(self, selected_song):
        for self.song_dir in self.playlist:  # iterate through the playlist variable to find the full path of highlighted song on the listWidget
            logging.debug(self.song_dir)
            if selected_song == os.path.basename(self.song_dir):  # if the song full path is found, stop searching by exiting the for loop
                logging.debug("Found ' " + selected_song + " ' in the playlist.")
                logging.debug("Full song path is ' " + self.song_dir + " '")
                break
        return self.song_dir

    def play_song(self, song_dir): #this fn plays the selected song
        mx.music.set_volume(0.5)
        self.ui.verticalSliderVolume.setValue(50)
        self.ui.labelVolumeDisplay.setText("  "+str(self.ui.verticalSliderVolume.value())+"%")
        mx.music.load(song_dir)
        mx.music.play()
        self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/pause.png"))
        self.ui.statusbar.showMessage('Playing...'+str(os.path.basename(self.song_dir)))

        self.show_details()

    def show_details(self):
        self.ui.labelPlaying.setText("Playing:  " + os.path.basename(self.song_dir))
        file_data = os.path.splitext(self.song_dir)
        if file_data[1] == '.mp3':
            audio = MP3(self.song_dir)
            total_length = audio.info.length
        else:
            a = mx.sound(self.song_dir)
            total_length = a.get_length()

        mins, secs = divmod(total_length, 60)
        mins = round(mins)
        secs = round(secs)
        time_format = '{:02d}:{:02d}'.format(mins, secs)
        self.ui.labelTotalTime.setText("Total Length:  " + "   " + time_format)
        t1 = threading.Thread(target=self.start_count, args=(total_length,), daemon = True)
        t1.start()

    def start_count(self, total_length):
        current_time = 0
        # mixer.music.getbusy() results to TRUE if the music is still ...
        # ...playing and FALSE if the music is not playing
        while current_time <= total_length and mx.music.get_busy():
            if self.paused:
                continue  # stops counting if music is paused
            else:
                mins, secs = divmod(current_time, 60)
                mins = round(mins)
                secs = round(secs)
                time_format = '{:02d}:{:02d}'.format(mins, secs)
                time.sleep(1)
                current_time += 1
                self.ui.labelCurrentTime.setText("Current Time: " + " - " + time_format)

    def volume_control(self):
        if self.muted: #check whether the mute is on and change icon to unmute
            self.ui.pushButtonMute_Unmute.setIcon(QtGui.QIcon("icons/unmute.png"))
            self.muted = False
        else:
            pass
        mx.music.set_volume((self.ui.verticalSliderVolume.value())/100)
        self.ui.labelVolumeDisplay.setText("  " + str(self.ui.verticalSliderVolume.value()) + "%")

    def mute_song(self):
        if self.muted:
            mx.music.set_volume(0.5)
            self.ui.verticalSliderVolume.setValue(50)
            self.ui.labelVolumeDisplay.setText("  " + str(50) + "%")
            self.muted = False
            logging.debug("song has been unmuted")
            self.ui.pushButtonMute_Unmute.setIcon(QtGui.QIcon("icons/unmute.png"))
        else:
            mx.music.set_volume(0)
            self.ui.verticalSliderVolume.setValue(0)
            self.ui.labelVolumeDisplay.setText("  " + str(0) + "%")
            self.muted = True
            logging.debug("song has been muted")
            # mute_icon = QtGui.QIcon()
            # mute_icon.addPixmap(QtGui.QPixmap("icons/mute.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
            # self.ui.pushButtonMute_Unmute.setIcon(mute_icon)
            # self.ui.pushButtonMute_Unmute.setIconSize(QtCore.QSize(32, 32))
            self.ui.pushButtonMute_Unmute.setIcon(QtGui.QIcon("icons/mute.png"))
            
    def stop_music(self):
        if self.paused:
            self.paused = False
            self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/play.png"))
            mx.music.stop()
            self.ui.statusbar.showMessage('Stopped...') #display stopped on the statusbar
        else:
            self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/play.png"))
            mx.music.stop()
            self.ui.statusbar.showMessage('Stopped...')
            
    def rewind_song(self):
        if self.song_dir == "": #do nothing if there is no song
            pass
        else:
            self.play_song(self.song_dir)

    def delete_a_song(self):
        if self.ui.listWidgetPlaylist.count() == 0: #do nothing if there are no songs in the list
            logging.debug("There are no songs to be deleted in the listWidget.")
        elif self.ui.listWidgetPlaylist.currentRow() == -1: #do nothing if no song in the list is selected
            logging.debug("There are songs in the listWidget but none is selected for deletion.")
        else: # delete a song if it is playing or not
            if mx.music.get_busy(): #check if a song is playing
                if self.ui.listWidgetPlaylist.currentItem().text() == os.path.basename(self.song_dir): # delete the playing song
                    logging.debug("The playing song has been stopped and deleted.")
                    self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/play.png"))
                    mx.music.stop()
                    self.ui.listWidgetPlaylist.takeItem(self.ui.listWidgetPlaylist.currentRow()) #delete the song
                else: #delete a song that is not playing
                    logging.debug("A song that is not playing has been deleted.")
                    self.ui.listWidgetPlaylist.takeItem(self.ui.listWidgetPlaylist.currentRow())  # delete the song
            else: # no songs are playing.delete the selected song
                logging.debug("Songs are not playing.Selected song has been deleted.")
                self.ui.listWidgetPlaylist.takeItem(self.ui.listWidgetPlaylist.currentRow())  # delete the song

        if self.ui.listWidgetPlaylist.count() == 0:
            self.ui.statusbar.showMessage('Melody Player on standby.')

    def delete_all_songs(self):
        mx.music.stop()
        self.ui.pushButtonPlay.setIcon(QtGui.QIcon("icons/play.png"))
        self.ui.listWidgetPlaylist.clear()
        self.ui.statusbar.showMessage('Melody Player on standby.')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MyForm()
    w.show()
    sys.exit(app.exec_())
