from cx_Freeze import setup, Executable
import os

base = "Win32GUI"

build_exe_options = {
    "packages": ["os", "reportlab"],
    "include_files": [("assets", "assets"), ("database", "database"), ("workspace", "workspace")],
}

executables = [
    Executable("main.py", target_name="BrainyStudio.exe", base=base, icon=r"D:\github_projects\brainy-studio\app\assets\icons\icon.ico")
]

setup(
    name="BrainyStudio v1.0.2",
    version="1.0.2",
    description="Brainy Studio Application",
    options={"build_exe": build_exe_options},
    executables=executables
)