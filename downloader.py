from PySide6 import QtCore
from PySide6.QtGui import QStandardItemModel, QStandardItem
import os
import re
import requests


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
#            resGet = requests.get(link, stream=True)
#            print(resGet.headers['Content-length'])
            response = requests.get(link)
            with open(filename, "wb") as f:
                f.write(response.content)
            self.updateProgress.emit((current+1)/total)
