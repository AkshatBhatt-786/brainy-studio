from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import customtkinter as ctk
from utils import getPath, centerWindow
from ui_components import Colors
from PIL import Image
import time
import os
import datetime
from users import UserManager, AuthView
from create_paper import CreatePaper


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
        self.title("Brainy Studio v1.0 (Beta)")
        self.minsize(700, 600)
        self.geometry(centerWindow(self, 1150, 600, self._get_window_scaling()))
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
            text_color=Colors.HIGHLIGHT
        )
        self.welcome_label.pack(pady=(30, 15))

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

        self._create_action_card("Create Paper", "assets\\images\\create-paper.png", 0, lambda: self.redirect_to_create_paper_page())
        self._create_action_card("Edit Paper", "assets\\images\\edit.png", 1, lambda: self.redirect("edit-page"))
        self._create_action_card("Export Paper", "assets\\images\\export.png", 2, None)

        self.recent_projects_frame = ctk.CTkFrame(self.main_content, fg_color=Colors.SECONDARY, corner_radius=10)
        self.recent_projects_frame.pack(padx=20, pady=10, expand=True, fill="both")
        self.recent_projects_frame.grid_propagate(flag=False)
        self.load_recent_projects()

        self.footer_label = ctk.CTkLabel(
            master=self.main_content,
            text="Brainy Studio v1.0",
            font=("Arial", 12),
            text_color=Colors.Footer.TEXT
        )
        self.footer_label.pack(side="bottom", pady=10)

    def redirect_to_create_paper_page(self):
        self.redirect("create-paper")

    def redirect_to_home_page(self):
        self.redirect("home-page")

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

        self.home_redirect_link_btn = ctk.CTkButton(
            master=self.name_frame,
            text="Home",
            font=("Calibri", 16, "bold"),
            hover_color=Colors.PRIMARY,
            fg_color=Colors.PRIMARY,
            width=120, corner_radius=12, height=38,
            text_color=Colors.Texts.BORDER,
            cursor="hand2"
        )
        self.home_redirect_link_btn.grid(row=2, column=0, pady=10, sticky="w")

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

        self.home_btn = ctk.CTkButton(
            self.icon_frame,
            fg_color="transparent",
            text_color=Colors.Texts.BORDER,
            hover_color=Colors.SECONDARY,
            corner_radius=18,
            text="",
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\home.png")), size=(30, 30)),
            width=20, height=20,
            cursor="hand2",
            command=lambda: self.redirect_to_home_page()
        )
        self.home_btn.grid(row=1, column=0, pady=20, padx=5, sticky="nsew")

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
                    command=lambda filepath=file_path: self.redirect_to_edit_paper_page(file_path)
                )
                file_button.pack(fill="x", padx=10, pady=5)

    def _create_action_card(self, text, image_path, column, callback):
        card = ctk.CTkFrame(
            master=self.action_grid,
            fg_color=Colors.Cards.BACKGROUND,
            corner_radius=20,
            border_width=2,
            border_color=Colors.Cards.BORDER
        )
        card.grid(row=0, column=column, padx=10, pady=10, sticky="nsew")
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

    
    def redirect_to_edit_paper_page(self, filepath=None):
        if filepath:
            for widget in self.main_content.winfo_children():
                widget.destroy()
            
            self.edit_page = CreatePaper(self, parent=self, edit_mode=True, file_path=filepath)
            self.edit_page.pack(padx=10, pady=10, fill="both", expand=True)
        else:
            # Handle new edit creation
            self.redirect("edit-paper")

    def redirect(self, page_name):
        for widget in self.main_content.winfo_children():
            widget.destroy()

        if page_name == "create-paper":
            if self.edit_page:
                self.edit_page.pack_forget()
            self.create_paper = CreatePaper(self.main_content, parent=self)
            self.create_paper.pack(padx=10, pady=10, anchor="center")

        if page_name == "home-page":
            if self.create_paper is not None:
                self.create_paper.pack_forget()
            self.build()

        if page_name == "edit-page":
            if self.create_paper:
                self.create_paper.pack_forget()
            self.edit_page = CreatePaper(self.main_content, edit_mode=True, parent=self)
            self.edit_page.pack(padx=10, pady=10, anchor="center")


if __name__ == "__main__":
    app = BrainyStudioApp()
