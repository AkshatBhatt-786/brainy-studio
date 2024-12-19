import os
import sys
from json import JSONDecodeError

import pyperclip
import yaml
import json
import customtkinter as ctk
import time
from PIL import Image
from typing import Tuple
from icecream import ic
from threading import Thread
from socket import create_connection


ic.configureOutput(prefix="debug", includeContext=True, contextAbsPath=True)

# utils methods


def get_resource_path(resource_path: str, force_get: bool = False):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    filepath = os.path.join(base_path, resource_path)

    if force_get:
        return filepath

    if os.path.exists(filepath):
        return filepath

    return None


def get_value(key: str, reference: dict, default_value=None):
    keys = key.split(".")
    value = reference
    try:
        for k in keys:
            value = value[k]
        return value
    except KeyError or TypeError:
        ic("using default: " + default_value)
        return default_value
    except Exception as e:
        ic("using default: " + default_value)
        return default_value


def center_window(parent: ctk.CTk, width: int, height: int, scale_factor: float = 1.0, variation: Tuple[int, int] = (0, 0)):
    screen_width = parent.winfo_screenwidth()
    screen_height = parent.winfo_screenheight()

    x = int(((screen_width/2) - (width/2)) * scale_factor)
    y = int(((screen_height/2) - (height/1.5)) * scale_factor)

    scaled_width = x + variation[0]
    scaled_height = y + variation[1]
    return f"{width}x{height}+{scaled_width}+{scaled_height}"



