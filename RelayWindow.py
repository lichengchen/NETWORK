from RelayUi import *
import sys, os
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import threading
import time

from DNSRelay import DNSRelay
from DBFacade import DBFacade

class RelayWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(RelayWindow, self).__init__(parent)
        self.setupUi(self)
        self.tableWidget.setColumnWidth(0,450)
        self.tableWidget.setColumnWidth(4,450)
        self.startBtn.clicked.connect(self.on_start)

        self.timer=QTimer()
        self.timer.timeout.connect(self.on_refresh)
        self.checkBox.stateChanged.connect(self.on_checkBox_checked)
        self.refreshBtn.clicked.connect(self.on_refresh)

        self.dnsRelay = DNSRelay()
        self.dnsRelayThread = DNSRelayThread(self.dnsRelay)

        self.updateTable()
    
    def on_start(self):
        self.startBtn.setEnabled(False)
        self.dnsRelayThread.start()
    
    def updateTable(self):
        db = DBFacade()
        records = db.fetch_table()
        self.tableWidget.setRowCount(len(records))

        for i in range(0, len(records)):
            for j in range(0, 5):
                txt = str(records[i][j])
                self.tableWidget.setItem(i,j,QTableWidgetItem(txt))
    
    def on_checkBox_checked(self, flag):
        if flag:
            self.timer.start()
        else:
            self.timer.stop()
        
    def on_refresh(self):
        self.refreshBtn.setEnabled(False)
        self.updateTable()
        self.refreshBtn.setEnabled(True)

class DNSRelayThread (threading.Thread):
    def __init__(self, dnsRelay):
        threading.Thread.__init__(self)
        self.dnsRelay = dnsRelay
        
    def run(self):
        print (" DNSRelay 启动！")
        self.dnsRelay.run()
        print (" DNSRelay 退出！")


if __name__ == "__main__":   
    app = QApplication(sys.argv)
    rw = RelayWindow()
    rw.show()
    sys.exit(app.exec_())