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

    def __init__(self, dirName, models, fileFormat):
        self.dirName = dirName
        self.models = models
        self.fileFormat = fileFormat
        QtCore.QThread.__init__(self)

    def run(self):
        total = len(self.models)
        self.updateProgress.emit(0)
        for current, index in enumerate(self.models):
            name = index.data()
            date = index.siblingAtColumn(1).data()
            filename = filenameCleanup(self.fileFormat.format(name=name, date=date))
#            resGet = requests.get(index.siblingAtColumn(2).data, stream=True)
#            print(resGet.headers['Content-length'])
            response = requests.get(index.siblingAtColumn(2).data())
            with open(os.path.join(self.dirName, filename), "wb") as f:
                f.write(response.content)
            self.updateProgress.emit((current+1)/total)
