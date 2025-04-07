import customtkinter as ctk
import pyperclip
import re
from utils import centerWindow,getPath
from PIL import Image
import sys
import json

class Colors:
    PRIMARY = "#0F172A"
    SECONDARY = "#1E293B"
    ACCENT = "#7C3AED"
    HIGHLIGHT = "#0EA5E9"
    TEXT = "#F8FAFC"
    SUBTEXT = "#94A3B8"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    CARD = "#1E293B"
    BORDER = "#334155"


# Unicode mappings
sup_map = str.maketrans("0123456789+-=()nexyz", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿᴇˣʸᶻ")
# sub_map = str.maketrans(
#     "0123456789+-=()exnkrstuhvlampoi",
#     "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₑₓₙₖᵣₛₜᵤₕᵥₗₐₘₚₒᵢ"
# )
sub_map = str.maketrans(
    "0123456789+-=()abcdefghijklmnopqrstuvwxyz",
    "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐᵦ𝒸𝒹ₑ𝒻𝓰ₕᵢⱼₖₗₘₙₒₚ𝓺ᵣₛₜᵤᵥ𝓌ₓᵧ𝓏"
)



fractions = {
    r"\b1/4\b": "¼", r"\b1/2\b": "½", r"\b3/4\b": "¾",
    r"\b1/3\b": "⅓", r"\b2/3\b": "⅔", r"\b1/5\b": "⅕",
    r"\b2/5\b": "⅖", r"\b3/5\b": "⅗", r"\b4/5\b": "⅘",
    r"\b1/6\b": "⅙", r"\b5/6\b": "⅚", r"\b1/8\b": "⅛",
    r"\b3/8\b": "⅜", r"\b5/8\b": "⅝", r"\b7/8\b": "⅞"
}

try:
    FILEPATH = getPath(r"database\extras.json")
    with open(FILEPATH, "r", encoding="utf-8") as f:
        extra_symbols = json.load(f)["symbols"]
    

except Exception as e:
    extra_symbols = {}

symbols = {
    "int": "∫",
    "sqrt": "√",
    "pi": "π",
    "theta": "θ",
    "alpha": "α",
    "beta": "β",
    "delta": "Δ",
    "infinity": "∞",
    "sum": "∑",
    "d/dx": "∂/∂x",
    "->": "→",
    "~=": "≈",
    "!=" : "≠",
    "<=" : "≤",
    ">=" : "≥",
    "+-" : "±",
    "therefore": "∴",
    "e^x": "ᴇˣ",
    "ln": "𝔬",
    "log": "log"
}
symbols.update(extra_symbols)


class CodexFormatter(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.parent = master
        self.title("Codex Formatter")
        self.attributes("-topmost", True)
        try:
            if sys.platform.startswith("win"):
                self.after(200, lambda: self.iconbitmap(getPath("assets\\icons\\icon.ico")))
        except Exception:
            pass
        self.geometry(centerWindow(self.parent, 800, 700, self.parent._get_window_scaling(), (0, 50)))
        self.configure(fg_color=Colors.PRIMARY)
        self._create_widgets()
        self._position_widgets()

    def _create_widgets(self):
        self.title_label = ctk.CTkLabel(self, text="Codex Formatter", font=("Arial", 24, "bold"), text_color=Colors.TEXT)
        self.input_entry = ctk.CTkEntry(self, placeholder_text="Enter math expression (e.g., x^2 + 3_1 → ∞)", width=680, height=50, font=("Consolas", 18), fg_color=Colors.SECONDARY, border_color=Colors.BORDER, text_color=Colors.TEXT)
        self.output_entry = ctk.CTkEntry(self, placeholder_text="Formatted output will appear here", width=680, height=50, font=("Consolas", 18), fg_color=Colors.SECONDARY, border_color=Colors.BORDER, text_color=Colors.TEXT)
        self.format_btn = ctk.CTkButton(self, text="Format Expression", command=self.format_expression, fg_color=Colors.ACCENT, hover_color=Colors.HIGHLIGHT, font=("Arial", 14, "bold"), height=40)
        self.copy_btn = ctk.CTkButton(self, text="Copy to Clipboard", command=self.copy_to_clipboard, fg_color=Colors.SUCCESS, hover_color="#059669", font=("Arial", 14), height=40)
        self.extras_btn = ctk.CTkButton(
            self, text="View Extra Symbols", command=self.show_extra_symbols,
            fg_color=Colors.WARNING, hover_color="#D97706", font=("Arial", 14), height=40
        )

        self.symbol_frame = ctk.CTkFrame(self, fg_color=Colors.CARD, border_color=Colors.BORDER, border_width=2)
        self._create_symbol_buttons()

    def _position_widgets(self):
        self.title_label.pack(pady=20)
        self.input_entry.pack(pady=10)
        self.output_entry.pack(pady=10)
        self.format_btn.pack(padx=10, pady=5)
        self.copy_btn.pack(padx=10, pady=5)
        self.extras_btn.pack(padx=10, pady=5)
        self.symbol_frame.pack(pady=20, padx=20, fill="both", expand=True)

    def _create_symbol_buttons(self):
        categories = {
            "Greek Letters": ["π", "θ", "α", "β", "Δ"],
            "Operators": ["∫", "√", "∂/∂x", "∑", "eˣ"],
            "Relations": ["→", "≈", "≠", "≤", "≥"],
            "Constants": ["∞", "±", "∴"]
        }

        for col, (title, syms) in enumerate(categories.items()):
            frame = ctk.CTkFrame(self.symbol_frame, fg_color="transparent")
            frame.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
            ctk.CTkLabel(frame, text=title, font=("Arial", 12, "bold"), text_color=Colors.SUBTEXT).pack(pady=5)

            for sym in syms:
                btn = ctk.CTkButton(
                    frame, text=sym, width=60,
                    command=lambda s=sym: self.insert_symbol(s),
                    fg_color=Colors.SECONDARY,
                    hover_color=Colors.ACCENT,
                    font=("Arial", 14)
                )
                btn.pack(pady=2)

        self.symbol_frame.grid_columnconfigure((0,1,2,3), weight=1)

    def insert_symbol(self, symbol):
        current = self.input_entry.get()
        pos = self.input_entry.index(ctk.INSERT)
        self.input_entry.delete(0, ctk.END)
        self.input_entry.insert(0, current[:pos] + symbol + current[pos:])
        self.input_entry.focus_set()

    def format_expression(self):
        text = self.input_entry.get()

        # Handle fractions
        for pattern, replacement in fractions.items():
            text = re.sub(pattern, replacement, text)

        # Handle predefined keywords
        escaped_keys = [re.escape(k) for k in symbols.keys()]
        text = re.sub(r"\b(" + "|".join(escaped_keys) + r")\b", lambda m: symbols[m.group(0)], text)

        # Normalize spacing like 'sqrt (x)' → 'sqrt(x)'
        text = re.sub(r"(sqrt|int|sum|log)\s+\(", lambda m: m.group(1) + "(", text)

        # Superscripts (e.g. ^2, ^(x+1))
        text = re.sub(r"\^(\([^\)]+\)|\w+)", lambda m: format_super(m.group(1).strip("()")), text)

        # Subscripts (e.g. _2, _(12))
        text = re.sub(r"_(\([^\)]+\)|\w+)", lambda m: format_sub(m.group(1).strip("()")), text)

        # Chemistry-style element+number (e.g., CO2 → CO₂)
        text = re.sub(r"([A-Za-z]{1,2})(\d+)", lambda m: m.group(1) + format_sub(m.group(2)), text)

        # Handle log base e
        text = re.sub(r"log_?e\((.*?)\)", r"ln(\1)", text)

        text = re.sub(
            r"(\w|\))\^(\(?-?\w+\)?)",
            lambda m: m.group(1) + format_super(m.group(2).strip("()")),
            text
        )

        # Handle derivatives like d/dx
        text = re.sub(r"d/d([a-zA-Z])", r"∂/∂\1", text)

        # Limits like lim{x->0}
        # text = re.sub(r"lim_?\{?([a-zA-Z]+)->([^}]+)\}?", lambda m: f"lim{m.group(1).translate(sub_map)}→{m.group(2).translate(sub_map)}", text)
        text = re.sub(
    r"lim_?\{?\s*([a-zA-Z])\s*->\s*([^\}\s]+)\s*\}?",
    lambda m: f"limit({format_sub(m.group(1))}→{format_sub(m.group(2))})",
    text
)

        text = re.sub(
            r"matrix\(\(([^()]+)\),\(([^()]+)\)\)",
            lambda m: f"⎡{m.group(1)}⎤\n⎣{m.group(2)}⎦",
            text
        )

        # Handle determinant pattern: det((1,2),(3,4))
        text = re.sub(
            r"det\(\(([^()]+)\),\(([^()]+)\)\)",
            lambda m: f"|{m.group(1)}|\n|{m.group(2)}|",
            text
        )


        self.output_entry.delete(0, ctk.END)
        self.output_entry.insert(0, text)

    def format_super_expression(self, text):
        return text.translate(sup_map).replace(" ", "")
    
    def on_close(self):
        if self.parent is not None:
            self.parent.attributes("-topmost", True)
            self.destroy()

    def show_extra_symbols(self):
        window = ctk.CTkToplevel(self)
        window.title("Symbol Library")
        self.attributes("-topmost", False)
        window.attributes("-topmost", True)
        window.geometry(centerWindow(self, 680, 500, self._get_window_scaling()))
        window.configure(fg_color=Colors.PRIMARY)
        window.protocol("WM_DELETE_WINDOW", self.on_close)


        # Category definitions
        categories = {
            "Mathematical": ["∞", "±", "∴", "∵", "∅", "∈", "∉", "∏", "∐", "∫", "∮", "√", "∛", "∜"],
            "Greek Letters": ["α", "β", "γ", "δ", "ε", "ζ", "η", "θ", "λ", "μ", "π", "ρ", "σ", "τ", "φ", "ω", "Δ", "Σ", "Ω"],
            "Arrows": ["→", "←", "↑", "↓", "↔", "⇒", "⇐", "⇔", "↦", "↔", "↵", "⇌", "⇋"],
            "Operators": ["⊕", "⊗", "⊥", "∥", "∠", "∡", "∦", "≈", "≠", "≡", "≢", "≤", "≥", "≪", "≫", "∝", "≅"],
            "Chemistry": ["↑", "↓", "⇌", "⇋", "°C", "Å", "⏦", "⚛", "⚗", "☢", "☣"],
            "Special Symbols": ["ℕ", "ℤ", "ℚ", "ℝ", "ℂ", "ℍ", "ℵ", "ℶ", "§", "¶", "†", "‡", "•", "◊", "★", "☆"],
            "extras": [symbol for symbol in extra_symbols.items()]
        }

        main_frame = ctk.CTkFrame(window, fg_color=Colors.PRIMARY)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Search bar
        search_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Search symbols...",
            width=400, fg_color=Colors.SECONDARY,
            border_color=Colors.BORDER, text_color=Colors.TEXT
        )
        search_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            search_frame, text="Clear", width=80,
            fg_color=Colors.WARNING, hover_color="#D97706",
            command=lambda: search_entry.delete(0, "end")
        ).pack(side="left")

        # Scrollable area
        scroll_frame = ctk.CTkScrollableFrame(
            main_frame, fg_color=Colors.SECONDARY,
            scrollbar_button_color=Colors.ACCENT,
            scrollbar_button_hover_color=Colors.HIGHLIGHT
        )
        scroll_frame.pack(fill="both", expand=True)

        # category sections
        for cat_name, symbols in categories.items():
            cat_frame = ctk.CTkFrame(scroll_frame, fg_color=Colors.CARD)
            cat_frame.pack(fill="x", pady=8, padx=5)

            # Category header
            ctk.CTkLabel(
                cat_frame, text=cat_name,
                font=("Arial", 14, "bold"),
                text_color=Colors.TEXT
            ).pack(anchor="w", padx=10, pady=(8, 12))

            # Symbols grid
            grid_frame = ctk.CTkFrame(cat_frame, fg_color="transparent")
            grid_frame.pack(fill="x", padx=10, pady=(0, 8))

            cols = 8
            for i, sym in enumerate(symbols):
                if i % cols == 0:
                    row_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2)

                btn = ctk.CTkButton(
                    row_frame, text=sym, width=50, height=40,
                    font=("Arial", 16), corner_radius=6,
                    fg_color=Colors.PRIMARY, hover_color=Colors.ACCENT,
                    command=lambda s=sym: self.insert_symbol_from_popup(s, window)
                )
                btn.pack(side="left", padx=2)

        # watermark
        ctk.CTkLabel(
            main_frame, text="⚡ Symbol Library v1.0",
            text_color=Colors.SUBTEXT, font=("Arial", 10)
            ).pack(side="bottom", pady=5)

    def insert_symbol_from_popup(self, symbol, popup):
        self.insert_symbol(symbol)
        popup.destroy()


    def copy_to_clipboard(self):
        pyperclip.copy(self.output_entry.get())
        self.copy_btn.configure(text="Copied! ✓")
        self.after(2000, lambda: self.copy_btn.configure(text="Copy to Clipboard"))

def format_super(text):
    return text.translate(sup_map).replace(" ", "")

def format_sub(text):
    return text.translate(sub_map).replace(" ", "")

