from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Red de Acueducto")
        self.setGeometry(100, 100, 800, 600)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        btn_cargar = QPushButton("Cargar Red")
        btn_cargar.clicked.connect(self.cargar_red)

        layout.addWidget(btn_cargar)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def cargar_red(self):
        # Lógica para cargar la red
        pass
