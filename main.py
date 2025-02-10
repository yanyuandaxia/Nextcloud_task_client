#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets
from MainWindow import MainWindow


def main():
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    window = MainWindow()
    if not window.config['offline_mode']:
        window.checkLocalServerTasks()
    window.fetchTasks()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
