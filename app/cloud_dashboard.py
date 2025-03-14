import customtkinter as ctk
from ui_components import *
from utils import getPath

class CloudDashboard(ctk.CTkFrame):
    def __init__(self, master, parent):
        super().__init__(master)
        self.parent = parent
        self.configure(fg_color="#0F172A")
        self.create_widgets()
        
    def create_widgets(self):
        self.pack(padx=10, pady=10, anchor="center")
        
        # File Selection Section
        file_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        
        ctk.CTkLabel(file_frame, text="Select Encrypted Paper (.enc)", 
                    text_color=Colors.Texts.HEADERS).pack(side="left", padx=5)
        self.file_entry = ctk.CTkEntry(file_frame, width=300, 
                                     placeholder_text="Select a valid .enc file",
                                     fg_color=Colors.Inputs.BACKGROUND)
        self.file_entry.pack(side="left", padx=5, fill="x", expand=True)
        PrimaryButton(file_frame, text="Browse", width=80).pack(side="left", padx=5)
        
        # Exam Details Section
        details_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        details_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Subject and Date
        ctk.CTkLabel(details_frame, text="Subject Code:", text_color=Colors.Texts.HEADERS).grid(row=0, column=0, sticky="w")
        self.subject_entry = ctk.CTkEntry(details_frame, fg_color=Colors.Inputs.BACKGROUND)
        self.subject_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(details_frame, text="Exam Date:", text_color=Colors.Texts.HEADERS).grid(row=1, column=0, sticky="w")
        self.date_entry = ctk.CTkEntry(details_frame, fg_color=Colors.Inputs.BACKGROUND)
        self.date_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Registration Time
        self.time_button = PrimaryButton(details_frame, text="Set Registration Time")
        self.time_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Features Section
        features_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        features_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.negative_marking_var = ctk.IntVar()
        ctk.CTkCheckBox(features_frame, text="Enable Negative Marking",
                       variable=self.negative_marking_var).pack(anchor="w")
        self.negative_marks_entry = ctk.CTkEntry(features_frame, 
                                                placeholder_text="Negative marks per wrong answer",
                                                fg_color=Colors.Inputs.BACKGROUND,
                                                state="disabled")
        self.negative_marks_entry.pack(fill="x", pady=5)
        
        self.shuffle_var = ctk.IntVar()
        ctk.CTkCheckBox(features_frame, text="Shuffle Questions", variable=self.shuffle_var).pack(anchor="w")
        
        # Filename Section
        filename_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        filename_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(filename_frame, text="Cloud Filename:", text_color=Colors.Texts.HEADERS).pack(side="left", padx=5)
        self.filename_entry = ctk.CTkEntry(filename_frame, width=150, fg_color=Colors.Inputs.BACKGROUND)
        self.filename_entry.pack(side="left", padx=5)
        PrimaryButton(filename_frame, text="Generate", width=80).pack(side="left", padx=5)
        
        # Upload Button
        PrimaryButton(self, text="Upload to Cloud").grid(row=4, column=0, columnspan=2, pady=10)
        
        self.columnconfigure(0, weight=1)