import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.database import Database
from src.ai_engine import AIEngine
from src.ui.main_window import MainWindow
from src.user_profile import get_profile


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("IFA Mentor")
    app.setOrganizationName("IFA")

    db = Database()
    ai = AIEngine(db)
    profile = get_profile(db)

    window = MainWindow(db, ai, profile=profile)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()