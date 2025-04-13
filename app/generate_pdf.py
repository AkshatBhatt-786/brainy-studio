import json
import base64
import sys
import os
import subprocess
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from utils import getPath
from PIL import Image
from ui_components import Colors, PrimaryButton, LinkButton
from create_paper import PasswordDialog
from pdf_template import GeneratePDF 
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag
import datetime
from subject_db import SubjectManagerUI

class GeneratePDFUI(ctk.CTkFrame):
    def __init__(self, master, subject_db, parent, container):
        super().__init__(master)
        self.parent = parent
        self.parent.title("Export to PDF")
        self.configure(fg_color="#0F172A")
        self.db_manager = subject_db
        self.detail_labels = {}
        self.parsed_questions = []
        self.logo_path = getPath(r"assets\images\logo.png")
        self.answer_checked = ctk.StringVar(value="No")
        self.main_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.valid_states = {
            'file': False,
            'subject': False,
            'title': False
        }
        
        self.create_widgets()
        self.setup_validations()
        # self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(pady=(10, 20), padx=20, fill="x")
        
        ctk.CTkLabel(
            header_frame,
            text="PDF Export",
            font=("Arial", 24, "bold"),
            text_color=Colors.Texts.HEADERS,
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\pdf.png")), 
            size=(40, 40)),
            compound="left"
        ).pack(side="left")

        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        left_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_column.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)

        file_card = ctk.CTkFrame(left_column, fg_color=Colors.Cards.SECONDARY, corner_radius=8)
        file_card.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(file_card, 
                    text="1. Select Paper File", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(anchor="w", pady=(10, 15), padx=10)
        
        file_input_frame = ctk.CTkFrame(file_card, fg_color="transparent")
        file_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.file_entry = ctk.CTkEntry(
            file_input_frame,
            placeholder_text="Select .enc file",
            fg_color=Colors.Inputs.BACKGROUND,
            border_color=Colors.Inputs.BORDER
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        PrimaryButton(
            master=file_input_frame, 
            text="Browse", 
            command=self.select_file, 
            width=100,
            height=38
        ).pack(side="left")

        subject_card = ctk.CTkFrame(left_column, fg_color=Colors.Cards.SECONDARY, corner_radius=8)
        subject_card.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(subject_card, 
                    text="2. Subject Details", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(anchor="w", pady=(10, 15), padx=10)
        
        subject_header = ctk.CTkFrame(subject_card, fg_color="transparent")
        subject_header.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(subject_header, text="Subject Code:").pack(side="left")
        LinkButton(subject_header, 
                 text="Manage Subjects", 
                 command=lambda: SubjectManagerUI(self.parent, self)).pack(side="right")
        
        self.subject_combo = ctk.CTkComboBox(
            subject_card,
            values=self.get_subject_codes(),
            fg_color=Colors.Inputs.BACKGROUND,
            border_color=Colors.Inputs.BORDER,
            button_color=Colors.Buttons.PRIMARY,
            dropdown_fg_color=Colors.Cards.SECONDARY,
            command=self.update_subject_details
        )
        self.subject_combo.set("Select Subject")
        self.subject_combo.pack(fill="x", padx=10, pady=(0, 10))

        details_card = ctk.CTkFrame(left_column, fg_color=Colors.Cards.SECONDARY, corner_radius=8)
        details_card.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(details_card, 
                    text="3. Exam Configuration", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(anchor="w", pady=(10, 15), padx=10)
        
        details_grid = ctk.CTkFrame(details_card, fg_color="transparent")
        details_grid.pack(padx=10, pady=(0, 10), fill="x")

        ctk.CTkLabel(details_grid, text="Subject Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.detail_labels['subject_name'] = ctk.CTkLabel(details_grid, text="N/A")
        self.detail_labels['subject_name'].grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    

        ctk.CTkLabel(details_grid, text="Exam Date:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.subject_date_picker = DateEntry(
            details_grid,
            date_pattern='yyyy-mm-dd',
            mindate=datetime.date.today(),
            background=Colors.Buttons.PRIMARY,
            foreground='white',
            bordercolor=Colors.Inputs.BORDER
        )
        self.subject_date_picker.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(details_grid, text="Time per Question:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        time_frame = ctk.CTkFrame(details_grid, fg_color="transparent")
        time_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        self.time_duration_slider = ctk.CTkSlider(
            time_frame,
            from_=1,
            to=10,
            number_of_steps=18,
            command=self.update_time_label,
            fg_color=Colors.Inputs.BACKGROUND,
            button_color=Colors.Buttons.PRIMARY,
            progress_color=Colors.Buttons.PRIMARY_HOVER
        )
        self.time_duration_slider.set(5.0)
        self.time_duration_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.time_duration_label = ctk.CTkLabel(
            time_frame, 
            text="5.0 min",
            width=60
        )
        self.time_duration_label.pack(side="left")

        ctk.CTkLabel(details_grid, text="Exam Title:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.exam_title_entry = ctk.CTkEntry(
            details_grid,
            placeholder_text="Enter Exam Title",
            fg_color=Colors.Inputs.BACKGROUND,
            border_color=Colors.Inputs.BORDER
        )
        self.exam_title_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        right_column = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_column.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        options_card = ctk.CTkFrame(right_column, fg_color=Colors.Cards.SECONDARY, corner_radius=8)
        options_card.pack(fill="both", expand=True, pady=5, padx=5)
        
        ctk.CTkLabel(options_card, 
                    text="Export Options", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(pady=(20, 15))
     
        options_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        options_frame.pack(pady=10, padx=20, fill="x")
        
        self.header_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame, 
            text="Include Header", 
            variable=self.header_var,
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER
        ).pack(anchor="w", pady=5)

        self.footer_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame, 
            text="Include Footer", 
            variable=self.footer_var,
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER
        ).pack(anchor="w", pady=5)

        answer_frame = ctk.CTkFrame(options_card, fg_color="transparent")
        answer_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(answer_frame, text="Include Answers:").pack(anchor="w", pady=5)
        
        radio_frame = ctk.CTkFrame(answer_frame, fg_color="transparent")
        radio_frame.pack(anchor="w", pady=5)
        
        ctk.CTkRadioButton(
            radio_frame, 
            text="Yes", 
            variable=self.answer_checked, 
            value="Yes",
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER
        ).pack(side="left", padx=10)
        
        ctk.CTkRadioButton(
            radio_frame, 
            text="No", 
            variable=self.answer_checked, 
            value="No",
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER
        ).pack(side="left", padx=10)


        status_frame = ctk.CTkFrame(right_column, fg_color=Colors.Cards.SECONDARY, corner_radius=8)
        status_frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(status_frame, 
                    text="Validation Checks", 
                    font=("Arial", 14, "bold"),
                    text_color=Colors.Texts.HEADERS).pack(anchor="w", pady=(10, 5), padx=10)
        
        self.status_labels = {
            'file': self.create_status_row(status_frame, "Paper file selected"),
            'subject': self.create_status_row(status_frame, "Subject selected"),
            'title': self.create_status_row(status_frame, "Exam title set")
        }

        btn_frame = ctk.CTkFrame(right_column, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        self.generate_btn = PrimaryButton(
            master=btn_frame,
            text="Generate PDF",
            command=self.initiate_generation,
            width=200,
            height=45,
            state="disabled"
        )
        self.generate_btn.pack()

        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        self.master.update_idletasks()

    def setup_validations(self):
        self.file_entry.bind("<KeyRelease>", lambda e: self.validate_file())
        self.exam_title_entry.bind("<KeyRelease>", lambda e: self.validate_title())
        self.subject_combo.bind("<<ComboboxSelected>>", lambda e: self.validate_subject())

    def create_status_row(self, parent, text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=2)
        
        dot = ctk.CTkLabel(frame, text="●", text_color=Colors.Special.ERROR_TEXT, width=20)
        dot.pack(side="left")
        
        label = ctk.CTkLabel(frame, text=text, text_color=Colors.Texts.MUTED)
        label.pack(side="left", fill="x", expand=True)
        
        return (dot, label)

    def update_status(self, key, valid):
        color = Colors.SUCCESS if valid else Colors.Special.ERROR_TEXT
        self.status_labels[key][0].configure(text_color=color)
        self.status_labels[key][1].configure(
            text_color=Colors.Texts.FIELDS if valid else Colors.Texts.MUTED
        )
        self.generate_btn.configure(state="normal" if all(self.valid_states.values()) else "disabled")

    def validate_file(self):
        valid = bool(self.file_entry.get().strip())
        self.valid_states['file'] = valid
        self.update_status('file', valid)

    def validate_title(self):
        valid = bool(self.exam_title_entry.get().strip())
        self.valid_states['title'] = valid
        self.update_status('title', valid)

    def validate_subject(self):
        valid = self.subject_combo.get() != "Select Subject"
        self.valid_states['subject'] = valid
        self.update_status('subject', valid)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)
            self.validate_file()

    def get_subject_codes(self):
        subjects = self.db_manager.fetch_data()
        return [sub[0] for sub in subjects] 

    
    def update_subject_details(self, choice):
        subjects = self.db_manager.fetch_data()
        details = next((sub for sub in subjects if sub[0] == choice), None)

        if details and 'subject_name' in self.detail_labels:
            self.detail_labels['subject_name'].configure(text=details[1])
        else:
            messagebox.showwarning("Warning", "Subject details not found")
        
        self.time_duration_slider.set(5.0)
        self.update_time_label(5.0)
        self.validate_subject()

    def update_time_label(self, value):
        self.time_duration_label.configure(text=f"{round(value, 1)} min")

    def initiate_generation(self):
        if not all(self.valid_states.values()):
            messagebox.showerror("Validation Error", "Please complete all required fields")
            return
        
        self.generate_pdf()

    def validate_inputs(self):
        if not self.subject_combo.get():
            messagebox.showerror("Error", "Please select a subject code!")
            return False
        if not self.file_entry.get():
            messagebox.showerror("Error", "Please select an encrypted file!")
            return False
        return True


    def decrypt_file(self, file_path):
        pass_dialog = PasswordDialog(self, mode="decrypt")
        self.wait_window(pass_dialog)

        if pass_dialog.password:
            try:
                with open(file_path, "r") as f:
                    encrypted_data = json.load(f)

                decrypted_text = self._decrypt_data(encrypted_data, pass_dialog.password)
                if decrypted_text is None:
                    messagebox.showerror("Error", "Invalid password or corrupted file!")
                    return

                self.parsed_questions = json.loads(decrypted_text)
                messagebox.showinfo("Success", "File decrypted successfully!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Decryption failed: {str(e)}")

    def generate_pdf(self):
        
        try:
            total_duration = round(self.time_duration_slider.get() * len(self.parsed_questions), 1)
            subject_code = self.subject_combo.get()
            selected_subject = self.db_manager.get_subject_name(subject_code)
            exam_title = self.exam_title_entry.get().upper()
            if exam_title == "":
                exam_title = self.detail_labels['subject_name'].cget("text")
                return

            subject_details = {
                'title': exam_title,
                'subject_code': self.subject_combo.get(),
                'subject_name': self.detail_labels['subject_name'].cget("text"),
                'subject_date': self.subject_date_picker.get_date().strftime("%Y-%m-%d"),
                'time_duration': f"{total_duration} minutes",
                'total_marks': self.calculate_total_marks(),
                'instructions': self.db_manager.get_instructions(subject_code)
            }

            generator = GeneratePDF(
                title=exam_title,
                subject_details=subject_details,
                instructions=subject_details['instructions'], 
                questions=self.parsed_questions,
                enrollment_no="______", 
                logo_path=self.logo_path,
                include_header=self.header_var.get(),
                include_footer=self.footer_var.get(),
                show_answers=(self.answer_checked.get() == "Yes")
            )

            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")]
            )

            if file_path:
                generator.generate_pdf(file_path)        
                self.show_popup(file_path)

        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {str(e)}")

    def calculate_auto_duration(self, choice):
        try:
            total_questions = len(self.parsed_questions)
            minutes_per_question = int(choice)
            total_duration = total_questions * minutes_per_question
            self.final_duration_label.configure(text=f"Final: {total_duration} minutes")
        except ValueError:
            self.final_duration_label.configure(text="Final: -- minutes")


    def show_popup(self, file_path):
        if messagebox.askyesno("PDF Generated", "PDF generated successfully! Do you want to preview it?"):
            self.open_pdf(file_path)
        
        self.parent.redirect("home-page")

    def open_pdf(self, file_path):
        if os.name == 'nt':
            os.startfile(file_path)

    def _decrypt_data(self, encrypted_data, password):
        # ! Credits ! Tech with tim & Neuraline YT
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
    
    def _derive_key(self, password, salt):
        # ! Credits ! Tech with tim & Neuraline YT
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def calculate_total_marks(self):
        return sum(int(q['marks']) for q in self.parsed_questions)
