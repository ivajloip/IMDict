#!/usr/bin/python3.0
import sys
from PyQt4 import QtCore, QtGui
import threading
import search_engine
import shelve
import os.path

langs = ['en', 'fi', 'fr', 'de', 'iw', 'it', 'ko', 'pt', 'ru', 'es', 'zh-CN', 'cs', 'el', 'bg', 'hr', 'sr', 'hi', 'th', 'ar', 'zh-TW']        
dict_hide = set(('entry', 'definition'))
text_hide = set(('translation', 'text'))
#lock = 


class TextBrowser(QtGui.QTextBrowser):
    def __init__(self, parent = None):
        super(TextBrowser, self).__init__(parent)
        self.window = parent

    def setSource(self, url):
        self.window.entry.setText(url.toString())
        self.window.definition.setText('')
        self.window.entry.emit(QtCore.SIGNAL('returnPressed()'))


class MainWindow(QtGui.QMainWindow):

    def __init__(self, use_local = True):
#       creates the window with the title and icon
        super(MainWindow, self).__init__()
        self.resize(480, 360)
        self.setWindowTitle('IMDict')
        self.setWindowIcon(QtGui.QIcon('icons/icon.png'))


#       creates the widgets that will be used to get the word that the user wants translated and the widget where the translation will appear
        self.entry = QtGui.QLineEdit(self)
        self.buttonGo = QtGui.QPushButton('Go', self)
        self.definition = TextBrowser(self)
#        self.definition.setFocusPolicy(False)
        self.definition.setReadOnly(True) 

#       creates the widgets for text input and its translation
        self.text = QtGui.QTextEdit(self)
        self.translation = QtGui.QTextEdit(self)
        self.translation.setReadOnly(True) 

#       creates the menuBar and the menu entries
        menubar = self.menuBar()
        file = menubar.addMenu('&File')
        file.addSeparator()
        self.createMenuItem('Exit', 'icons/exit.png', 'Ctrl+Q', 'Exit application', QtCore.SLOT('close()'),file)

#        edit = menubar.addMenu('&Edit')
#        print(dir(self.translation))
#        self.createMenuItem('Copy', 'icons/copy.png', 'Ctrl+C', 'Copy selected text', lambda : self.emit(QtCore.SIGNAL('copy()')), edit)

#       defines where each widget is displayed
        self.frame = QtGui.QFrame(self)
        self.setCentralWidget(self.frame)
        self.layout = QtGui.QGridLayout()
        self.layout.addWidget(self.entry, 10, 1, 10, 7)
        self.layout.addWidget(self.buttonGo, 10, 9, 10, 1)
        self.layout.addWidget(self.definition, 20, 0, 100, 10)
        self.layout.setHorizontalSpacing(20)
        self.layout.setVerticalSpacing(1)
        self.frame.setLayout(self.layout)
        self.tabbar = QtGui.QTabBar(self)
        self.layout.addWidget(self.tabbar, 0, 0, 10, 10)
        self.tabbar.addTab('Dictionary')
        self.tabbar.addTab('Text Translation')

#       connects signal with their handlers
        self.connect(self.tabbar, QtCore.SIGNAL('currentChanged(int)'), self.changeTab)
        self.connect(self.definition, QtCore.SIGNAL('currentChanged(QString)'), self.update_definition) 
        self.connect(self.translation, QtCore.SIGNAL('currentChanged(QString)'), self.update_translation)
        self.connect(self.buttonGo, QtCore.SIGNAL('clicked()'), self.look_for_word)
        self.connect(self.entry, QtCore.SIGNAL('returnPressed()'),self.look_for_word) 

        self.layout.addWidget(self.text, 20, 0, 100, 5)
        self.layout.addWidget(self.translation, 20, 5, 100, 5)
        
        self.from_lang = self.createComboBox(self.layout, 10, 0)
        self.to_lang = self.createComboBox(self.layout, 10, 8)
        self.to_lang.setCurrentIndex(13)
        for _ in text_hide:
            self.__getattribute__(_).hide()

        self.lock = threading.Lock()

        if use_local:
            if os.name == 'nt':
                self.directory = os.path.expanduser('~/AppData/Local/.IMDict/')
            else:
                self.directory = os.path.expanduser('~/.IMDict/')
            if not os.path.exists(self.directory):
                reply = QtGui.QMessageBox.question(self, 'No local configuration', 'Do you want me to create local configuration?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
                if reply == QtGui.QMessageBox.Yes:
                    os.mkdir(self.directory)
                    self.use_local = True
                else:
                    self.use_local = False
            else:
                db = shelve.open(self.directory+'/config.conf')
                for _ in db.keys():
                        self.__setattr__(_,db[_])
                db.close()
        else:
            self.use_cache = False

        self.center()
        self.show()

    def createMenuItem(self, label, iconLocation, shortCut, statusTip, func, addTo):
        tmp = QtGui.QAction(QtGui.QIcon(iconLocation), label, self)
        tmp.setShortcut(shortCut)
        tmp.setStatusTip(statusTip)
        self.connect(tmp, QtCore.SIGNAL('triggered()'), func)
        addTo.addAction(tmp)       

    def createComboBox(self, layout, row, column):
        tmp = QtGui.QComboBox(self)
        layout.addWidget(tmp, row, column, 10, 1)
        for _ in langs:
            tmp.addItem(_)
            
        return tmp

    def changeTab(self, ind):
        if ind == 1:
            for _ in dict_hide:
                self.__getattribute__(_).hide()
            for _ in text_hide:
                self.__getattribute__(_).show()
        else:
            for _ in text_hide:
                self.__getattribute__(_).hide()
            for _ in dict_hide:
                self.__getattribute__(_).show()

    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)  

    def update_definition(self, string):
        self.definition.setText(string)

    def update_translation(self, string):
        self.translation.setText(string)

    def search_word(self):
        if self.tabbar.currentIndex() == 0:
            word = str(self.entry.text())
            if self.use_cache:
                db = shelve.open(self.directory + langs[self.from_lang.currentIndex()] + '-' + langs[self.to_lang.currentIndex()]) 
                if db.get(word):
                    definition = db[word]
                else:
                    definition = search_engine.find_word(langs[self.from_lang.currentIndex()], langs[self.to_lang.currentIndex()], word)
                    db[word] = definition
                db.close()
            else:
                definition = search_engine.find_word(langs[self.from_lang.currentIndex()], langs[self.to_lang.currentIndex()], word)
            self.definition.emit(QtCore.SIGNAL('currentChanged(QString)'), definition)
        else:
            text = str(self.text.toPlainText())
            translation = search_engine.find_translation(langs[self.from_lang.currentIndex()], langs[self.to_lang.currentIndex()], text)
            self.translation.emit(QtCore.SIGNAL('currentChanged(QString)'), translation)
        self.lock.release()

    def look_for_word(self):
        self.lock.acquire()
        self.definition.setText('')
        tr = threading.Thread(name = 'search for word', target = self.search_word,)
        tr.start()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    print(sys.argv)
    if len(sys.argv) > 1 and sys.argv[1] == '--no-local':
        use_local = False
    else: 
        use_local = True
    window = MainWindow(use_local)
    sys.exit(app.exec_())       

