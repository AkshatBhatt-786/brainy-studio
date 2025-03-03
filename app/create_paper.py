import customtkinter as ctk
import tkinter as tk
from ui_components import PrimaryButton, SearchButton, ErrorButton, Colors
from question_bank import QuestionBank
from tkinter import filedialog, messagebox
from utils import getPath, centerWindow
from PIL import Image
import json
import os
import random
import string
import base64
import threading
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag


class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, mode="encrypt"):
        super().__init__(parent)
        self.attributes("-topmost", True)
        if mode == "encrypt":
            title_text = "Set a 4-digit passcode to secure your question paper."
        else:
            title_text = "Enter the 4-digit passcode to access your question paper."

        self.title("Set Passcode" if mode == "encrypt" else "Enter Passcode")
        self.geometry(centerWindow(parent, 560, 400, self._get_window_scaling()))
        self.resizable(False, False)
        self.configure(fg_color=Colors.BACKGROUND)

        self.password = None
        
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(padx=20, pady=15, fill="both", expand=True)

        self.logo = ctk.CTkLabel(
                    master=container,
                    text="Brainy Studio",
                    image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\logo.png")), size=(80, 80)),
                    font=("Consolas", 14, "bold"),
                    compound="top",
                    text_color=Colors.HIGHLIGHT
                )
        self.logo.pack(pady=(0, 10))

        self.label = ctk.CTkLabel(container, text=title_text, 
                                  font=("Segoe UI", 14),
                                  text_color=Colors.Texts.HEADERS)
        self.label.pack(pady=(0, 15))

        self.input_frame = ctk.CTkFrame(container, fg_color="transparent")
        self.input_frame.pack(pady=5)

        self.digit_entries = []
        for i in range(4):
            entry = ctk.CTkEntry(self.input_frame,
                                 width=50, height=50,
                                 fg_color=Colors.SECONDARY,
                                 border_color=Colors.Texts.BORDER,
                                 text_color=Colors.Texts.HEADERS,
                                 font=("Segoe UI", 18),
                                 justify="center")
            entry.pack(side="left", padx=5)
            entry.bind("<KeyRelease>", lambda e, idx=i: self.validate_input(e, idx))
            self.digit_entries.append(entry)

        self.confirm_btn = ctk.CTkButton(container, text="Confirm",
                                         command=self.on_confirm,
                                         width=120, height=40,
                                         fg_color=Colors.Buttons.PRIMARY,
                                         hover_color=Colors.Buttons.PRIMARY_HOVER,
                                         font=("Segoe UI", 12, "bold"),
                                         text_color="white",
                                         state="disabled")
        self.confirm_btn.pack(pady=(20, 0))

        self.grab_set()

        self.after(100, lambda: self.digit_entries[0].focus_set())

    def validate_input(self, event, idx):
        if event.char.isdigit():
            self.digit_entries[idx].delete(0, "end")
            self.digit_entries[idx].insert(0, event.char)
            if idx < 3:
                self.digit_entries[idx + 1].focus_set()
  
        elif event.keysym == "BackSpace":
            if not self.digit_entries[idx].get() and idx > 0:
                self.digit_entries[idx - 1].focus_set()
                self.digit_entries[idx - 1].delete(0, "end")

        passcode = "".join(entry.get() for entry in self.digit_entries)
        if len(passcode) == 4 and passcode.isdigit():
            self.confirm_btn.configure(state="normal")
        else:
            self.confirm_btn.configure(state="disabled")

    def on_confirm(self):
        self.password = "".join(entry.get() for entry in self.digit_entries)
        self.destroy()

class QuestionFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=Colors.Cards.BACKGROUND, corner_radius=10, border_width=2, border_color=Colors.Cards.BORDER)
        self.delete_mode = False
        self.master = master
        self.question_id = None
        self.question_type = "MCQ"
        self.normal_border = Colors.Cards.BORDER
        self.error_border = Colors.DANGER
        self._create_widgets()
        self._add_input_validation()

    def _create_widgets(self):
        self.grid_columnconfigure(0, minsize=40, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.select_var = ctk.BooleanVar(value=False)
        self.select_checkbox = ctk.CTkCheckBox(self, variable=self.select_var, text="", fg_color=Colors.SUCCESS)
        self.select_checkbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.select_checkbox.grid_remove()

        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)

        self.meta_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.meta_frame.grid(row=0, column=0, sticky="ew")
        self.meta_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.type_combobox = ctk.CTkComboBox(self.meta_frame, values=["MCQ", "True/False", "One Word"], command=self.update_question_type, width=120, fg_color=Colors.Buttons.PRIMARY, border_color=Colors.Buttons.PRIMARY_HOVER)
        self.type_combobox.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.tag_entry = ctk.CTkEntry(self.meta_frame, placeholder_text="Tags", width=140,
                                      fg_color=Colors.Inputs.BACKGROUND, border_color=Colors.Inputs.BORDER,
                                      text_color=Colors.Inputs.TEXT, placeholder_text_color=Colors.Inputs.PLACEHOLDER)
        self.tag_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.marks_entry = ctk.CTkEntry(self.meta_frame, placeholder_text="Marks", width=80,
                                      fg_color=Colors.Inputs.BACKGROUND, border_color=Colors.Inputs.BORDER,
                                      text_color=Colors.Inputs.TEXT, placeholder_text_color=Colors.Inputs.PLACEHOLDER)
        self.marks_entry.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.question_text = ctk.CTkTextbox(self.details_frame, height=80, wrap="word",
                                      fg_color=Colors.PRIMARY, border_color=Colors.Inputs.BORDER)
        self.question_text.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.options_container = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.options_container.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        self.setup_question_type("MCQ")

    def setup_question_type(self, q_type):
        for widget in self.options_container.winfo_children():
            widget.destroy()

        if q_type == "MCQ":
            self.setup_mcq_options()
        elif q_type == "True/False":
            self.setup_truefalse_options()
        elif q_type == "One Word":
            self.setup_oneword_options()

    def setup_mcq_options(self):
        self.option_entries = []

        for i in range(4):
            entry = ctk.CTkEntry(self.options_container, 
                                 placeholder_text=f"Option {i+1}", 
                                 fg_color=Colors.Inputs.BACKGROUND, 
                                 border_color=Colors.Inputs.BORDER, 
                                 text_color=Colors.Inputs.TEXT, 
                                 placeholder_text_color=Colors.Inputs.PLACEHOLDER)
            entry.pack(padx=2, pady=2, fill="x")
            entry.bind("<KeyRelease>", lambda e: self.update_correct_answer_choices())
            self.option_entries.append(entry)

        self.correct_answer = ctk.CTkComboBox(self.options_container, 
                                              values=[],  # Initially empty
                                              fg_color=Colors.Inputs.BACKGROUND, 
                                              border_color=Colors.Inputs.BORDER, 
                                              text_color=Colors.Inputs.TEXT)
        self.correct_answer.set("Select Answer")
        self.correct_answer.pack(pady=5)

    def update_correct_answer_choices(self):
        options = [entry.get().strip() for entry in self.option_entries if entry.get().strip()]
        if not options:
            self.correct_answer.configure(values=[""])
            self.correct_answer.set("Select Answer")
        else:
            self.correct_answer.configure(values=options)
            if self.correct_answer.get() not in options:
                self.correct_answer.set("Select Answer")


    def setup_truefalse_options(self):
        self.tf_var = ctk.StringVar(value="True")
        ctk.CTkRadioButton(self.options_container, text="True", variable=self.tf_var, value="True").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(self.options_container, text="False", variable=self.tf_var, value="False").pack(anchor="w", pady=2)

    def setup_oneword_options(self):
        self.answer_entry = ctk.CTkEntry(self.options_container, placeholder_text="Correct Answer")
        self.answer_entry.pack(fill="x", pady=5)

    def _add_input_validation(self):
        self.marks_entry.configure(validate="key", validatecommand=(self.register(self._validate_marks), "%P"))
        self.question_text.bind("<KeyRelease>", lambda e: self._clear_error_highlight(self.question_text))
        self.tag_entry.bind("<KeyRelease>", lambda e: self._clear_error_highlight(self.tag_entry))
        self.marks_entry.bind("<KeyRelease>", lambda e: self._clear_error_highlight(self.marks_entry))
        self.correct_answer.bind("<<ComboboxSelected>>", lambda e: self._clear_error_highlight(self.correct_answer))
        if hasattr(self, 'answer_entry'):
            self.answer_entry.bind("<KeyRelease>", lambda e: self._clear_error_highlight(self.answer_entry))

    def _validate_marks(self, value):
        return value == "" or value.isdigit()

    def _clear_error_highlight(self, widget):
        if isinstance(widget, str): widget = self.nametowidget(widget)
        widget.configure(border_color=self.normal_border)

    def _highlight_error(self, widget):
        widget.configure(border_color=self.error_border)
        widget.focus_set()

    def validate_fields(self):
        errors = []
        question_text = self.question_text.get("1.0", "end-1c").strip()
        if not question_text:
            errors.append("Question text cannot be empty")
            self._highlight_error(self.question_text)
        
        marks = self.marks_entry.get().strip()
        if not marks:
            errors.append("Marks cannot be empty")
            self._highlight_error(self.marks_entry)
        elif not marks.isdigit():
            errors.append("Marks must be a valid number")
            self._highlight_error(self.marks_entry)

        if self.question_type == "MCQ":
            if self.correct_answer.get() == "Select Answer":
                errors.append("Please select correct answer")
                self._highlight_error(self.correct_answer)
            for i, entry in enumerate(self.option_entries):
                if not entry.get().strip():
                    errors.append(f"Option {i+1} cannot be empty")
                    self._highlight_error(entry)
        elif self.question_type == "One Word":
            answer = self.answer_entry.get().strip()
            if not answer:
                errors.append("Correct answer cannot be empty")
                self._highlight_error(self.answer_entry)
        
        if not self.tag_entry.get().strip():
            errors.append("At least one tag is required")
            self._highlight_error(self.tag_entry)
        
        return errors

    def get_data(self):
        data = {
            "id": self.question_id,
            "type": self.question_type,
            "text": self.question_text.get("1.0", "end-1c").strip(),
            "tags": self.tag_entry.get().strip(),
            "marks": self.marks_entry.get().strip(),
        }
        if self.question_type == "MCQ":
            data["options"] = [entry.get().strip() for entry in self.option_entries]
            data["correct"] = self.correct_answer.get()
        elif self.question_type == "True/False":
            data["correct"] = self.tf_var.get()
        elif self.question_type == "One Word":
            data["correct"] = self.answer_entry.get().strip()
        errors = self.validate_fields()
        return data, errors

    def update_question_type(self, choice):
        self.question_type = choice
        self.setup_question_type(choice)

    def set_delete_mode(self, mode):
        self.select_checkbox.grid() if mode else self.select_checkbox.grid_remove()

    def is_selected(self): return self.select_var.get()

