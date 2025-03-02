import customtkinter as ctk
from ui_components import Colors, PrimaryButton, SearchButton, ErrorButton
from PIL import Image
from utils import getPath

class QuestionFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            fg_color=Colors.Cards.BACKGROUND,
            corner_radius=10,
            border_width=2,
            border_color=Colors.Cards.BORDER
        )
        self.delete_mode = False

        self.grid_columnconfigure(0, minsize=40, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.select_var = ctk.BooleanVar(value=False)
        self.select_checkbox = ctk.CTkCheckBox(
            self, variable=self.select_var, text=""
        )
        self.select_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.select_checkbox.grid_remove() 
  
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)

        self.question_text = ctk.CTkTextbox(
            self.details_frame,
            height=80,
            fg_color=Colors.PRIMARY,
            text_color=Colors.Inputs.TEXT,
        )
        self.question_text.grid(row=0, column=0, padx=5, pady=(5,10), sticky="ew")

        self.options_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.options_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(1, weight=1)

        left_container = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        left_container.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        options_label = ctk.CTkLabel(
            left_container,
            text="Options:",
            text_color=Colors.Texts.HEADERS,
            font=("Arial", 12, "bold")
        )
        options_label.pack(anchor="w", padx=2, pady=(2,4))
        self.option_entries = []
        for i in range(4):
            entry = ctk.CTkEntry(
                left_container,
                placeholder_text=f"Option {i+1}",
                fg_color=Colors.Inputs.BACKGROUND,
                text_color=Colors.Inputs.TEXT,
                placeholder_text_color=Colors.Inputs.PLACEHOLDER
            )
            entry.pack(padx=2, pady=2, fill="x")
            self.option_entries.append(entry)

        right_container = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        right_container.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        right_container.grid_columnconfigure(0, weight=1)

    
        tags_label = ctk.CTkLabel(
            right_container,
            text="Tags:",
            text_color=Colors.Texts.HEADERS,
            font=("Arial", 12, "bold")
        )
        tags_label.grid(row=0, column=0, sticky="w", padx=5, pady=(2,2))
        self.tag_entry = ctk.CTkEntry(
            right_container,
            placeholder_text="Enter tags",
            fg_color=Colors.Inputs.BACKGROUND,
            text_color=Colors.Inputs.TEXT,
            placeholder_text_color=Colors.Inputs.PLACEHOLDER
        )
        self.tag_entry.grid(row=1, column=0, padx=5, pady=(0,5), sticky="ew")

        marks_label = ctk.CTkLabel(
            right_container,
            text="Marks:",
            text_color=Colors.Texts.HEADERS,
            font=("Arial", 12, "bold")
        )
        marks_label.grid(row=2, column=0, sticky="w", padx=5, pady=(2,2))
        self.marks_entry = ctk.CTkEntry(
            right_container,
            placeholder_text="Enter marks",
            fg_color=Colors.Inputs.BACKGROUND,
            text_color=Colors.Inputs.TEXT,
            placeholder_text_color=Colors.Inputs.PLACEHOLDER,
            width=40
        )
        self.marks_entry.grid(row=3, column=0, padx=5, pady=(0,5), sticky="ew")

        correct_label = ctk.CTkLabel(
            right_container,
            text="Correct Option:",
            text_color=Colors.Texts.HEADERS,
            font=("Arial", 12, "bold")
        )
        correct_label.grid(row=4, column=0, sticky="w", padx=5, pady=(2,2))
        self.correct_answer_cb = ctk.CTkComboBox(
            right_container,
            values=["Option 1", "Option 2", "Option 3", "Option 4"],
            dropdown_text_color=Colors.HIGHLIGHT,
            fg_color=Colors.Inputs.BACKGROUND,
            button_color=Colors.ACCENT,
            width=120
        )
        self.correct_answer_cb.grid(row=5, column=0, padx=5, pady=(0,5), sticky="ew")
        self.correct_answer_cb.set("Select Answer")

    def set_delete_mode(self, mode: bool):
        self.delete_mode = mode
        if mode:
            self.select_checkbox.grid()
        else:
            self.select_checkbox.grid_remove() 

    def is_selected(self):
        return self.select_var.get()


