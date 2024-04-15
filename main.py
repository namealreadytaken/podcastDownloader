import os
import sys
import re
import requests
import time
import feedparser
import configparser
import pickle
from downloader import Downloader

from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QPushButton, QTreeView, QComboBox, QLineEdit, QFileDialog, QProgressBar, QApplication
from PySide6.QtCore import QFile, QObject, Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QStandardItemModel, QStandardItem


def filenameCleanup(name):
    s = str(name).strip().replace(' ', '_')
    s = re.sub(r'(?u)[^-\w.]', '', s)
    if s in {'', '.', '..'}:
        return 'error.jpg'
    return s


class MySortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(MySortFilterProxyModel, self).__init__(parent)

    def filterAcceptsRow(self, source_row, source_parent):
        index0 = self.sourceModel().index(source_row, 0, source_parent)

        return bool(re.search(self.filterRegularExpression().pattern(), str(self.sourceModel().data(index0))))


class Form(QObject):

    def __init__(self, ui_file, parent=None):
        super(Form, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        self.episodeModel = QStandardItemModel(0, 5)
        self.episodeModel.setHeaderData(0, Qt.Horizontal, "Title")
        self.episodeModel.setHeaderData(1, Qt.Horizontal, "Date")
        self.episodeModel.setHeaderData(2, Qt.Horizontal, "Link")
        self.episodeModel.setHeaderData(3, Qt.Horizontal, "Timestamp")
        self.episodeModel.setHeaderData(4, Qt.Horizontal, "EpisodeNumber")
        self.proxyModel = MySortFilterProxyModel()
        self.proxyModel.setSourceModel(self.episodeModel)

        self.RSSLine = self.window.findChild(QComboBox, 'comboBoxRss')
        self.folderLine = self.window.findChild(QLineEdit, 'lineEditFolder')
        self.filterLine = self.window.findChild(QLineEdit, 'lineEditFilter')
        self.treeView = self.window.findChild(QTreeView, 'treeView')
        self.treeView.setModel(self.proxyModel)
        self.treeView.hideColumn(2)
        self.treeView.hideColumn(3)
        self.treeView.hideColumn(4)
        btn = self.window.findChild(QPushButton, 'pushButtonFolder')
        btn.clicked.connect(self.find_folder)
        self.filterLine.editingFinished.connect(self.textFilterChanged)
        btnDownload = self.window.findChild(QPushButton, 'pushButtonDownload')
        btnDownload.clicked.connect(self.download_mp3)
        self.knownPodcasts = {}
        self.config()
        self.window.show()

    def config(self):
        config = configparser.ConfigParser()
        if not os.path.exists('config.ini'):
            config['DEFAULT'] = {'fileFormat': '{name} {date}.mp3'}
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        config.read('config.ini')
        self.fileFormat = config['DEFAULT']['fileFormat']

        if os.path.exists('knownPodcasts.pickle'):
            with open('knownPodcasts.pickle', 'rb') as knownPodcasts:
                self.knownPodcasts = pickle.load(knownPodcasts)
            self.RSSLine.addItems(self.knownPodcasts.keys())

    def setProgress(self, progress):
        progressBar = self.window.findChild(QProgressBar, 'progressBar')
        progressBar.setValue(progress*100)

    def prepareDownload(self):
        indexes = self.treeView.selectionModel().selectedRows()
        dirName = self.folderLine.text()
        downloads = []
        for current, index in enumerate(indexes):
            name = index.data()
            date = index.siblingAtColumn(1).data()
            link = index.siblingAtColumn(2).data()
            tracknumber = index.siblingAtColumn(4).data()
            filename = os.path.join(dirName, filenameCleanup(self.fileFormat.format(name=name, date=date)))
            downloads.append({'filename': filename, 'link': link, 'tracknumber': tracknumber})
        return downloads

    def download_mp3(self):
        downloads = self.prepareDownload()
        self.down = Downloader(downloads)
        self.down.updateProgress.connect(self.setProgress)
        self.down.start()

    def find_folder(self):
        selected_directory = QFileDialog.getExistingDirectory()
        self.folderLine.setText(selected_directory)
        self.download_RSS()

    def download_RSS(self):
        rssLink = self.RSSLine.currentText()
        response = requests.get(rssLink)
        podcast = feedparser.parse(response.content)
        if len(podcast.entries) == 0:
            return
        self.episodeModel.removeRows(0, self.episodeModel.rowCount())
        size = len(podcast.entries)
        for index, item in enumerate(podcast.entries):
            date = f'({item.published_parsed.tm_year}/{item.published_parsed.tm_mon:02}/{item.published_parsed.tm_mday:02})'
            url = QStandardItem(item.links[0].href)
            for links in item.links:
                if links.type == 'audio/mpeg':
                    url = QStandardItem(links.href)
            title = QStandardItem(item.title)
            date = QStandardItem(str(date))
            stamp = QStandardItem(str(time.mktime(item.published_parsed)))
            tracknumber = QStandardItem(str(size - index))
            line = [title, date, url, stamp, tracknumber]
            self.episodeModel.appendRow(line)
        self.proxyModel.sort(3, Qt.DescendingOrder)
        self.treeView.resizeColumnToContents(0)
        mostRecent = self.proxyModel.index(0, 3).data()
        self.knownPodcasts[rssLink] = mostRecent
        with open('knownPodcasts.pickle', 'wb') as knownPodcasts:
            pickle.dump(self.knownPodcasts, knownPodcasts)

    def textFilterChanged(self):
        regExp = QRegularExpression(self.filterLine.text())
        self.proxyModel.setFilterRegularExpression(regExp)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form(os.path.join(os.path.dirname(__file__), "form.ui"))
    sys.exit(app.exec())
