from PySide6 import QtCore
from PySide6.QtGui import QStandardItemModel, QStandardItem
import os
import re
import requests


def filenameCleanup(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    if s in {'', '.', '..'}:
        return 'error.jpg'
    return s

class Downloader(QtCore.QThread):

    updateProgress = QtCore.Signal(float)

    def __init__(self, dirName, models):
        self.dirName = dirName
        self.models = models
        QtCore.QThread.__init__(self)

    def run(self):
        total = len(self.models)
        self.updateProgress.emit(0)
        for current, index in enumerate(self.models):
            filename = filenameCleanup(index.data() + ".mp3")
            resGet = requests.get(index.siblingAtColumn(2).data, stream=True)
            print(resGet.headers['Content-length'])
            response = requests.get(index.siblingAtColumn(2).data())
            with open(os.path.join(self.dirName, filename), "wb") as f:
                f.write(response.content)
            self.updateProgress.emit(current/total)
