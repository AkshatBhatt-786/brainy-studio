import pandas as pd
from ui_components import *
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag
from create_paper import PasswordDialog
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkcalendar import DateEntry
from utils import getPath
import os
from PIL import Image
import base64
import json

class ExportToExcelUI(ctk.CTkFrame):
    def __init__(self, master, parent, container):
        super().__init__(master)
        self.parent = parent
        self.parent.title("Export to Excel")
        self.configure(fg_color="#0F172A")
        self.parsed_questions = []
        self.main_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_widgets()
    

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(header_frame, text="\nGenerate Your Questions to Excel Format!\n", font=("Arial", 21, "bold"),
                     image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\excel.png")), size=(50, 50)), compound="top").pack(padx=10, pady=10)
        
        file_frame = ctk.CTkFrame(self.main_frame, fg_color="#334155", corner_radius=8)
        file_frame.pack(padx=20, pady=20, anchor="center", fill="x")
        
        self.file_entry = ctk.CTkEntry(file_frame, placeholder_text="Select encrypted paper file")
        self.file_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        PrimaryButton(
            master=file_frame, 
            text="Browse", 
            command=lambda: self.select_file(),
            width=180,
            height=32
        ).pack(side="left", padx=10)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        excel_btn = PrimaryButton(
            master=btn_frame,
            text="Convert to Excel",
            command=lambda: self.process_data(),
        )
        excel_btn.pack(anchor="center", padx=10)
        excel_btn.configure(fg_color=Colors.SUCCESS, border_color=Colors.Buttons.SUCCESS_BORDER, hover_color=Colors.Buttons.SUCCESS_HOVER, text_color=Colors.Texts.SUCCESS)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)
    
    def save_file(self, data):
        try:
            if not isinstance(data, pd.DataFrame) or data.empty:
                messagebox.showwarning("Invalid Data", "No valid questions found to save.")
                return None
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[
                    ("Excel Files", "*.xlsx"),
                    ("Legacy Excel", "*.xls"),
                    ("All Files", "*.*")
                ],
                title="Save Question Bank As"
            )
            
            if not file_path:
                return None

            engine = 'openpyxl' if file_path.endswith('.xlsx') else 'xlwt'
            data.to_excel(file_path, index=False, engine=engine)

            if not os.path.exists(file_path):
                raise IOError("File was not created successfully")

            messagebox.showinfo(
                "Question Bank Saved Successfully",
                f"Question bank saved to:\n{file_path}\n\n"
                f"Contains {len(data)} questions\n"
                f"Total Marks: {data['Marks'].sum()}\n"
                "Formats preserved for future imports",
                icon='info'
            )

            if messagebox.askyesno("PDF Generated", "PDF generated successfully! Do you want to preview it?"):
                if os.name == 'nt':
                    os.startfile(file_path)
                else: 
                    subprocess.run(['open', file_path], check=True)
        
            self.parent.redirect("home-page")

        except Exception as e:
            messagebox.showerror(
                "Save Failed",
                f"Could not save question bank:\n{type(e).__name__}: {str(e)}",
                icon='error'
            )
            return None

    def process_data(self):
        try:
            if not self.parsed_questions or not isinstance(self.parsed_questions, list):
                messagebox.showwarning("No Data", "Decrypted question bank is empty or invalid.")
                return
            formatted_data = []
            for question in self.parsed_questions:
                if not all(key in question for key in ['id', 'text', 'tags', 'marks', 'type', 'correct']):
                    raise ValueError("Invalid question format in decrypted data")
                
                formatted_data.append({
                    'Question ID': str(question['id']),
                    'Question': str(question['text']),
                    'Tags': str(question['tags']),
                    'Marks': int(question['marks']),
                    'Options': ', '.join(map(str, question.get('options', []))),
                    'Question Type': str(question['type']),
                    'Answer': str(question['correct'])
                })

            df = pd.DataFrame(formatted_data)
            required_columns = ['Question ID', 'Question', 'Tags', 'Marks', 'Options', 'Question Type', 'Answer']
            if not all(col in df.columns for col in required_columns):
                raise ValueError("DataFrame missing required columns")
            df = df[required_columns]
            
            if df.empty:
                messagebox.showwarning("Empty Data", "No valid questions found after formatting.")
                return

            self.save_file(df)

        except Exception as e:
            messagebox.showerror(
                "Processing Error",
                f"Failed to process questions:\n{type(e).__name__}: {str(e)}"
            )


    def decrypt_file(self, file_path):
        pass_dialog = PasswordDialog(self, mode="decrypt")
        self.wait_window(pass_dialog)

        if pass_dialog.password:
            try:
                with open(file_path, "r") as f:
                    encrypted_data = json.load(f)

                decrypted_text = self._decrypt_data(encrypted_data, pass_dialog.password)
                if not decrypted_text:
                    raise ValueError("Empty decrypted content")
                
                self.parsed_questions = json.loads(decrypted_text)
                
                if not isinstance(self.parsed_questions, list) or len(self.parsed_questions) == 0:
                    raise ValueError("Decrypted data is not a valid question list")
                
                messagebox.showinfo("Success", f"Successfully decrypted {len(self.parsed_questions)} questions!")

            except Exception as e:
                messagebox.showerror("Decryption Error", f"Failed to decrypt file:\n{type(e).__name__}: {str(e)}")
                self.parsed_questions = []
    
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