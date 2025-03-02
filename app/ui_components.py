import customtkinter as ctk
class Colors:
    
    PRIMARY = "#0F172A" 
    SECONDARY = "#1E293B" 
    ACCENT = "#3B82F6" 
    HIGHLIGHT = "#10B981"
    SUCCESS = "#22C55E" 
    WARNING = "#F59E0B" 
    DANGER = "#EF4444" 
    BACKGROUND = "#0F172A" 

    class Texts:
        HEADERS = "#F8FAFC" 
        FIELDS = "#E2E8F0" 
        PLACEHOLDER = "#94A3B8" 
        BORDER = "#475569" 

    class Sidebar:
        BACKGROUND = "#1E293B"
        BORDER = "#334155" 
        HOVER = "#334155" 

    class Buttons:
        PRIMARY = "#3B82F6"
        PRIMARY_HOVER = "#2563EB" 
        SECONDARY = "#10B981" 
        SECONDARY_HOVER = "#059669"  
        DISABLED = "#64748B" 

    class Inputs:
        BACKGROUND = "#1E293B"  
        BORDER = "#475569" 
        TEXT = "#E2E8F0"  
        PLACEHOLDER = "#94A3B8"  

    class Alerts:
        SUCCESS = "#22C55E" 
        WARNING = "#F59E0B"  
        DANGER = "#EF4444"
        INFO = "#3B82F6" 

    class Footer:
        BACKGROUND = "#0F172A"
        TEXT = "#94A3B8" 

    class Cards:
        BACKGROUND = "#1E293B" 
        BORDER = "#334155"  

    class Tables:
        HEADER_BACKGROUND = "#1E293B"  
        ROW_BACKGROUND = "#0F172A"
        ROW_HOVER = "#1E293B"  
        BORDER = "#334155"  

    class Modals:
        BACKGROUND = "#1E293B"
        BORDER = "#334155"


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text, width=200, height=50, **kwargs):
        super().__init__(master, text=text, width=width, height=height,
                         fg_color="#5C6BC0", border_color="#303F9F", corner_radius=8, text_color="white", 
                         border_width=2, hover_color="#3F51B5", cursor="hand2", **kwargs)

class ErrorButton(ctk.CTkButton):
    def __init__(self, master, text, width=200, height=50, **kwargs):
        super().__init__(master, text=text, width=width, height=height,
                         fg_color=Colors.DANGER, border_color="#E74C3C", corner_radius=8, text_color="white", 
                         border_width=2, hover_color="#FFC080", cursor="hand2", **kwargs)


class SearchButton(ctk.CTkButton):

    def __init__(self, master, text, width=130, height=50, **kwargs):
        super().__init__(master, text=text, width=width, height=height,
                         fg_color="#FF9800", border_color="#8E44AD", corner_radius=12, text_color="white", 
                         border_width=2, hover_color="#F57C00", cursor="hand2", **kwargs)

class NavigationBtn(ctk.CTkButton):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(
            fg_color="#8E44AD",
            hover_color="#8E44AD",
            width=35, height=35,
            text_color="#FFFFFF",
            cursor="hand2",
            font=("Poppins", 16)
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        self.configure(text_color="#A2DFF7")
    
    def on_leave(self, event):
        self.configure(text_color="#FFFFFF")


class SidebarButton(ctk.CTkButton):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(
            fg_color=Colors.SECONDARY,
            hover_color=Colors.PRIMARY,
            width=180, height=40,
            text_color=Colors.Texts.HEADERS,
            cursor="hand2",
            font=("Inter", 14, "bold")
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        self.configure(text_color=Colors.HIGHLIGHT)
    
    def on_leave(self, event):
        self.configure(text_color=Colors.Texts.HEADERS)

class CustomLabel(ctk.CTkLabel):
    def __init__(self, master=None, default_color=None, hover_color=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_color = default_color
        self.hover_color = hover_color
        self.configure(text_color=default_color)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        if self.hover_color:
            self.configure(text_color=self.hover_color)

    def on_leave(self, event=None):
        self.configure(text_color=self.default_color)
