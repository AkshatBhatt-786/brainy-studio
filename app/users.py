import sqlite3
import os
import re
import hashlib
from tkinter import messagebox
import tkinter.filedialog as fd
from ui_components import *
from utils import centerWindow, getPath
from PIL import Image
import customtkinter as ctk

# ^ Author : Bhatt Akshat S
# ^ Last Updated : 17-01-2025
# ^ Version : 1.0.2 ^


class UserManager:
    
    def __init__(self, db_name="database\\brainy-studio.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.user = None
        self.create_users_tables()
    
    def create_users_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL CHECK(LENGTH(username) >= 6),
                password TEXT NOT NULL,
                workspace TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    pass
    
    def is_strong_password(self, password):
        # ! Neuroline Pattern Recognition
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        return bool(re.match(pattern, password))
    
    def login_user(self, username, password):
        user_exists = self.cursor.execute("SELECT * FROM users WHERE username= (?)", (username, )).fetchone()
        if user_exists:
            password_hash = self.hash_password(password)
            if password_hash == user_exists[2]:
                self.user = user_exists
                return True
        
        return False
        
    def register_user(self, username, password, workspace):
        try:
            password_hash = self.hash_password(password)
            try:
                os.makedirs(workspace, exist_ok=True)
            except OSError:
                messagebox.show_error("OS Error", "failed to create directory!")
            self.cursor.execute("""
                INSERT INTO users (username, password, workspace)
                VALUES (?, ?, ?)
            """, (username, password_hash, workspace))
            self.conn.commit()

        
        except sqlite3.IntegrityError as e:
            return 

    def fetch_usernames(self):
        data = []
        results = self.cursor.execute("SELECT * FROM users").fetchall()
        for username in range(len(results)):
            data.append(results[username][1])
        return data

class AuthView(ctk.CTkToplevel):
    def __init__(self, user_manager, on_login_success):
        super().__init__()
        self.user_manager = user_manager
        self.on_login_success = on_login_success
        self.title("Auth | BrainyStudio")
        self.logged_in = False
        self.resizable(False, False)
        self.configure(fg_color=Colors.PRIMARY)
        self.geometry(centerWindow(self, 900, 550, self._get_window_scaling()))
        self.message_box, self.message_title, self.message_desc, self.close_btn = None, None, None, None
        
    def build(self):
        self.container = ctk.CTkFrame(
            self, width=850, height=500, fg_color=Colors.SECONDARY, corner_radius=12
        )
        self.container.place(relx=0.5, rely=0.5, anchor="center")
        self.container.pack_propagate(False)

        self.image_frame = ctk.CTkFrame(
            self.container, width=250, height=500, fg_color=Colors.PRIMARY, corner_radius=0
        )
        self.image_frame.pack(side="left", fill="y")
        self.image_frame.pack_propagate(False)

        ctk.CTkLabel(self.image_frame, text="Brainy Studio",
                     font=("Inter", 22, "bold"), text_color=Colors.Texts.HEADERS).pack(pady=20)

        ctk.CTkLabel(self.image_frame, text="Innovate. Learn. Grow.",
                     font=("Inter", 14), text_color=Colors.Texts.FIELDS).pack()

        ctk.CTkLabel(self.image_frame, text="", image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\logo.png")), size=(220, 220))).pack(pady=50)

        self.content_frame = ctk.CTkFrame(self.container, width=600, height=500, fg_color=Colors.SECONDARY)
        self.content_frame.pack(side="right", fill="y")
        self.content_frame.pack_propagate(False)

        self.tab_view = ctk.CTkTabview(self.content_frame, segmented_button_fg_color=Colors.SECONDARY, fg_color="transparent", text_color=Colors.Texts.HEADERS, segmented_button_selected_color="#1A237E", segmented_button_unselected_color="#7986CB", width=550, border_color=Colors.Texts.BORDER)
        self.tab_view.place(relx=0.5, rely=0.6, anchor="center")
        self.tab_view.add("Login")
        self.tab_view.add("Register")

        self.create_login_form()
        self.create_register_form()

    def create_login_form(self):
        login_frame = self.tab_view.tab("Login")
        login_frame.configure(width=550, height=550)
        login_frame.pack_propagate(False)

        ctk.CTkLabel(login_frame, text="Welcome Back!", font=("Inter", 20, "bold"), text_color=Colors.Texts.HEADERS).pack(pady=20)

        self.login_username_entry = ctk.CTkEntry(login_frame, placeholder_text="Username", fg_color=Colors.PRIMARY, corner_radius=8, width=280, height=34)
        self.login_username_entry.pack(pady=5, padx=10)

        self.login_password_entry = ctk.CTkEntry(login_frame, placeholder_text="Password", show="●", fg_color=Colors.PRIMARY, corner_radius=8, width=280, height=34)
        self.login_password_entry.pack(pady=5, padx=10)

        PrimaryButton(login_frame, text="Login", width=200, command=self.on_login).pack(pady=10)

    def create_register_form(self):
        self.register_frame = self.tab_view.tab("Register")
        self.register_frame.configure(width=550, height=550)
        self.register_frame.pack_propagate(False)

        ctk.CTkLabel(self.register_frame, text="Create an Account", font=("Inter", 20, "bold"), text_color=Colors.Texts.HEADERS).pack(pady=10, anchor="center")

        self.register_username_entry = ctk.CTkEntry(self.register_frame, placeholder_text="Username", fg_color=Colors.PRIMARY, corner_radius=8, width=280, height=34)
        self.register_username_entry.pack(pady=5, padx=10)

        self.register_username_entry.bind("<KeyRelease>", self.update_workspace_field)

        self.register_password1_entry = ctk.CTkEntry(self.register_frame, placeholder_text="Create Strong Password", show="●", fg_color=Colors.PRIMARY, corner_radius=8, width=280, height=34)
        self.register_password1_entry.pack(pady=5, padx=10)

        self.register_password2_entry = ctk.CTkEntry(self.register_frame, placeholder_text="Confirm Password", show="●", fg_color=Colors.PRIMARY, corner_radius=8, width=280, height=34)
        self.register_password2_entry.pack(pady=5, padx=10)

        self.workspace_frame = ctk.CTkFrame(self.register_frame, fg_color="transparent")
        self.workspace_frame.pack(pady=10, padx=10, fill="x", anchor="center")

        ctk.CTkLabel(self.workspace_frame, text="Workspace Directory:", font=("Inter", 14), text_color=Colors.Texts.HEADERS).pack(padx=10, pady=10, side="left")

        self.workspace_option = ctk.StringVar(value="default")

        self.default_workspace_radio = ctk.CTkRadioButton(self.workspace_frame, text="Default", variable=self.workspace_option, value="default", command=self.toggle_workspace_selection)
        self.default_workspace_radio.pack(padx=10, pady=10, side="left")

        self.custom_workspace_radio = ctk.CTkRadioButton(self.workspace_frame, text="Custom", variable=self.workspace_option, value="custom", command=self.toggle_workspace_selection)

        self.custom_workspace_radio.pack(padx=10, pady=10, side="left")

        self.custom_workspace_frame = ctk.CTkFrame(self.register_frame, fg_color="transparent")
        self.custom_workspace_frame.pack(pady=10, padx=10, fill="x", anchor="center")

        ctk.CTkLabel(self.custom_workspace_frame, text="Filepath:", font=("Inter", 14), text_color=Colors.Texts.HEADERS).pack(padx=10, pady=10, side="left")

        self.workspace_entry = ctk.CTkEntry(self.custom_workspace_frame, placeholder_text="Select workspace folder", fg_color=Colors.PRIMARY, corner_radius=8, width=280, height=34, state="disabled")
        self.workspace_entry.pack(side="left", padx=10, pady=10)

        self.browse_button = ctk.CTkButton(self.custom_workspace_frame, text="Browse", command=self.browse_workspace, state="disabled")
        self.browse_button.pack(side="left", padx=10, pady=10)

        PrimaryButton(self.register_frame, text="Register", width=200, command=self.on_register).pack(pady=10)

    def toggle_workspace_selection(self):
        if self.workspace_option.get() == "custom":
            self.workspace_entry.configure(state="normal")
            self.browse_button.configure(state="normal")
        else:
            self.workspace_entry.configure(state="disabled")
            self.browse_button.configure(state="disabled")
            self.update_workspace_field(event=None)

    def browse_workspace(self):
        folder_selected = fd.askdirectory()
        if folder_selected:
            self.workspace_entry.delete(0, "end")
            self.workspace_entry.insert(0, folder_selected)
    
    def on_login(self):
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()

        user = self.user_manager.login_user(username, password)
        if not user:
            self.showMessageBox()
            self.message_title.configure(text="  Invalid Credentials  ", fg_color="red")
            self.message_desc.configure(text="Either password or username is incorrect. both are case-sensetive")
            self.after(4000, self.onMessageboxClose)
            return
        
        self.logged_in = True
        self.on_login_success()

    def on_register(self):

        username = self.register_username_entry.get()
        password1 = self.register_password1_entry.get()
        password2 = self.register_password2_entry.get()
        existed_users = self.user_manager.fetch_usernames()
        
        if len(username) < 6:
            self.showMessageBox()
            self.message_title.configure(text="  Invalid Username  ", fg_color="red")
            self.message_desc.configure(text="The username is too short!")
            self.after(4000, self.onMessageboxClose)
            return
        
        if username in existed_users:
            self.showMessageBox()
            self.message_title.configure(text="  Username Exists  ", fg_color="red")
            self.message_desc.configure(text="The username already exists!")
            self.after(4000, self.onMessageboxClose)
            return
        
        if not self.user_manager.is_strong_password(password=password1):
            self.showMessageBox()
            self.message_box.configure(height=50)
            self.message_title.configure(text="  Weak Password  ", fg_color="red")
            self.message_desc.configure(text="The password must be 8 characters long and contains \none uppercase, one lowercase, digits and alphanumeric symbols.")
            self.after(6000, self.onMessageboxClose)
            return
        
        if password1 != password2:
            self.showMessageBox()
            self.message_box.configure(height=50)
            self.message_title.configure(text="  Re-enter Password  ", fg_color="red")
            self.message_desc.configure(text="The Password did not match")
            self.after(6000, self.onMessageboxClose)
            return
        
        if self.workspace_option.get() == "default":
            workspace_path = getPath(f"workspace\\{username}")
        else:
            workspace_path = self.workspace_entry.get().strip()
            if not workspace_path:
                self.showMessageBox()
                self.message_title.configure(text="  Missing Workspace  ", fg_color="red")
                self.message_desc.configure(text="Please select a valid workspace directory.")
                self.after(4000, self.onMessageboxClose)
                return
    
        self.user_manager.register_user(username , password1, workspace_path)
        self.user_manager.login_user(username, password1)
        self.on_login_success()

    def showMessageBox(self):
        if self.message_box is None:
            self.message_box = ctk.CTkFrame(
                self.content_frame, fg_color="#FDEDEC",
                border_color="#E74C3C",
                border_width=2, height=40
            )
            self.message_box.pack_propagate(False)
            self.message_box.pack(padx=10, pady=10, anchor="center", fill="x")
            if self.message_box is not None:
                self.message_title = ctk.CTkLabel(
                    self.message_box,
                    text_color="#FFFFFF",
                    text="",
                    fg_color="#FDEDEC",
                    image=None
                )
                self.message_title.pack(side="left", fill="both")

                self.message_desc = ctk.CTkLabel(
                    self.message_box,
                    text_color="#212121",
                    text="",
                    fg_color="transparent"
                )
                self.message_desc.pack(padx=10, pady=10, side="left")

                self.close_btn = ctk.CTkButton(
                    self.message_box,
                    text="",
                    image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\cross.png")), size=(10, 10)),
                    width=10, height=10,
                    fg_color="#FDEDEC",
                    hover_color="#FDEDEC",
                    border_color="#FDEDEC",
                    border_width=2, corner_radius=50,
                    command=self.onMessageboxClose
                )
                self.close_btn.pack(padx=10, pady=10, side="right")


    def update_workspace_field(self, event=None):

        username = self.register_username_entry.get().strip()
        if username:
            default_workspace = getPath(f"workspace\\{username}")
            self.workspace_entry.configure(state="normal")
            self.workspace_entry.delete(0, "end")
            self.workspace_entry.insert(0, default_workspace)
            self.workspace_entry.configure(state="disabled")
    
    def onMessageboxClose(self):
        if self.message_box:
            self.message_box.pack_forget()
        self.message_box = None
    
    def run(self):
        self.build()
        self.mainloop()
