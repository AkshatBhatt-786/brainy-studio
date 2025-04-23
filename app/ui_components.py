import customtkinter as ctk

class Colors:

    PRIMARY = "#121826"  
    SECONDARY = "#1F2937"  
    ACCENT = "#6366F1" 
    HIGHLIGHT = "#22D3EE"  
    SUCCESS = "#4CAF50" 
    WARNING = "#FACC15"  
    DANGER = "#F87171"
    BACKGROUND = "#0F172A" 
    
    class Texts:
        HEADERS = "#E2E8F0"  
        FIELDS = "#CBD5E1"  
        PLACEHOLDER = "#94A3B8"  
        BORDER = "#475569" 
        SUCCESS = "#C8E6C9" 
        MUTED = "#6c757d"

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
        SUCCESS_HOVER = "#388E3C"
        SUCCESS_BORDER = "#2E7D32"
    
    class Inputs:
        BACKGROUND = "#1F2937"
        BORDER = "#334155"
        TEXT = "#E2E8F0"
        PLACEHOLDER = "#94A3B8"
    
    class Cards:
        BACKGROUND = "#1E293B"
        BORDER = "#334155"
        SECONDARY = "#2D3748"
    
    class Footer:
        BACKGROUND = "#0F172A"
        TEXT = "#94A3B8"
    
    class Modals:
        BACKGROUND = "#1E293B"
        BORDER = "#334155"
    
    class Radio:
        BACKGROUND = "#2B2B2B"       
        PRIMARY = "#4A90E2"            
        SECONDARY = "#6C757D"         
        HOVER = "#357ABD"            
        ACTIVE = "#2D6DB4"           
        BORDER = "#3D3D3D"            
        TEXT = "#F8F9FA"         
        DISABLED = "#495057"           
        CHECKMARK = "#FFFFFF"        
        GLOW = "rgba(74, 144, 226, 0.2)"

    class Special:
        ERROR_TEXT = "#FF6B57"
        HEADER_ACCENT = "#357ABD"
        HIGHLIGHT_TEXT = "#38BDF8"
        BULLET_POINTS = "#357ABD"
        FOOTER_TEXT = "#7f8c8d" 


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
            font=("DejaVuSansCondensed-Bold", 14, "bold"),
            cursor="hand2",
            **kwargs
        )

class ErrorButton(ctk.CTkButton):
    def __init__(self, master, text, width=200, height=50, **kwargs):
        super().__init__(master, text=text, width=width, height=height,
                         fg_color=Colors.DANGER, border_color="#E74C3C", corner_radius=8, text_color="white", font=("DejaVuSansCondensed-Bold", 14, "bold"),
                         border_width=2, hover_color="#FFC080", cursor="hand2", **kwargs)


class IconButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master, width=20, height=20,
            cursor="hand2", fg_color="transparent",
            text_color=Colors.Texts.BORDER,
            hover_color=Colors.SECONDARY,
            corner_radius=18,
            text="", **kwargs)
        
class SidebarButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        super().__init__(master,
            hover_color=Colors.PRIMARY,
            fg_color=Colors.PRIMARY,
            width=20, corner_radius=12, height=38,
            text_color=Colors.Texts.BORDER,
            font=("DejaVuSansCondensed-Bold", 14, "bold"),
            cursor="hand2", **kwargs)

class LinkButton(ctk.CTkButton):

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(
            fg_color="#1E293B",
            hover_color="#1E293B",
            width=35, height=35,
            text_color="#FFFFFF",
            cursor="hand2",
            font=("DejaVuSansCondensed-Bold", 14, "bold")
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, event):
        self.configure(text_color="#A2DFF7")
    
    def on_leave(self, event):
        self.configure(text_color="#FFFFFF")

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
            font=("DejaVuSansCondensed-Bold", 14, "bold"),
            **kwargs
        )
