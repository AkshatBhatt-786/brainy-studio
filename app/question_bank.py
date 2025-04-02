import customtkinter as ctk
from tkinter import filedialog, ttk, messagebox
from utils import centerWindow, getPath
import pandas as pd
import os
import sys


EXCEL_FILE = r"D:\github_projects\brainy-studio\app\database\question_bank.xlsx"


class QuestionBank(ctk.CTkToplevel):
    def __init__(self, master, parent=None):
        super().__init__(master=master)
        self.parent = parent
        self.attributes("-topmost", True)
        self.title("Question Bank")
        try:
            if sys.platform.startswith("win"):
                self.after(200, lambda: self.iconbitmap(getPath("assets\\icons\\icon.ico")))
        except Exception:
            pass
        self.geometry(centerWindow(master, 900, 500, self._get_window_scaling()))
        self.configure(fg_color="#0F172A")
        self.question_data = None
        self.lift()
        self.focus_force()

        self.navbar = ctk.CTkFrame(self, fg_color="#1E293B", height=50, corner_radius=10)
        self.navbar.pack(fill="x", padx=10, pady=10)

        self.search_entry = ctk.CTkEntry(self.navbar, placeholder_text="Search Questions...", width=300, fg_color="#334155", text_color="white", corner_radius=8)
        self.search_entry.pack(side="left", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self.filter_questions)

        self.sort_by = ctk.StringVar(value="Sort by")
        self.sort_combobox = ctk.CTkComboBox(self.navbar, values=["Question ID", "Tags", "Marks", "Question Type"], variable=self.sort_by, fg_color="#334155", text_color="white", button_color="#6366F1", dropdown_text_color="white", corner_radius=8, command=self.sort_questions)
        self.sort_combobox.pack(side="left", padx=10, pady=10)

        self.upload_btn = ctk.CTkButton(self.navbar, text="Import Excel", fg_color="#6366F1", hover_color="#818CF8", text_color="white", corner_radius=8, command=self.import_excel)
        self.upload_btn.pack(side="right", padx=10, pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=10)
        self.scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        style = ttk.Style()
        style.configure("Treeview",
                        background="#1E293B",
                        foreground="#FFFFFF",
                        rowheight=30,
                        fieldbackground="#1E293B")
        style.configure("Treeview.Heading",
                        background="#1E293B",
                        foreground="#333333",
                        fg_color="#1E293B",
                        font=("Arial", 14, "bold"))
        
        self.tree = ttk.Treeview(self.scroll_frame, 
                         columns=("Question ID", "Question", "Tags", "Marks", "Options", "Question Type", "Answer"), 
                         show="headings", selectmode="extended")

        self.tree.heading("Question ID", text="ID", anchor="center")
        self.tree.heading("Question", text="Question", anchor="w")
        self.tree.heading("Tags", text="Tags", anchor="center")
        self.tree.heading("Marks", text="Marks", anchor="center")
        self.tree.heading("Question Type", text="Type", anchor="center")
        self.tree.heading("Answer", text="Answer", anchor="center")
        self.tree.heading("Options", text="Options", anchor="w")


        self.tree.column("Question ID", width=120, anchor="center")
        self.tree.column("Question", width=300, anchor="w")
        self.tree.column("Tags", width=120, anchor="center")
        self.tree.column("Marks", width=80, anchor="center")
        self.tree.column("Question Type", width=100, anchor="center")
        self.tree.column("Answer", width=120, anchor="center")
        self.tree.column("Options", width=250, anchor="w")


        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.add_to_paper_btn = ctk.CTkButton(self, text="Add to Existing Paper", fg_color="#10B981", hover_color="#34D399", text_color="white", corner_radius=8, command=self.add_selected_questions)
        self.add_to_paper_btn.pack(pady=10)

        self.load_questions()

    def import_excel(self):
        self.attributes("-topmost", False)
        file_path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        self.attributes("-topmost", True)

        if file_path:
            try:
                df = pd.read_excel(file_path, engine="openpyxl")

                required_columns = {"Question ID", "Question", "Tags", "Marks", "Options", "Question Type", "Answer"}
                if not required_columns.issubset(df.columns):
                    messagebox.showerror("Invalid Format", "Invalid file format! Missing required columns.")
                    return

                output_file = EXCEL_FILE if EXCEL_FILE.endswith(".xlsx") else EXCEL_FILE + ".xlsx"

                df.to_excel(output_file, index=False, engine="openpyxl")
                self.load_questions()

            except Exception as e:
                messagebox.showerror("Something went Wrong!", f"Error loading file: {e}")

    def load_questions(self):
        if os.path.exists(EXCEL_FILE):
            try:
                self.question_data = pd.read_excel(EXCEL_FILE)
                self.display_questions()
            except Exception as e:
                messagebox.showerror("Error Occurred!", f"Error loading questions: {e}")
    
    def display_questions(self, filtered_data=None):
        self.tree.delete(*self.tree.get_children())  
        data = filtered_data if filtered_data is not None else self.question_data
    
        for _, row in data.iterrows():
            full_question = row["Question"]  
            displayed_question = (full_question[:50] + "...") if len(full_question) > 50 else full_question
    
            self.tree.insert("", "end", values=(
                row["Question ID"], full_question, row["Tags"], row["Marks"], row["Options"], row["Question Type"], row["Answer"]
            ), tags=(displayed_question,))
    
    def sort_questions(self, event=None):
        selected_sort = self.sort_by.get()
        if selected_sort in self.question_data.columns:
            self.question_data = self.question_data.sort_values(by=[selected_sort], ascending=True)
            self.display_questions()
    
    def filter_questions(self, event=None):
        query = self.search_entry.get().strip().lower()
        filtered_data = self.question_data[self.question_data.apply(lambda row: query in str(row["Question"]).lower() or query in str(row["Tags"]).lower(), axis=1)]
        self.display_questions(filtered_data)

    def add_selected_questions(self):
        selected_items = self.tree.selection()
        selected_questions = [
            (self.tree.item(item, "values")[0],  # & Question ID
             self.tree.item(item, "values")[1],  # & Question Text
             self.tree.item(item, "values")[2],  # & Tags
             int(float(self.tree.item(item, "values")[3])),  # & Marks
             self.tree.item(item, "values")[4],  # & Options
             self.tree.item(item, "values")[5],  # & Question Type
             self.tree.item(item, "values")[6])  # & Answer
            for item in selected_items
        ]

        if not selected_questions:
            messagebox.showwarning("No Selection", "Please select at least one question.")
            return

        self.parent.add_questions_from_bank(selected_questions)
        self.destroy()
