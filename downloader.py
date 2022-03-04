from PySide6 import QtCore
import os
import requests
from mutagen.easyid3 import EasyID3

class Downloader(QtCore.QThread):

    updateProgress = QtCore.Signal(float)

    def __init__(self, downloads):
        self.downloads = downloads
        QtCore.QThread.__init__(self)

    def run(self):
        total = len(self.downloads)
        self.updateProgress.emit(0)
        for current, index in enumerate(self.downloads):
            filename = index['filename']
            link = index['link']
            tracknumber = index['tracknumber']
#            resGet = requests.get(link, stream=True)
#            print(resGet.headers['Content-length'])
            response = requests.get(link)
            with open(filename, "wb") as f:
                f.write(response.content)
            audio = EasyID3(filename)
            audio["tracknumber"] = tracknumber
            audio.save()
            self.updateProgress.emit((current+1)/total)