class ThemeManager:

    def __init__(self):
        self.theme = {}
        self.theme_path = get_resource_path("assets\\themes\\light_theme.yaml")
        self.loadTheme()

    def loadTheme(self):
        if self.theme_path:
            with open(self.theme_path, "r") as f:
                self.theme = yaml.safe_load(f)
            return

    def loadComponentStyle(self, component_name):
        return get_value(component_name, self.theme, {})


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.theme = themeManager.theme
        self._windows_set_titlebar_color("light")
        self._icon_path = get_resource_path("assets\\icons\\icon.ico")
        if self._icon_path:
            self.iconbitmap(self._icon_path)
        self.title("Get started with BrainyStudio")
        self.geometry(center_window(self, 1200, 600, self._get_window_scaling(), (0, 50)))
        self.running = True
        self.isConnected = self.checkNetwork()
        # sidebar configurations
        self.sidebar, self.name_frame, self.icon_frame, self.frame = None, None, None, None
        self.message_box = None
        self.start_pos = 0
        self.end_pos = -0.2
        self.in_start_pos = True
        self.pos = self.start_pos
        self.start_pos = self.start_pos + 0.02
        self.width = abs(self.start_pos - self.end_pos)
        self.halfway_pos = ((self.start_pos + self.end_pos) / 2) - 0.06
        self.sidebar_css = themeManager.loadComponentStyle("theme.sidebar")
        self.bind_all('<Shift-A>', self.show_api_configurations)
        self.bind_all('<Shift-C>', self.clearFrame)
        self.dbx_frame = None
        self.btn_frame = None


    def build(self):
        self.configure(fg_color=get_value("theme.primary", self.theme, "#E5D3FF"))
        if self.frame is None:
            self.frame = ctk.CTkFrame(
                self, fg_color=get_value("theme.background", self.theme, "#B39DDB"),
                border_color=get_value("theme.border_color", self.theme, "#7E57C2"),
                border_width=2, corner_radius=10
            )
            self.frame.place(relx=0.08, rely=0.09, relwidth=0.9, relheight=0.9)

        if self.sidebar is None:
            self.sidebar = ctk.CTkFrame(
                self, fg_color=get_value("background", self.sidebar_css, "#B39DDB"),
                border_color=get_value("border_color", self.sidebar_css, "#7E57C2"),
                border_width=2, corner_radius=10
            )
            self.sidebar.place(relx=self.start_pos, rely=0.14, relwidth=self.width, relheight=0.8)
            self.sidebar.columnconfigure((0, 1), weight=1)
            self.sidebar.rowconfigure(0, weight=1)

            if self.name_frame is None:
                self.name_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="#E1F5FE", corner_radius=8, width=140,
                                                         scrollbar_fg_color="#E1F5FE", scrollbar_button_color="#E1F5FE",
                                                         scrollbar_button_hover_color="#E1F5FE")
                self.name_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
                self.name_frame.pack_propagate(False)

            if self.icon_frame is None:
                self.icon_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="#C4E4E7", corner_radius=8, width=60,
                                                         scrollbar_fg_color="#C4E4E7", scrollbar_button_color="#C3E4E7",
                                                         scrollbar_button_hover_color="#C3E4E7")
                self.icon_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
                self.icon_frame.pack_propagate(False)
                self.icon_frame.grid_propagate(flag=False)

                self.toggle_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\menu-burger.png")), size=(25, 25)), width=20, height=20, command=self.animate)
                self.toggle_btn.grid(row=0, column=0, pady=20, padx=5, sticky="nsew")

                self.toggle_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\add-document.png")),
                                       size=(25, 25)), width=20, height=20, command=self.display_content("create-exam"))
                self.toggle_btn.grid(row=1, column=0, pady=20, padx=5, sticky="nsew")



    def showMessageBox(self):
        if self.message_box is None:
            self.message_box = ctk.CTkFrame(
                self, fg_color=get_value("theme.message_box.background", self.theme, "#FDEDEC"),
                border_color=get_value("theme.message_box.border_color", self.theme, "#E74C3C"),
                border_width=2, height=40
            )
            self.message_box.pack_propagate(False)
            self.message_box.pack(padx=10, pady=10, anchor="center", fill="x")
            if self.message_box is not None:
                self.message_title = ctk.CTkLabel(
                    self.message_box,
                    text_color=get_value("theme.message_box.text_secondary", self.theme, "#FFFFFF"),
                    text="",
                    fg_color=get_value("theme.message_box.background", self.theme, "#FDEDEC"),
                    image=None
                )
                self.message_title.pack(side="left", fill="both")

                self.message_desc = ctk.CTkLabel(
                    self.message_box,
                    text_color=get_value("theme.message_box.text_primary", self.theme, "#212121"),
                    text="",
                    fg_color="transparent"
                )
                self.message_desc.pack(padx=10, pady=10, side="left")

                self.close_btn = ctk.CTkButton(
                    self.message_box,
                    text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\cross.png")), size=(10, 10)),
                    width=10, height=10,
                    fg_color=get_value("theme.message_box.button.background", self.theme, "#FDEDEC"),
                    hover_color=get_value("theme.message_box.button.on_hover", self.theme, "#FDEDEC"),
                    border_color=get_value("theme.message_box.button.border_color", self.theme, "#FDEDEC"),
                    border_width=2, corner_radius=50,
                    command=self.onMessageboxClose
                )
                self.close_btn.pack(padx=10, pady=10, side="right")

    def clearFrame(self, event=None):
        for widget in self.frame.winfo_children():
            widget.destroy()
        if self.dbx_frame:
            self.dbx_frame = None

    def onMessageboxClose(self):
        if self.message_box:
            self.message_box.pack_forget()
        self.message_box = None

    def animate(self):
        if self.in_start_pos:
            self.animate_to(self.halfway_pos)
        else:
            self.animate_to(self.start_pos)

    def animate_to(self, target_pos):
        if abs(self.pos - target_pos) > 0.008:
            step = -0.008 if self.pos > target_pos else 0.008
            self.pos += step
            self.sidebar.place(relx=self.pos, rely=0.14, relwidth=self.width, relheight=0.8)
            self.sidebar.after(10, self.animate_to, target_pos)
        else:
            self.pos = target_pos
            self.sidebar.place(relx=self.pos, rely=0.14, relwidth=self.width, relheight=0.8)
            self.in_start_pos = self.pos == self.start_pos

    def display_content(self, content_type):
        for widget in self.frame.winfo_children():
            widget.destroy()

        if content_type == "api-configurations":
            self.show_api_configurations()
        if content_type == "create-exam":
            self.show_create_exam_view()

    def show_create_exam_view(self):
        self.header_frame = ctk.CTkFrame(self.frame, fg_color="#F5F5F5", corner_radius=0)
        self.header_frame.pack(padx=25, pady=10, anchor="center", fill="x")

        self.workspace_frame = ctk.CTkScrollableFrame(
            self.frame, fg_color="#F5F5F5", border_color="#333333", border_width=0,
            scrollbar_fg_color="#F5F5F5", scrollbar_button_color="#f5F5F5",
            scrollbar_button_hover_color="#F5F5F5"
        )
        self.workspace_frame.pack(padx=25, anchor="center", fill="both", expand=True)

    def show_api_configurations(self, event=None):

        ERROR_404 = False
        config_file_path = get_resource_path("data\\config.json")
        if config_file_path:
            with open(config_file_path, "r") as f:
                data = json.load(f)
        else:
            self.showMessageBox()
            self.message_title.configure(
                image=ctk.CTkImage(
                    light_image=Image.open(get_resource_path("assets\\symbols\\not-found.png")), size=(20, 20)
                ), text="File not Found", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                fg_color="#D32F2F"
            )
            self.message_desc.configure(text="The API configurations file is missing!")
            ERROR_404 = True

        if not ERROR_404:
            try:
                access_token = data["access_token"]
                app_key = data["app_key"]
                app_secret = data["app_secret"]
            except Exception as e:
                self.showMessageBox()
                self.message_title.configure(
                    image=ctk.CTkImage(
                        light_image=Image.open(get_resource_path("assets\\symbols\\not-found.png")), size=(20, 20)
                    ), text="File not Found", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                    fg_color="#D32F2F"
                )
                self.message_desc.configure(text="The API configurations file is missing!")
                return
        else:
            return

        if self.dbx_frame is None:
            (ctk.CTkLabel(
                self.frame, text="API CONFIGURATIONS",
                font=ctk.CTkFont(family="Game Of Squids", size=28, weight="bold"),
                text_color=get_value("theme.text_primary", self.theme, "#212121"))
             .pack(padx=10, pady=20, anchor="center"))

            self.dbx_frame = ctk.CTkFrame(self.frame, fg_color="#F5F5F5")
            self.dbx_frame.pack(padx=25, pady=10, anchor="center", fill="x")

            self.btn_frame = ctk.CTkFrame(self.frame, fg_color="#FFFFFF")
            self.btn_frame.pack(padx=25, pady=10, anchor="center", fill="x")

            (ctk.CTkLabel(
                self.dbx_frame, text=f"Access Token", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                text_color=get_value("theme.text_primary", self.theme, "#")
            ).grid(row=0, column=1, padx=10, pady=10, sticky="w"))

            self.access_token_entry = ctk.CTkEntry(
                self.dbx_frame, text_color="#212121", fg_color="#F5F5F5", border_color="#F5F5F5", width=810, height=30)
            self.access_token_entry.grid(row=0, column=2, padx=10, pady=10, sticky="w")
            self.access_token_entry.insert(0, f"{access_token}")
            self.access_token_entry.configure(state="disabled")

            ctk.CTkButton(
                self.dbx_frame, text="", image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\copy.png")), size=(20, 20)),
                width=30, height=30, fg_color="#F5F5F5", hover_color="#F5F5F5", command=lambda: self.copyText(text=access_token, name="access token")
            ).grid(row=0, column=3, padx=10, pady=10, sticky="e")

            (ctk.CTkLabel(
                self.dbx_frame, text=f"App Key", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                text_color=get_value("theme.text_primary", self.theme, "#")
            ).grid(row=1, column=1, padx=10, pady=10, sticky="w"))

            self.app_key_entry = ctk.CTkEntry(
                self.dbx_frame, text_color="#212121", fg_color="#F5F5F5", width=810, height=30, border_color="#F5F5F5")
            self.app_key_entry.grid(row=1, column=2, padx=10, pady=10, sticky="w")
            self.app_key_entry.insert(0, f"{app_key}")
            self.app_key_entry.configure(state="disabled")

            ctk.CTkButton(
                self.dbx_frame, text="",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\copy.png")), size=(20, 20)),
                width=30, height=30, fg_color="#F5F5F5", hover_color="#F5F5F5", command=lambda: self.copyText(text=app_key, name="app key")
            ).grid(row=1, column=3, padx=10, pady=10, sticky="e")

            (ctk.CTkLabel(
                self.dbx_frame, text=f"App Secret", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                text_color=get_value("theme.text_primary", self.theme, "#"),
            ).grid(row=2, column=1, padx=10, pady=10, sticky="w"))

            self.app_secret_entry = ctk.CTkEntry(
                self.dbx_frame, text_color="#212121", fg_color="#F5F5F5", width=810, height=30, border_color="#F5F5F5")
            self.app_secret_entry.grid(row=2, column=2, padx=10, pady=10, sticky="w")
            self.app_secret_entry.insert(0, f"{app_secret}")
            self.app_secret_entry.configure(state="disabled")

            ctk.CTkButton(
                self.dbx_frame, text="",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\copy.png")), size=(20, 20)),
                width=30, height=30, fg_color="#F5F5F5", hover_color="#F5F5F5", command=lambda: self.copyText(text=app_secret, name="app secret")
            ).grid(row=2, column=3, padx=10, pady=10, sticky="e")

            self.edit_configuration_btn = (ctk.CTkButton(
                self.btn_frame, text="Edit Configurations", width=120, height=38,
                fg_color="#2196F3", hover_color="#1E88E5", text_color="#FFFFFF",
                border_color="#1565C0", border_width=2, corner_radius=8, command=lambda: self.editConfigurations()
            ))
            self.edit_configuration_btn.pack(padx=10, pady=10, side="right")


    def copyText(self, text: str, name: str):
        pyperclip.copy(text)
        self.showMessageBox()
        self.message_title.configure(text="Copy Successful", image=ctk.CTkImage(
            light_image=(Image.open(get_resource_path("assets\\symbols\\check-circle.png"))),
            size=(20, 20)
        ), text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#4CAF50")
        self.message_desc.configure(text=f"The {name} has been successfully copied to your clipboard.")

    def saveConfigurations(self):
        data = {
            "access_token": self.access_token_entry.get(),
            "app_key": self.app_key_entry.get(),
            "app_secret": self.app_secret_entry.get()
        }
        try:
            with open(get_resource_path("data\\config.json", force_get=True), "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            return

        self.save_btn.destroy()

        self.access_token_entry.configure(state="disabled")
        self.app_secret_entry.configure(state="disabled")
        self.app_key_entry.configure(state="disabled")

        self.edit_configuration_btn = ctk.CTkButton(
            self.btn_frame, text="Edit Configurations", width=120, height=38,
            fg_color="#2196F3", hover_color="#1E88E5", text_color="#FFFFFF",
            border_color="#1565C0", border_width=2, corner_radius=8, command=lambda: self.editConfigurations()
        )
        self.edit_configuration_btn.pack(padx=10, pady=10, side="right")

    def editConfigurations(self):
        self.app_secret_entry.configure(state="normal")
        self.app_key_entry.configure(state="normal")
        self.access_token_entry.configure(state="normal")

        if hasattr(self, 'edit_configuration_btn'):
            self.edit_configuration_btn.destroy()

        self.save_btn = ctk.CTkButton(
            self.btn_frame, text="Save Configurations", width=120, height=38,
            fg_color="#2196F3", hover_color="#1E88E5", text_color="#FFFFFF",
            border_color="#1565C0", border_width=2, corner_radius=8, command=lambda: self.saveConfigurations()
        )
        self.save_btn.pack(padx=10, pady=10, side="right")

    def run(self):
        self.configureThreadManagement()
        self.build()
        self.mainloop()

    def configureThreadManagement(self):
        self.network_thread = Thread(target=self.runNetworkCheck, daemon=True)
        self.network_thread.start()

    @staticmethod
    def checkNetwork():
        try:
            create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False

    def updateNetworkStatus(self):
        if not self.running:
            return

        self.isConnected = self.checkNetwork()
        if self.isConnected:
            self.title("Get Started with BrainyStudio")
        else:
            self.showMessageBox()
            self.title("Server Not Found ~ BrainyStudio")
            if self.message_box:
                self.message_title.configure(
                    image=ctk.CTkImage(
                        light_image=Image.open(get_resource_path("assets\\symbols\\not-found.png")), size=(20, 20)
                    ), text="No Internet Connection", text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#D32F2F"
                )
                self.message_desc.configure(text="Oops! It seems we are having trouble connecting to the server. Please check your connection and retry.")

    def runNetworkCheck(self):
        while True:
            self.updateNetworkStatus()
            time.sleep(5)


if __name__ == '__main__':
    themeManager = ThemeManager()
    ic(themeManager.theme)
    App().run()
