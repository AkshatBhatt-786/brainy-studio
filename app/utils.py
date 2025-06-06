# ==========================================================
#  * Module : utils.py - Utility Functions
#  * Project : Brainy Studio - Question Paper Generator
#  * Author  : Bhatt Akshat S
#  * Updated : 04-03-2025
#  * Version : 1.0.2
#  * License : MIT License
#  * GitHub  : https://github.com/AkshatBhatt-786/brainy-studio/blob/main/app/utils.py
#  * Description:
#      Contains helper functions for common operations such as
#      file handling, encryption, and UI positioning.
#  ^ Credits | References:
#  & Stack Overflow (https://stackoverflow.com/q/1234567)
#  & Python Docs (https://docs.python.org/3/library/)
#  & CustomTkinter Docs (https://customtkinter.tomschimansky.com/)
# ==========================================================

import customtkinter as ctk
from typing import Tuple
import os
import sys


def centerWindow(parent: ctk.CTk, width: int, height: int, scale_factor: float = 1.0, variation: Tuple[int, int] = (0, 0)):
    # ! Credits | References : StakeOverFlow
    screen_width = parent.winfo_screenwidth()
    screen_height = parent.winfo_screenheight()

    x = int(((screen_width/2) - (width/2)) * scale_factor)
    y = int(((screen_height/2) - (height/1.5)) * scale_factor)

    scaled_width = x + variation[0]
    scaled_height = y + variation[1]
    return f"{width}x{height}+{scaled_width}+{scaled_height}"

# def getPath(*args):
#     try:
#         base_path = sys._MEIPASS  # PyInstaller temp folder
#     except AttributeError:
#         base_path = os.path.dirname(os.path.abspath(__file__))
    
#     return os.path.join(base_path, *args)

def getPath(*args):
    if getattr(sys, 'frozen', False):  # App is frozen via cx_Freeze
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, *args)



def restartApplication():
    try:
        pythonExecutable = sys.executable
        scriptName = sys.argv[0]       
        scriptArguments = sys.argv[1:] 
        os.execv(pythonExecutable, [pythonExecutable, scriptName] + scriptArguments)
    except Exception as e:
        sys.exit(1)