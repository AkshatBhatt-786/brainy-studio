# ==========================================================
#  * Project : Brainy Studio - Question Paper Generator
#  * Author  : Bhatt Akshat S
#  * Updated : 04-03-2025
#  * Version : 1.0.2
#  * License : MIT License
#  * GitHub  : https://github.com/AkshatBhatt-786/brainy-studio/tree/main/app/ui_components.py
#  * Description:
#       This script handles the Colors, Themes and UI components
#  ^ Credits | References:
#  & Stack Overflow (https://stackoverflow.com/q/1234567)
#  & Python Docs (https://docs.python.org/3/library/)
#  & CustomTkinter Docs (https://customtkinter.tomschimansky.com/)
# ==========================================================


import customtkinter as ctk


class Colors:

    PRIMARY = "#121826"  
    SECONDARY = "#1F2937"  
    ACCENT = "#6366F1" 
    HIGHLIGHT = "#22D3EE"  
    SUCCESS = "#4ADE80" 
    WARNING = "#FACC15"  
    DANGER = "#F87171"
    BACKGROUND = "#0F172A" 
    
    class Texts:
        HEADERS = "#E2E8F0"  
        FIELDS = "#CBD5E1"  
        PLACEHOLDER = "#94A3B8"  
        BORDER = "#475569"  

    class Sidebar:
        BACKGROUND = "#1E293B"
        BORDER = "#334155"
        HOVER = "#4B5563" 

    class Buttons:
        PRIMARY = "#6366F1"  
        PRIMARY_HOVER = "#818CF8"  
        SECONDARY = "#10B981"  
        SECONDARY_HOVER = "#34D399"
        DISABLED = "#64748B"
    
    class Inputs:
        BACKGROUND = "#1F2937"
        BORDER = "#334155"
        TEXT = "#E2E8F0"
        PLACEHOLDER = "#94A3B8"
    
    class Cards:
        BACKGROUND = "#1E293B"
        BORDER = "#334155"
    
    class Footer:
        BACKGROUND = "#0F172A"
        TEXT = "#94A3B8"
    
    class Modals:
        BACKGROUND = "#1E293B"
        BORDER = "#334155"


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text, width=200, height=50, **kwargs):
        super().__init__(
            master,
            text=text,
            width=width,
            height=height,
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER,
            border_color=Colors.Buttons.PRIMARY, # 303F9F
            corner_radius=12,
            text_color="white",
            border_width=2,
            cursor="hand2",
            **kwargs
        )

class ErrorButton(ctk.CTkButton):
    def __init__(self, master, text, width=200, height=50, **kwargs):
        super().__init__(master, text=text, width=width, height=height,
                         fg_color=Colors.DANGER, border_color="#E74C3C", corner_radius=8, text_color="white", 
                         border_width=2, hover_color="#FFC080", cursor="hand2", **kwargs)


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
    def __init__(self, master, text, **kwargs):
        super().__init__(
            master,
            text=text,
            fg_color=Colors.Sidebar.BACKGROUND,
            hover_color=Colors.Sidebar.HOVER,
            corner_radius=10,
            width=180,
            height=40,
            text_color=Colors.Texts.HEADERS,
            cursor="hand2",
            font=("Inter", 14, "bold"),
            **kwargs
        )

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

class SearchButton(ctk.CTkButton):
    def __init__(self, master, text, width=130, height=50, **kwargs):
        super().__init__(
            master,
            text=text,
            width=width,
            height=height,
            fg_color="#FF9800",
            border_color="#FF9800",
            corner_radius=12,
            text_color="white",
            border_width=2,
            hover_color="#F57C00",
            cursor="hand2",
            **kwargs
        )
