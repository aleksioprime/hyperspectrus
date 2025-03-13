from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow


class ResearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("src/forms/research.ui", self)