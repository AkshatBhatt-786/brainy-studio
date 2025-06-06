# ==========================================================
#  * Project : Brainy Studio - Question Paper Generator
#  * Author  : Bhatt Akshat S
#  * Updated : 04-03-2025
#  * Version : 1.0.2
#  * License : MIT License
#  * GitHub  : https://github.com/AkshatBhatt-786/brainy-studio/blob/main/app/main.py
#  * Description:
#      This is the main entry point for Brainy Studio.
#      It initializes the UI, handles user authentication, 
#      and manages the navigation between different modules.
#  ^ Credits | References:
#  & Stack Overflow (https://stackoverflow.com/q/1234567)
#  & Python Docs (https://docs.python.org/3/library/)
#  & CustomTkinter Docs (https://customtkinter.tomschimansky.com/)
# ==========================================================

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import customtkinter as ctk
from tkinter import messagebox
from utils import getPath, centerWindow
from ui_components import Colors, IconButton, SidebarButton
from PIL import Image
import time
import os
import datetime
from users import UserManager, AuthView
from create_paper import CreatePaper
from generate_pdf import GeneratePDFUI
from cloud_export import CloudPublishUI
from subject_db import SubjectDBManager
from excel_export import ExportToExcelUI
from admin_panel import AdminPanel
from codex_formatter import CodexFormatter

subject_db = SubjectDBManager()

class WorkspaceEventHandler(FileSystemEventHandler):
    def __init__(self, app, observer):
        self.app = app
        self.observer = observer

    def on_created(self, event):
        if not event.is_directory:
            self.app.after(0, self.app.load_recent_projects)

    def on_deleted(self, event):
        workspace_path = self.app.user_manager.user[3]

        if not os.path.exists(workspace_path):
            self.observer.stop()
        else:
            self.app.after(0, self.app.load_recent_projects)

    def on_modified(self, event):
        pass


def watch_workspace(app, user):
    workspace_path = user[3]

    if not os.path.exists(workspace_path):
        return

    observer = Observer()
    event_handler = WorkspaceEventHandler(app, observer)
    observer.schedule(event_handler, workspace_path, recursive=True)
    observer.start()

    def run_observer():
        try:
            observer.join()
        except KeyboardInterrupt:
            observer.stop()

    thread = threading.Thread(target=run_observer, daemon=True)
    thread.start()


class BrainyStudioApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Brainy Studio v1.0.2 (Beta)")
        self.minsize(700, 600)
        self.geometry(centerWindow(self, 1150, 720, self._get_window_scaling(), (0, 130)))
        self.iconbitmap(bitmap=getPath("assets\\icons\\icon.ico"))
        self.content_frame = None
        self.user_manager = UserManager()
        self.auth_view = AuthView(self.user_manager, self.on_login_success)
        self.icon_frame, self.name_frame = None, None
        self.start_pos = 0
        self.end_pos = -0.2
        self.in_start_pos = True
        self.pos = self.start_pos
        self.start_pos += 0.02
        self.width = abs(self.start_pos - self.end_pos)
        self.halfway_pos = ((self.start_pos + self.end_pos) / 2) - 0.06
        self.configure(fg_color=Colors.BACKGROUND)
        self.create_paper = None
        self.edit_page = None
        self.attributes("-topmost", True)
        self.main_content = ctk.CTkFrame(
            master=self,
            fg_color=Colors.PRIMARY,
            # scrollbar_button_color=Colors.BACKGROUND,
            # scrollbar_button_hover_color=Colors.HIGHLIGHT,
            corner_radius=15,
            border_width=0,
            border_color=Colors.Texts.BORDER
        )
        self.main_content.place(relx=0.25, rely=0.09, relwidth=0.7, relheight=0.9)

        self.sidebar = ctk.CTkFrame(
            master=self,
            fg_color=Colors.Sidebar.BACKGROUND,
            border_color=Colors.Sidebar.BORDER,
            border_width=2,
            corner_radius=10
        )

        if self.name_frame is None:
            self._create_name_frame()

        if self.icon_frame is None:
            self._create_icon_frame()

        self.sidebar.place(relx=self.start_pos, rely=0.14, relwidth=self.width, relheight=0.8)
        self.sidebar.columnconfigure((0, 1), weight=1)
        self.sidebar.rowconfigure(0, weight=1)
        self.auth_view.run()

    def on_login_success(self):
        self.auth_view.destroy()
        thread = threading.Thread(target=watch_workspace, args=(self, self.user_manager.user), daemon=True)
        thread.start()
        self.build()
        self.mainloop()

    def build(self):

        self.welcome_label = ctk.CTkLabel(
            master=self.main_content,
            text="Welcome to Brainy Studio!",
            font=("Arial", 32, "bold"),
            text_color=Colors.HIGHLIGHT,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\logo.png")), size=(70, 70)),
            compound="right"
        )
        self.welcome_label.pack(pady=(30, 15), padx=(10, 20))

        self.tagline_label = ctk.CTkLabel(
            master=self.main_content,
            text="Create, Edit, and Export your Digital Exam Papers effortlessly.",
            font=("Arial", 16, "italic"),
            text_color=Colors.Texts.FIELDS
        )
        self.tagline_label.pack(pady=(0, 30))

        self.action_grid = ctk.CTkFrame(
            master=self.main_content,
            fg_color="transparent"
        )
        self.action_grid.pack(padx=20, pady=10, expand=True, fill="both")
        self.action_grid.columnconfigure((0, 1, 2), weight=1, uniform="a")

        self._create_action_card("Create Paper", "assets\\images\\create-paper.png", 0, 0, lambda: self.redirect_to_create_paper_page())
        self._create_action_card("Edit Paper", "assets\\images\\edit.png", 0, 1, lambda: self.redirect("edit-page"))
        self._create_action_card("Export To PDF", "assets\\images\\pdf.png", 1, 0, lambda: self.redirect_to_export_page())
        self._create_action_card("Export To Cloud", "assets\\images\\cloud-computing.png", 0, 2, lambda: self.redirect("cloud-expo"))
        self._create_action_card("Open Codex Formatter", "assets\\images\\brainstorm.png", 1, 1, lambda: self.open_codex_formatter())
        self._create_action_card("Export to Excel", "assets\\images\\excel.png", 1, 2, lambda: self.redirect("excel-export-page"))

        self.footer_label = ctk.CTkLabel(
            master=self.main_content,
            text="Brainy Studio v1.0.2 (beta)",
            font=("Arial", 12),
            text_color=Colors.Footer.TEXT
        )
        self.footer_label.pack(side="bottom", pady=10)

    def redirect_to_edit_paper_page(self, filepath=None):
        if filepath:
            for widget in self.main_content.winfo_children():
                widget.destroy()

            self.edit_page = CreatePaper(self.main_content, parent=self, edit_mode=True, file_path=filepath)
            self.edit_page.pack(padx=10, pady=10, fill="both", expand=True)
        else:
            self.redirect("edit-page")

    def redirect_to_create_paper_page(self):
        self.redirect("create-paper")

    def redirect_to_home_page(self):
        self.redirect("home-page")

    def redirect_to_export_page(self):
        self.redirect("export-page")

    def redirect_to_export_excel(self):
        self.redirect("excel-export-page")

    def _create_name_frame(self):
        self.name_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color=Colors.PRIMARY,
            corner_radius=8,
            width=140,
            scrollbar_fg_color=Colors.PRIMARY,
            scrollbar_button_color=Colors.PRIMARY,
            scrollbar_button_hover_color=Colors.PRIMARY
        )
        self.name_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        self.name_frame.grid_propagate(flag=False)

        header_frame = ctk.CTkFrame(
            master=self.name_frame,
            fg_color=Colors.HIGHLIGHT,
            height=40,
            corner_radius=8
        )
        header_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        header_label = ctk.CTkLabel(
            master=header_frame,
            text="Welcome Back",
            font=("Arial", 12, "bold"),
            text_color="white"
        )
        header_label.pack(pady=5)

        self.logo = ctk.CTkLabel(
            master=self.name_frame,
            text="Brainy Studio",
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\logo.png")), size=(50, 50)),
            font=("Consolas", 14, "bold"),
            compound="top",
            text_color=Colors.HIGHLIGHT
        )
        self.logo.grid(row=1, column=0, pady=10, padx=10, sticky="nsew")

        self.home_redirect_link_btn = SidebarButton(
            master=self.name_frame,
            text="Home",
            command=lambda: self.redirect_to_home_page()
        )
        self.home_redirect_link_btn.grid(row=2, column=0, pady=10, sticky="w")

        self.create_paper_name_btn = SidebarButton(
            master=self.name_frame,
            text="Create Paper",
            command=lambda: self.redirect_to_create_paper_page()
        )
        self.create_paper_name_btn.grid(row=3, column=0, pady=10, sticky="w")

        self.edit_paper_name_btn = SidebarButton(
            master=self.name_frame,
            text="Edit Paper",
            command=lambda: self.redirect_to_edit_paper_page()
        )
        self.edit_paper_name_btn.grid(row=4, column=0, pady=10, sticky="w")

        self.cloud_dashboard_name_btn= SidebarButton(
            master=self.name_frame,
            text="Cloud Export",
            command=lambda: self.redirect("cloud-expo")
        )
        self.cloud_dashboard_name_btn.grid(row=5, column=0, pady=10, sticky="w")

        self.export_to_pdf_name_btn = SidebarButton(
            master=self.name_frame,
            text="Generate PDF",
            command=lambda: self.redirect_to_export_page()
        )
        self.export_to_pdf_name_btn.grid(row=6, column=0, pady=10, sticky="w")

        self.export_to_excel_name_btn = SidebarButton(
            master=self.name_frame,
            text="Generate EXCEL",
            command=lambda: self.redirect_to_export_excel()
        )
        self.export_to_excel_name_btn.grid(row=7, column=0, pady=10, sticky="w")

        self.configure_database_name_btn = SidebarButton(
            master=self.name_frame,
            text="Open Admin Panel",
            command=lambda: self.open_admin_panel()
        )
        self.configure_database_name_btn.grid(row=8, column=0, pady=10, sticky="w")

    def open_admin_panel(self):
        self.attributes("-topmost", False)
        self.admin_panel = AdminPanel(subject_db=subject_db)

    def _create_icon_frame(self):
        self.icon_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color=Colors.SECONDARY,
            corner_radius=8,
            width=60,
            scrollbar_fg_color=Colors.SECONDARY,
            scrollbar_button_color=Colors.SECONDARY,
            scrollbar_button_hover_color=Colors.SECONDARY
        )

        self.icon_frame.grid(row=0, column=1, padx=(5, 10), pady=5, sticky="nsew")
        self.icon_frame.pack_propagate(flag=False)
        self.icon_frame.grid_propagate(flag=False)

        self.toggle_btn = ctk.CTkButton(
            self.icon_frame,
            fg_color="transparent",
            text_color=Colors.Texts.BORDER,
            hover_color=Colors.SECONDARY,
            corner_radius=18,
            text="",
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\hamburger.png")), size=(30, 30)),
            width=20,
            height=20,
            command=self.animate
        )
        self.toggle_btn.grid(row=0, column=0, pady=20, padx=5, sticky="nsew")

        self.home_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\home.png")), size=(30, 30)),
            command=lambda: self.redirect_to_home_page()
        )
        self.home_btn.grid(row=1, column=0, pady=20, padx=5, sticky="nsew")

        self.create_paper_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\create-paper.png")), size=(30, 30)),
            command=lambda: self.redirect_to_create_paper_page()
        )
        self.create_paper_btn.grid(row=2, column=0, pady=20, padx=5, sticky="nsew")

        self.edit_paper_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\edit.png")), size=(30, 30)),
            command=lambda: self.redirect_to_edit_paper_page()
        )
        self.edit_paper_btn.grid(row=3, column=0, pady=20, padx=5, sticky="nsew")

        self.cloud_dashboard_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\cloud-computing.png")), size=(30, 30)),
            command=lambda: self.redirect("cloud-expo")
        )
        self.cloud_dashboard_btn.grid(row=4, column=0, pady=20, padx=5, sticky="nsew")

        self.export_to_pdf_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\pdf.png")), size=(30, 30)),
            command=lambda: self.redirect_to_export_page()
        )
        self.export_to_pdf_btn.grid(row=5, column=0, pady=20, padx=5, sticky="nsew")

        self.export_to_excel_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\excel.png")), size=(30, 30)),
            command=lambda: self.redirect_to_export_excel()
        )
        self.export_to_excel_btn.grid(row=6, column=0, pady=20, padx=5, sticky="nsew")

        self.configure_database_btn = IconButton(
            self.icon_frame,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\brainstorm.png")), size=(30, 30)),
            command=lambda: self.open_codex_formatter()
        )
        self.configure_database_btn.grid(row=7, column=0, pady=20, padx=5, sticky="nsew")

    def load_recent_projects(self):
        workspace_path = self.user_manager.user[3]
        if not os.path.exists(workspace_path):
            empty_label = ctk.CTkLabel(
                self.recent_projects_frame, 
                text="The database or workspace is been moved or may be deleted!.\nFor more queries contact the devloper team", 
                font=("Arial", 14)
            )
            empty_label.pack(pady=10)
            return

        for widget in self.recent_projects_frame.winfo_children():
            widget.destroy()

        header = ctk.CTkLabel(
            self.recent_projects_frame, 
            text="Recent Projects", 
            font=("Arial", 18, "bold"), 
            text_color=Colors.HIGHLIGHT
        )
        header.pack(pady=(10, 5))

        files = sorted(
            os.listdir(workspace_path), 
            key=lambda f: os.path.getctime(os.path.join(workspace_path, f)), 
            reverse=True
        )

        if not files:
            empty_label = ctk.CTkLabel(
                self.recent_projects_frame, 
                text="No recent files found.", 
                font=("Arial", 14)
            )
            empty_label.pack(pady=10)
            return

        for i, file in enumerate(files):
            file_path = os.path.join(workspace_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path) / 1024
                created_at = os.path.getctime(file_path)
                formatted_time = datetime.datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S")

                file_button = ctk.CTkButton(
                    self.recent_projects_frame, 
                    text=f"📁 {file}  |  {size:.2f} KB  |  {formatted_time}",
                    font=("Arial", 14),
                    fg_color=Colors.ACCENT, 
                    text_color="white",
                    hover_color=Colors.ACCENT,
                    corner_radius=10,
                    command=lambda f=file_path: self.redirect(page_name="edit-page", filepath=f)
                )
                file_button.pack(fill="x", padx=10, pady=5)

    def _create_action_card(self, text, image_path, row, column, callback):
        card = ctk.CTkFrame(
            master=self.action_grid,
            fg_color=Colors.Cards.BACKGROUND,
            corner_radius=20,
            border_width=2,
            border_color=Colors.Cards.BORDER
        )
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        card.columnconfigure(0, weight=1)

        icon = ctk.CTkLabel(
            master=card,
            image=ctk.CTkImage(light_image=Image.open(getPath(image_path)), size=(50, 50)),
            text="",
        )
        icon.pack(pady=15)

        label = ctk.CTkLabel(
            master=card,
            text=text,
            font=("Arial", 20, "bold"),
            text_color=Colors.HIGHLIGHT
        )
        label.pack(pady=10, anchor="center")

        btn = ctk.CTkButton(
            master=card,
            text=f"{text} Now",
            font=("Arial", 16, "bold"),
            corner_radius=15,
            height=32,
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER,
            text_color="white",
            cursor="hand2",
            command=callback
        )
        btn.pack(pady=20, padx=10)

    def animate(self):
        if self.in_start_pos:
            self.animate_to(self.halfway_pos)
            self.main_content.place_configure(relx=0.10, rely=0.09, relwidth=0.85, relheight=0.9)
        else:
            self.animate_to(self.start_pos)
            self.main_content.place_configure(relx=0.25, rely=0.09, relwidth=0.7, relheight=0.9)

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

    def redirect(self, page_name, filepath=None):
        for widget in self.main_content.winfo_children():
            widget.destroy()

        if page_name == "create-paper":
            if self.edit_page:
                self.edit_page.pack_forget()
            self.title("Create Paper")
            self.create_paper = CreatePaper(self.main_content, parent=self)
            self.create_paper.pack(padx=10, pady=10, anchor="center")

        if page_name == "home-page":
            self.title("Brainy Studio v1.0.2 (Beta)")
            if self.create_paper is not None:
                self.create_paper.pack_forget()
            self.build()

        if page_name == "edit-page":
            if self.create_paper:
                self.create_paper.pack_forget()
            self.title("Edit Paper")
            self.edit_page = CreatePaper(self.main_content, edit_mode=True, parent=self, file_path=filepath)
            self.edit_page.pack(padx=10, pady=10, anchor="center")

        if page_name == "cloud-expo":
            firebase_config, dropbox_config = os.getenv("FIREBASE_CONFIG"), os.getenv("DBX_BACKEND")
            if firebase_config is None or dropbox_config is None:
                messagebox.showinfo("Environment Not Configured", "This feature requires specific environments that are not detected in the system PATH.\nAccess is restricted until all required environments are properly configured.\n\nPlease contact the developer for assistance or configuration support.")
                self.redirect("home-page")
                return
            self.title("Export to Cloud")
            self.cloud_page = CloudPublishUI(self.main_content, parent=self, subject_db=subject_db)

        if page_name == "export-page":
            self.export_page = GeneratePDFUI(self, subject_db, self, self.main_content)

        if page_name == "excel-export-page":
            self.excel_page = ExportToExcelUI(self, self, self.main_content)

    def open_codex_formatter(self):
        self.attributes("-topmost", False)
        CodexFormatter(self)
        return
    
if __name__ == "__main__":
    app = BrainyStudioApp()