class CreatePaper(ctk.CTkFrame):
    def __init__(self, master, edit_mode=False, file_path=None, parent=None):
        super().__init__(master)
        self.configure(fg_color="transparent")
        self.question_frames = []
        self.delete_mode = False
        self.current_search_query = ""
        self.file_path = file_path
        self.parent = parent
        self.edit_mode = edit_mode

        control_frame = ctk.CTkFrame(master, fg_color=Colors.SECONDARY, height=120, width=1000)
        control_frame.pack(fill="x", pady=10, padx=20)
        control_frame.pack_propagate(False)

        logo = ctk.CTkLabel(
            master=control_frame,
            text="Brainy Studio",
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\logo.png")), size=(50, 50)),
            font=("Consolas", 14, "bold"),
            compound="top",
            text_color=Colors.HIGHLIGHT
        )
        logo.pack(padx=10, pady=10, side="left")
        
        PrimaryButton(control_frame, text="Add Question", command=self.add_question, width=130, height=42).pack(side="left", padx=5)
        PrimaryButton(control_frame, text="Save Paper", command=self.save_paper, width=130, height=42).pack(side="left", padx=5)
        PrimaryButton(control_frame, text="Question Bank", command=self.open_question_bank, width=130, height=42).pack(side="left", padx=5)
        ErrorButton(control_frame, text="Delete Questions", command=self.toggle_delete_mode, width=130, height=42).pack(side="left", padx=5)

        search_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        search_frame.pack(side="right", padx=10, pady=10)
        
        self.search_input = ctk.CTkEntry(search_frame, placeholder_text="Search...", width=230, height=42,
                                         fg_color=Colors.Inputs.BACKGROUND,
                                        border_color=Colors.Inputs.BORDER,
                                        placeholder_text_color=Colors.Inputs.PLACEHOLDER)
        self.search_input.pack(side="left", padx=5, expand=True)
        self.search_input.bind("<KeyRelease>", lambda e: self.perform_search())
        # self.search_input.pack_propagate(False)
        SearchButton(search_frame, text="Search", command=self.perform_search,width=110, height=42).pack(side="left", padx=5)  

        self.workspace = ctk.CTkScrollableFrame(self, fg_color="transparent", width=800, height=600)
        self.workspace.pack(fill="both", expand=True)
        
        if self.edit_mode and self.file_path:
            self.load_paper_from_recent_projects(self.file_path)
        elif self.edit_mode:
            self.load_paper() 

    def load_paper_from_recent_projects(self, filepath):
        if os.path.exists(filepath):
            pswd = PasswordDialog(self, mode="decrypt")
            self.wait_window(pswd)

            with open(filepath, "r") as fp:
                encrypted_data = json.load(fp)

            if pswd.password:
                    decrypted_data = self._decrypt_data(encrypted_data, pswd.password)
                    if decrypted_data:
                        questions = json.loads(decrypted_data)
                        self._load_questions(questions)
                        messagebox.showinfo("Question Added", "Questions Loaded Successfully!")
                        return
            
            messagebox.showerror("Incorrect Password", "The given password is incorrect!")
            self.after(0, lambda: self.parent.redirect("home-page"))
            return
        
        messagebox.showerror("File Not Found", "The file may be deleted or moved by user!")
        self.after(0, lambda: self.parent.redirect("home-page"))


    def open_question_bank(self):
        self.parent.attributes("-topmost", False)
        QuestionBank(self.parent, parent=self)
        return
    
    def generate_question_id(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def _derive_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def _encrypt_data(self, data, password):
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        iv = os.urandom(16)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        padded_data = data + (16 - len(data) % 16) * chr(16 - len(data) % 16)
        ciphertext = encryptor.update(padded_data.encode()) + encryptor.finalize()
        
        return {
            'salt': base64.b64encode(salt).decode(),
            'iv': base64.b64encode(iv).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode()
        }

    def _decrypt_data(self, encrypted_data, password):
        try:
            salt = base64.b64decode(encrypted_data['salt'])
            iv = base64.b64decode(encrypted_data['iv'])
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            
            key = self._derive_key(password, salt)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            pad_len = plaintext[-1]
            return plaintext[:-pad_len].decode()
        except (InvalidKey, ValueError, InvalidTag):
            return None

    def add_question(self):
        qf = QuestionFrame(self.workspace)
        qf.question_id = self.generate_question_id()
        self.question_frames.append(qf)
        qf.pack(fill="x", pady=5, padx=5)
        self.perform_search()

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        for qf in self.question_frames: qf.set_delete_mode(self.delete_mode)
        if not self.delete_mode:
            for qf in self.workspace.winfo_children():
                if isinstance(qf, QuestionFrame) and qf.is_selected():
                    qf.destroy()
            self.question_frames = [child for child in self.workspace.winfo_children() if isinstance(child, QuestionFrame)]
            self.perform_search()

    def perform_search(self):
        self.current_search_query = self.search_input.get().strip().lower()
        for qf in self.workspace.winfo_children():
            if isinstance(qf, QuestionFrame):
                qf.pack_forget()
        
        for qf in self.question_frames:
            data, _ = qf.get_data()
            question_text = data['text'].lower()
            tags = data['tags'].lower()
            correct_answer = data.get('correct', '').lower()
            tag_list = [tag.strip() for tag in tags.split(',')]
            
            text_match = self.current_search_query in question_text
            tag_match = any(self.current_search_query in tag.lower() for tag in tag_list)
            answer_match = self.current_search_query in correct_answer
            
            if not self.current_search_query or text_match or tag_match or answer_match:
                qf.pack(fill="x", pady=5, padx=5)

    def save_paper(self):
        all_questions = []
        all_errors = []
        for idx, qf in enumerate(self.question_frames, 1):
            data, errors = qf.get_data()
            if errors: 
                all_errors.append(f"Question {idx}:\n" + "\n".join([f" • {e}" for e in errors]))
            elif data: 
                all_questions.append(data)

        if all_errors:
            messagebox.showerror("Validation Errors", "Cannot save:\n\n" + "\n\n".join(all_errors))
            return

        pass_dialog = PasswordDialog(self, mode="encrypt")
        self.wait_window(pass_dialog)

        if not pass_dialog.password:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".enc",
            filetypes=[("Encrypted Files", "*.enc"), ("All files", "*.*")],
            title="Save Encrypted Question Paper"
        )

        if not file_path:
            return
    
        def save_thread():
            try:
                json_data = json.dumps(all_questions, indent=4)
                encrypted_data = self._encrypt_data(json_data, pass_dialog.password)

                with open(file_path, 'w') as f:
                    json.dump(encrypted_data, f)

                self.after(0, lambda: messagebox.showinfo("Success", "Paper encrypted and saved successfully!"))
                self.after(0, lambda: self.parent.redirect("home-page"))

            except Exception as error:
                self.after(0, lambda e=error: messagebox.showerror("Error", f"Save failed:\n{str(e)}"))

        threading.Thread(target=save_thread, daemon=True).start()

    def load_paper(self):
        file_path = filedialog.askopenfilename(
                    filetypes=[("Encrypted Files", "*.enc"), ("All files", "*.*")],
                    title="Open Encrypted Question Paper")
        
        if not file_path:
            return
        
        def load_thread():
            try:
                with open(file_path, 'r') as f:
                    encrypted_data = json.load(f)
                
                self.after(0, self.handle_password, encrypted_data)
                
            except Exception as e:
                error = messagebox.askretrycancel("Error", f"Load failed:\n{str(e)}")
                if error:
                    self.after(0, self.load_paper())
        
        threading.Thread(target=load_thread, daemon=True).start()

    def handle_password(self, encrypted_data):
        pass_dialog = PasswordDialog(self, mode="decrypt")
        self.wait_window(pass_dialog)
        
        if not pass_dialog.password:
            return
        
        def decrypt_thread():
            try:
                decrypted_data = self._decrypt_data(encrypted_data, pass_dialog.password)
                if not decrypted_data:
                    raise ValueError("Invalid passcode")
                
                questions = json.loads(decrypted_data)
                self.after(0, lambda: self._load_questions(questions))
                self.after(0, lambda: messagebox.showinfo("Success", "Paper loaded successfully!"))
                
            except Exception as e:
                self.after(0, lambda e=e: messagebox.showerror("Error", f"Load failed:\n{str(e)}"))
        
        threading.Thread(target=decrypt_thread, daemon=True).start()

    def _load_questions(self, questions_data):
        for qf in self.workspace.winfo_children():
            if isinstance(qf, QuestionFrame):
                qf.destroy()
        self.question_frames = []
        
        for q_data in questions_data:
            qf = QuestionFrame(self.workspace)
            qf.question_id = q_data['id']
            
            qf.question_text.insert("1.0", q_data['text'])
            qf.tag_entry.insert(0, q_data['tags'])
            qf.marks_entry.insert(0, q_data['marks'])
            
            qf.type_combobox.set(q_data['type'])
            qf.update_question_type(q_data['type'])  
            
            if q_data['type'] == "MCQ":
                for i, option in enumerate(q_data['options']):
                    if i < 4:  # Only load first 4 options
                        qf.option_entries[i].insert(0, option)
                qf.correct_answer.set(q_data['correct'])
            elif q_data['type'] == "True/False":
                qf.tf_var.set(q_data['correct'])
            elif q_data['type'] == "One Word":
                qf.answer_entry.insert(0, q_data['correct'])
            
            qf.pack(fill="x", pady=5, padx=5)
            self.question_frames.append(qf)
        
        self.perform_search()
    
    def load_existing_paper(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    encrypted_data = json.load(f)
                
                pass_dialog = PasswordDialog(self, mode="decrypt")
                self.wait_window(pass_dialog)
                
                if pass_dialog.password:
                    decrypted_data = self._decrypt_data(encrypted_data, pass_dialog.password)
                    if decrypted_data:
                        questions = json.loads(decrypted_data)
                        self._load_questions(questions)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load paper: {str(e)}")
    
    def add_questions_from_bank(self, questions):
        valid_types = {"MCQ", "True/False", "One Word"}

        for q in questions:
            question_id, question_text, tags, marks, options, q_type, answer = q

            if q_type not in valid_types:
                messagebox.showerror("Invalid Question Type", f"Question '{question_text[:30]}...' has an invalid type: {q_type}")
                continue

            qf = QuestionFrame(self.workspace)
            qf.question_id = question_id  
            qf.question_text.insert("1.0", question_text)  
            qf.tag_entry.insert(0, tags)  
            qf.marks_entry.insert(0, marks)  

            qf.type_combobox.set(q_type)
            qf.update_question_type(q_type)

            if q_type == "MCQ":
                options_list = options.split(", ") if options else []  

                for i, opt in enumerate(options_list):
                    if i < len(qf.option_entries):
                        qf.option_entries[i].insert(0, opt) 

                qf.correct_answer.configure(values=options_list) 

                if answer.strip() in options_list:
                    qf.correct_answer.set(answer.strip())
                else:
                    qf.correct_answer.set("Select Answer")

            elif q_type == "True/False":
                qf.tf_var.set("True" if answer == "1" else "False")

            elif q_type == "One Word":
                qf.answer_entry.insert(0, answer)

            qf.pack(fill="x", pady=5, padx=5)
            self.question_frames.append(qf)

        self.perform_search()
        