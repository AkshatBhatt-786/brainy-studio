import customtkinter as ctk
from tkinter import messagebox, filedialog
from utils import centerWindow
from create_paper import PasswordDialog
from pdf_template import GeneratePDF 
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag

class GeneratePDFUI(ctk.CTkToplevel):
    def __init__(self, master, subject_db):
        super().__init__(master)
        self.title("Generate Exam Paper")
        self.geometry(centerWindow(master, 1000, 700, self._get_window_scaling()))
        self.configure(fg_color="#0F172A")
        self.subject_db = subject_db
        self.parsed_questions = []
        self.logo_path = ""
        
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
        for i, (key, label) in enumerate(zip(
            ['subject_name', 'subject_date', 'time_duration'],
            ['Subject Name:', 'Exam Date:', 'Duration:']
        )):
            frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            frame.grid(row=i//2, column=i%2, padx=5, pady=2)
            ctk.CTkLabel(frame, text=label).pack(side="left")
            self.detail_labels[key] = ctk.CTkLabel(frame, text="")
            self.detail_labels[key].pack(side="left")

        # File Selection
        file_frame = ctk.CTkFrame(main_frame, fg_color="#334155", corner_radius=8)
        file_frame.pack(pady=10, padx=20, fill="x")
        
        self.file_entry = ctk.CTkEntry(file_frame, placeholder_text="Select encrypted paper file")
        self.file_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        ctk.CTkButton(
            file_frame, 
            text="Browse", 
            command=self.select_file
        ).pack(side="left", padx=10)

        # PDF Options
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
        """Update subject details based on selected subject code"""
        details = self.subject_db.get(choice, {})
        for key in ['subject_name', 'subject_date', 'time_duration']:
            if key in details:
                self.detail_labels[key].configure(text=details[key])

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)
    
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

    def decrypt_file(self, file_path):
        pass_dialog = PasswordDialog(self, mode="decrypt")
        self.wait_window(pass_dialog)
        
        if pass_dialog.password:
            try:
                with open(file_path, "r") as f:
                    encrypt_data = json.load(f)
                

                self.parsed_questions = self._decrypt_data(encrypted_data=encrypt_data, password=pass_dialog.password) 
                messagebox.showinfo("Success", "File decrypted successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Decryption failed: {str(e)}")

    def calculate_total_marks(self):
        return sum(q['marks'] for q in self.parsed_questions)

    def get_subject_details(self):
        return {
            'subject_code': self.subject_combo.get(),
            'subject_name': self.detail_labels['subject_name'].cget("text"),
            'subject_date': self.detail_labels['subject_date'].cget("text"),
            'time_duration': self.detail_labels['time_duration'].cget("text"),
            'total_marks': self.calculate_total_marks()
        }

    def initiate_generation(self):
       
        if not self.validate_inputs():
            return
        
        pass_dialog = PasswordDialog(self, mode="set_password")
        self.wait_window(pass_dialog)
        
        if pass_dialog.password:
            self.generate_pdf(pass_dialog.password)

    def generate_pdf(self, password):
        try:
            generator = GeneratePDF(
                title=self.detail_labels['subject_name'].cget("text"),
                subject_details=self.get_subject_details(),
                instructions="", 
                questions=self.parsed_questions,
                enrollment_no="", 
                logo_path=self.logo_path,
                include_header=self.header_var.get(),
                include_footer=self.footer_var.get()
            )
     
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")]
            )
            
            if file_path:
                generator.generate_pdf(file_path, password)
                messagebox.showinfo("Success", "PDF generated successfully!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Generation failed: {str(e)}")
    
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

    def validate_inputs(self):
        if not self.subject_combo.get():
            messagebox.showerror("Error", "Please select a subject code!")
            return False
        if not self.file_entry.get():
            messagebox.showerror("Error", "Please select an encrypted file!")
            return False
        return True

    def select_logo(self):
        self.logo_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")]
        )

    def preview_pdf(self):
        pass

    def on_close(self):
        self.destroy()

subject_db = {  
        "4341601": {
            "subject_name": "Advance Java",
            "subject_date": "-",
            "time_duration": "-"
        }
    }

app = ctk.CTk()
app.withdraw()
GeneratePDFUI(app, subject_db)
app.mainloop()