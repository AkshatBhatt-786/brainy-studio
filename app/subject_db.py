import sqlite3
import customtkinter as ctk
from tkinter import messagebox
from utils import getPath

def initialize_db():
    conn = sqlite3.connect(getPath(r"app\database\brainy-studio.db"))
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
                        subject_code TEXT PRIMARY KEY,
                        subject_name TEXT,
                        subject_date TEXT,
                        time_duration TEXT,
                        instructions TEXT
                    )''')
    conn.commit()
    conn.close()


