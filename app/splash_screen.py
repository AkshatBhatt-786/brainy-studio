import customtkinter as ctk
from PIL import Image
import os
from ui_components import Colors
from utils import centerWindow

BOLD_FONT = "TimesRoman"

class SplashScreen:
    def __init__(self, root, logo_path, duration=2):
        self.root = root
        self.root.overrideredirect(True)
        self.duration = duration

        window_width = 800
        window_height = 500
        self.root.geometry(centerWindow(self.root, window_width, window_height, self.root._get_window_scaling(), (0, 100)))

        self.main_frame = ctk.CTkFrame(self.root, fg_color=Colors.PRIMARY)
        self.main_frame.pack(fill="both", expand=True)

        self.logo_photo = None
        if os.path.exists(logo_path):
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((250, 250), Image.LANCZOS)
            self.logo_photo = ctk.CTkImage(light_image=logo_image, size=(250, 250))

        self.logo_label = ctk.CTkLabel(self.main_frame, image=self.logo_photo, text="")
        self.logo_label.pack(pady=(50, 20))

        self.app_name_label = ctk.CTkLabel(
            self.main_frame,
            text="Where creativity meets precision.",
            font=(BOLD_FONT, 20, "bold"),
            text_color=Colors.Texts.HEADERS
        )
        self.app_name_label.pack(pady=(0, 30))

        self.loading_indicator = ctk.CTkCanvas(
            self.main_frame,
            width=150,
            height=4,
            bg=Colors.PRIMARY,
            highlightthickness=0
        )
        self.loading_indicator.pack(pady=10)

        self.progress = 0
        self.max_progress = 100
        self.update_interval = int((self.duration * 1000) / self.max_progress)  # ~70ms for 7 sec

        self._animate_loading()
        self.root.mainloop()

    def _animate_loading(self):
        self.loading_indicator.delete("all")

        bar_width = int((self.progress / self.max_progress) * 150)
        color = self._interpolate_color(Colors.ACCENT, Colors.HIGHLIGHT, self.progress / self.max_progress)

        self.loading_indicator.create_rectangle(
            0, 0, bar_width, 4, fill=color, outline=""
        )

        if self.progress < self.max_progress:
            self.progress += 1
            self.root.after(self.update_interval, self._animate_loading)
        else:
            self.root.overrideredirect("False")
            self.root.geometry(centerWindow(self.root, 900, 550, self.root._get_window_scaling()))
            self.root.resizable(False, False)
            self.root.build()


    def _interpolate_color(self, c1, c2, t):
        c1 = tuple(int(c1[i:i+2], 16) for i in (1, 3, 5))
        c2 = tuple(int(c2[i:i+2], 16) for i in (1, 3, 5))
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        return f"#{r:02x}{g:02x}{b:02x}"
