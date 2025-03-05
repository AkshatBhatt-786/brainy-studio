import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from utils import centerWindow, getPath
from create_paper import PasswordDialog
from pdf_template import GeneratePDF 
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag
import datetime
import sys
import os
import subprocess

class GeneratePDFUI(ctk.CTkToplevel):
    def __init__(self, master, subject_db):
        super().__init__(master)
        self.attributes("-topmost", True)
        self.title("Generate Exam Paper")
        self.geometry(centerWindow(master, 1000, 600, self._get_window_scaling()))
        try:
            if sys.platform.startswith("win"):
                self.after(200, lambda: self.iconbitmap(getPath("assets\\icons\\icon.ico")))
        except Exception:
            pass
        self.configure(fg_color="#0F172A")
        self.subject_db = subject_db
        self.parsed_questions = []
        self.logo_path = ""
        self.answer_checked = ctk.StringVar(value="No")
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="#1E293B", corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(header_frame, text="Subject Code:").pack(side="left", padx=5)
        self.subject_combo = ctk.CTkComboBox(
            header_frame,
            values=list(self.subject_db.keys()),
            command=self.update_subject_details
        )
        self.subject_combo.pack(side="left", padx=5)
        
        self.detail_labels = {}
        details_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        details_frame.pack(side="left", padx=20)
        
        ctk.CTkLabel(details_frame, text="Subject Name:").grid(row=0, column=0, padx=5, pady=2)
        self.detail_labels['subject_name'] = ctk.CTkLabel(details_frame, text="")
        self.detail_labels['subject_name'].grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(details_frame, text="Exam Date:").grid(row=1, column=0, padx=5, pady=2)
        self.subject_date_picker = DateEntry(details_frame, date_pattern='yyyy-mm-dd', mindate=datetime.date.today() + datetime.timedelta(days=1))
        self.subject_date_picker.grid(row=1, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(details_frame, text="Duration:").grid(row=2, column=0, padx=5, pady=2)
        self.detail_labels['time_duration'] = ctk.CTkLabel(details_frame, text="")
        self.detail_labels['time_duration'].grid(row=2, column=1, padx=5, pady=2)

        file_frame = ctk.CTkFrame(main_frame, fg_color="#334155", corner_radius=8)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        self.file_entry = ctk.CTkEntry(file_frame, placeholder_text="Select encrypted paper file")
        self.file_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        ctk.CTkButton(
            file_frame, 
            text="Browse", 
            command=self.select_file
        ).pack(side="left", padx=10)

        options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
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
        
        ctk.CTkButton(
            options_frame, 
            text="Select Logo", 
            command=self.select_logo
        ).pack(side="right", padx=10)

        answer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        answer_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(answer_frame, text="Include Answers:").pack(side="left", padx=10)
        ctk.CTkRadioButton(answer_frame, text="Yes", variable=self.answer_checked, value="Yes").pack(side="left", padx=10)
        ctk.CTkRadioButton(answer_frame, text="No", variable=self.answer_checked, value="No").pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Preview PDF",
            fg_color="#3B82F6",
            command=self.preview_pdf
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Generate PDF",
            fg_color="#10B981",
            command=self.initiate_generation
        ).pack(side="left", padx=10)
    
    def update_subject_details(self, choice):
        details = self.subject_db.get(choice, {})
        self.detail_labels['subject_name'].configure(text=details.get("subject_name", ""))
        self.detail_labels['time_duration'].configure(text=details.get("time_duration", ""))
    
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)

    def select_logo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.logo_path = file_path
            messagebox.showinfo("Logo Selected", "Logo has been successfully selected.")

    def preview_pdf(self):
        messagebox.showinfo("Preview PDF", "PDF preview functionality is not yet implemented.")

    def initiate_generation(self):
        """Validates inputs and starts PDF generation."""
        if not self.validate_inputs():
            return

        pass_dialog = PasswordDialog(self, mode="set_password")
        self.wait_window(pass_dialog)

        if pass_dialog.password:
            self.generate_pdf(pass_dialog.password)

    def validate_inputs(self):
        """Check if subject and file are selected."""
        if not self.subject_combo.get():
            messagebox.showerror("Error", "Please select a subject code!")
            return False
        if not self.file_entry.get():
            messagebox.showerror("Error", "Please select an encrypted file!")
            return False
        return True

    def on_close(self):
        """Handles window close event."""
        self.destroy()

    def decrypt_file(self, file_path):
        """Decrypt the selected file and parse the questions."""
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

    def generate_pdf(self, password):
        """Generate the PDF based on user selections."""
        try:
            subject_details = {
                'subject_code': self.subject_combo.get(),
                'subject_name': self.detail_labels['subject_name'].cget("text"),
                'subject_date': self.subject_date_picker.get_date(),
                'time_duration': self.detail_labels['time_duration'].cget("text"),
                'total_marks': self.calculate_total_marks()
            }

            generator = GeneratePDF(
                title=self.detail_labels['subject_name'].cget("text"),
                subject_details=subject_details,
                instructions="", 
                questions=self.parsed_questions,
                enrollment_no="", 
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

    def show_popup(self, file_path):
        if messagebox.askyesno("PDF Generated", "PDF generated successfully! Do you want to preview it?"):
            self.open_pdf(file_path)
        
        self.destroy()

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
        """Calculate the total marks from the parsed questions."""
        return sum(int(q['marks']) for q in self.parsed_questions)
