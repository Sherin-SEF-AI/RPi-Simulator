"""
PiStudio Desktop GUI Application
"""

import sys
from PyQt6.QtWidgets import QApplication
from .main_window import MainWindow


def main():
    """Launch desktop GUI"""
    app = QApplication(sys.argv)
    app.setApplicationName("PiStudio")
    app.setApplicationVersion("0.1.0")
    
    # Set dark theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QPushButton {
            background-color: #404040;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #353535;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()