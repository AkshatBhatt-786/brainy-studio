import sqlite3
import customtkinter as ctk
from tkinter import ttk, messagebox
from utils import getPath, centerWindow
from ui_components import PrimaryButton, ErrorButton, SearchButton, Colors
import sys

class SubjectDBManager:
    def __init__(self):
        self.db_path = getPath(r"database\brainy-studio.db")

    def get_subject_name(self, subject_code):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT subject_name FROM subjects WHERE subject_code = ?", (subject_code, ))
        results = cursor.fetchone()
        conn.close()
        return results
    
    def get_instructions(self, subject_code):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT instructions FROM subjects WHERE subject_code = ?", (subject_code, ))
        results = cursor.fetchone()
        conn.close()
        return results[0]


    def fetch_data(self, search_query=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM subjects WHERE subject_name LIKE ?", (f"%{search_query}%",))
        else:
            cursor.execute("SELECT subject_code, subject_name FROM subjects")
        results = cursor.fetchall()
        conn.close()
        return results

    def add_subject(self, subject_code, subject_name, instructions):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''INSERT INTO subjects (subject_code, subject_name, instructions) VALUES (?, ?, ?)''',
                           (subject_code, subject_name, instructions))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            cursor.close()
            conn.close()

    def delete_subject(self, subject_code):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM subjects WHERE subject_code = ?", (subject_code,))
        conn.commit()
        conn.close()

class SubjectManagerUI(ctk.CTkToplevel):
    def __init__(self, parent, frame):
        super().__init__(parent)
        self.db_manager = SubjectDBManager()
        self.title("Subject Database Manager")
        try:
            if sys.platform.startswith("win"):
                self.after(200, lambda: self.iconbitmap(getPath("assets\\icons\\icon.ico")))
        except Exception:
            pass
        self.geometry(centerWindow(parent, 900, 550, parent._get_window_scaling()))
        self.configure(fg_color=Colors.BACKGROUND)
        self.parent_frame = frame

        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        title_label = ctk.CTkLabel(self, text="Subject Manager", font=("Arial", 18, "bold"), text_color=Colors.Texts.HEADERS)
        title_label.pack(pady=10)

        search_frame = ctk.CTkFrame(self, fg_color=Colors.PRIMARY)
        search_frame.pack(fill='x', padx=10, pady=5)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search Subject...", fg_color=Colors.Inputs.BACKGROUND, text_color=Colors.Inputs.TEXT)
        self.search_entry.pack(side='left', padx=10, expand=True, fill='x')
        
        search_button = SearchButton(search_frame, text="Search", command=self.search_subjects)
        search_button.pack(side='right', padx=10)

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
        
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E293B", corner_radius=10)
        self.scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        tree_frame = ctk.CTkFrame(self.scroll_frame)
        tree_frame.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.tree = ttk.Treeview(tree_frame, columns=("Code", "Name", "Instructions"), show="headings")
        self.tree.heading("Code", text="Subject Code")
        self.tree.heading("Name", text="Subject Name")
        self.tree.pack(fill='both', expand=True, padx=10, pady=5)
        
        button_frame = ctk.CTkFrame(self, fg_color=Colors.PRIMARY)
        button_frame.pack(pady=10)
        
        self.add_button = PrimaryButton(button_frame, text="Add Subject", command=self.open_add_window)
        self.add_button.pack(side='left', padx=5)
        
        self.delete_button = ErrorButton(button_frame, text="Delete Subject", command=self.delete_selected)
        self.delete_button.pack(side='left', padx=5)

    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.db_manager.fetch_data():
            self.tree.insert("", "end", values=row)
    
    def search_subjects(self):
        query = self.search_entry.get()
        self.tree.delete(*self.tree.get_children())
        for row in self.db_manager.fetch_data(query):
            self.tree.insert("", "end", values=row)
    
    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No subject selected!")
            return
        
        subject_code = self.tree.item(selected_item, "values")[0]
        self.db_manager.delete_subject(subject_code)
        self.load_data()
        self.parent_frame.get_subject_codes()
        messagebox.showinfo("Success", "Subject deleted successfully!")
    
    def open_add_window(self):
        add_window = ctk.CTkToplevel(self)
        add_window.title("Add Subject to Database")
        add_window.geometry(centerWindow(self, 420, 300, self._get_window_scaling()))
        add_window.configure(bg=Colors.Modals.BACKGROUND)
        add_window.transient(self)
        add_window.grab_set()

        add_window.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(add_window, text="Subject Code", text_color=Colors.Texts.HEADERS).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        subject_code_entry = ctk.CTkEntry(add_window, fg_color=Colors.Inputs.BACKGROUND, text_color=Colors.Inputs.TEXT)
        subject_code_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(add_window, text="Subject Name", text_color=Colors.Texts.HEADERS).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        subject_name_entry = ctk.CTkEntry(add_window, fg_color=Colors.Inputs.BACKGROUND, text_color=Colors.Inputs.TEXT)
        subject_name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(add_window, text="Instructions", text_color=Colors.Texts.HEADERS).grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        instructions_entry = ctk.CTkTextbox(add_window, height=100, fg_color=Colors.Inputs.BACKGROUND, text_color=Colors.Inputs.TEXT)
        instructions_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        def validate_code():
            code = subject_code_entry.get()
            if not code.isdigit() or len(code) != 7:
                messagebox.showwarning("Warning", "Subject Code must be exactly 6 digits!")
                return False
            return True

        def add_subject():
            if not validate_code():
                return

            code = subject_code_entry.get()
            name = subject_name_entry.get().upper()
            instructions = instructions_entry.get("1.0", "end").strip()

            if not code or not name:
                messagebox.showwarning("Warning", "Subject Code and Name are required!")
                return

            if self.db_manager.add_subject(code, name, instructions):
                messagebox.showinfo("Success", "Subject added successfully!")
                self.parent_frame.get_subject_codes()
                add_window.destroy()
                self.load_data()
            else:
                messagebox.showerror("Error", "Subject code already exists!")

        PrimaryButton(add_window, text="Add", command=add_subject).grid(row=3, column=0, columnspan=2, pady=10)