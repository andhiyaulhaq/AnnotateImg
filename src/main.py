"""
Application entry point.
"""
import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .annotations.storage import create_connection, create_tables

def main():
    """
    Main function to run the application.
    """
    # Database setup
    conn = create_connection("annotations.db")
    if conn is not None:
        create_tables(conn)
        conn.close()
    else:
        print("Error! cannot create the database connection.")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