class CreatePaper(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master)
        self.configure(fg_color="transparent")
        master.sidebar.lift()

        self.question_frames = []

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(padx=20, pady=20, fill="both", expand=True)

        self.container.grid_columnconfigure(0, minsize=200, weight=0)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_columnconfigure(2, minsize=100, weight=0)

        self.container.grid_rowconfigure(0, weight=0)
        self.container.grid_rowconfigure(1, weight=1)

        self.user_panel = ctk.CTkFrame(
            self.container,
            height=200,
            fg_color="transparent",
            border_width=2,
            border_color=Colors.Texts.BORDER
        )
        self.user_panel.grid(row=0, column=1, padx=10, pady=(10,5), sticky="ew")
        self.user_panel.grid_columnconfigure((0,1,2,3), weight=1, minsize=100)

        self.add_question_btn = PrimaryButton(
            self.user_panel, text="Add Questions", height=32, width=120, command=self.add_question
        )
        self.add_question_btn.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.question_bank_btn = PrimaryButton(
            self.user_panel, text="Question Bank", height=32, width=120
        )
        self.question_bank_btn.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.delete_questions = ErrorButton(
            self.user_panel, text="Delete Questions", height=32, width=120, command=self.toggle_delete_mode
        )
        self.delete_questions.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        self.delete_questions.configure(state="disabled")

        self.search_input = ctk.CTkEntry(
            self.user_panel,
            placeholder_text="Search...",
            width=220,
            height=32,
            fg_color=Colors.Inputs.BACKGROUND,
            text_color=Colors.Inputs.TEXT,
            placeholder_text_color=Colors.Inputs.PLACEHOLDER
        )
        self.search_input.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        self.search_btn = SearchButton(
            self.user_panel, text="Search", height=32, width=120
        )
        self.search_btn.grid(row=0, column=4, padx=10, pady=10, sticky="ew")

        self.workspace_frame = ctk.CTkScrollableFrame(
            self.container,
            width=1050,
            height=600,
            fg_color="transparent",
            border_width=2,
            border_color=Colors.Cards.BORDER
        )
        self.workspace_frame.grid(row=1, column=1, padx=10, pady=(5,10), sticky="nsew")
        self.workspace_frame.grid_columnconfigure(0, weight=1)

        self.placeholder_label = ctk.CTkLabel(
            self.workspace_frame,
            text="No questions added yet.\nUse 'Add Questions' or explore the 'Question Bank' to get started.",
            font=("Arial", 18, "italic"),
            text_color=Colors.Texts.FIELDS
        )
        self.placeholder_label.pack(expand=True)

        self.delete_mode = False


    def add_question(self):
        if self.placeholder_label.winfo_exists():
            self.placeholder_label.destroy()
        qf = QuestionFrame(self.workspace_frame)
        qf.pack(padx=10, pady=10, fill="x", expand=True)
        self.question_frames.append(qf)
        self.delete_questions.configure(state="normal")


    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            for qf in self.question_frames:
                qf.set_delete_mode(True)
            self.delete_questions.configure(text="Confirm Delete")
        else:
            to_delete = [qf for qf in self.question_frames if qf.is_selected()]
            for qf in to_delete:
                qf.destroy()
                self.question_frames.remove(qf)
            for qf in self.question_frames:
                qf.set_delete_mode(False)
            self.delete_questions.configure(text="Delete Questions")
            if not self.question_frames:
                self.delete_questions.configure(state="disabled")
                self.placeholder_label = ctk.CTkLabel(
                    self.workspace_frame,
                    text="No questions added yet.\nUse 'Add Questions' or explore the 'Question Bank' to get started.",
                    font=("Arial", 18, "italic"),
                    text_color=Colors.Texts.FIELDS
                )
                self.placeholder_label.pack(expand=True)
