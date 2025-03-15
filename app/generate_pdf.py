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
        self.parsed_questions = []
        self.logo_path = getPath(r"assets\images\logo.png")
        self.answer_checked = ctk.StringVar(value="No")
        self.main_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.create_widgets()
        # self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):

        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(header_frame, text="Generate Your Questions to PDF Format!", font=("Arial", 21, "bold")).pack(padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Subject Code:").pack(side="left", padx=5)
        self.subject_combo = ctk.CTkComboBox(
            header_frame,
            values=self.get_subject_codes(),
            fg_color=Colors.Inputs.BACKGROUND,
            text_color=Colors.Inputs.TEXT,
            border_color=Colors.Inputs.BORDER,
            dropdown_fg_color=Colors.SECONDARY,
            dropdown_hover_color=Colors.HIGHLIGHT,
            dropdown_text_color=Colors.Inputs.TEXT,
            command=self.update_subject_details
        )
        self.subject_combo.pack(side="left", padx=5)
        self.subject_combo.set("---SELECT---")

        LinkButton(header_frame, text="Edit Database!", command=lambda parent=self.parent: SubjectManagerUI(parent)).pack(side="left", padx=10)
        
        self.detail_labels = {}
        details_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        details_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(details_frame, text="Subject Name:", font=("Arial", 16, "bold")).grid(row=0, column=0, padx=5, pady=2)
        self.detail_labels['subject_name'] = ctk.CTkLabel(details_frame, text="")
        self.detail_labels['subject_name'].grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(details_frame, text="Exam Date:").grid(row=1, column=0, padx=5, pady=2)
        self.subject_date_picker = DateEntry(details_frame, date_pattern='yyyy-mm-dd', mindate=datetime.date.today() + datetime.timedelta(days=1))
        self.subject_date_picker.grid(row=1, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(details_frame, text="Duration (min):").grid(row=2, column=0, padx=5, pady=2)

        self.time_duration_label = ctk.CTkLabel(details_frame, text="5.0 min per question.")  
        self.time_duration_label.grid(row=2, column=2, padx=5, pady=2)

        # Create Slider for 1 - 10 min (step size 0.5)
        self.time_duration_slider = ctk.CTkSlider(
            details_frame,
            from_=1,
            to=10,   
            number_of_steps=18,
            command=self.update_time_label, 
        )
        self.time_duration_slider.set(5.0) 
        self.time_duration_slider.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

        file_frame = ctk.CTkFrame(self.main_frame, fg_color="#334155", corner_radius=8)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        self.file_entry = ctk.CTkEntry(file_frame, placeholder_text="Select encrypted paper file")
        self.file_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        PrimaryButton(
            master=file_frame, 
            text="Browse", 
            command=self.select_file,
            width=180,
            height=32
        ).pack(side="left", padx=10)

        options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        options_frame.pack(pady=10, padx=20, fill="x")
        
        self.header_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame, 
            text="Include Header", 
            variable=self.header_var
        ).pack(side="left", padx=10)
        
        self.footer_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame, 
            text="Include Footer", 
            variable=self.footer_var
        ).pack(side="left", padx=10)

        answer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        answer_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(answer_frame, text="Include Answers:").pack(side="left", padx=10)
        ctk.CTkRadioButton(answer_frame, text="Yes", variable=self.answer_checked, value="Yes").pack(side="left", padx=10)
        ctk.CTkRadioButton(answer_frame, text="No", variable=self.answer_checked, value="No").pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        PrimaryButton(
            master=btn_frame,
            text="Generate PDF",
            command=self.initiate_generation
        ).pack(side="left", padx=10)

    def get_subject_codes(self):
        subjects = self.db_manager.fetch_data()
        return [sub[0] for sub in subjects] 

    
    def update_subject_details(self, choice):
        subjects = self.db_manager.fetch_data()
        details = next((sub for sub in subjects if sub[0] == choice), None)

        if details:
            self.detail_labels['subject_name'].configure(text=details[1])  # Subject Name
        else:
            self.detail_labels['subject_name'].configure(text="")
        
        self.time_duration_slider.set(5.0)
        self.update_time_label(5.0)

    def update_time_label(self, value):
        self.time_duration_label.configure(text=f"{round(value, 1)} min")

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)

    def initiate_generation(self):
        if not self.validate_inputs():
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
            selected_subject = self.subject_db.get(subject_code, {})

            subject_details = {
                'subject_code': self.subject_combo.get(),
                'subject_name': self.detail_labels['subject_name'].cget("text"),
                'subject_date': self.subject_date_picker.get_date().strftime("%Y-%m-%d"),
                'time_duration': f"{total_duration} minutes",
                'total_marks': self.calculate_total_marks(),
                'instructions': selected_subject.get("instructions", [])
            }

            generator = GeneratePDF(
                title=self.detail_labels['subject_name'].cget("text"),
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
        else:
            subprocess.call(["xdg-open", file_path])

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
