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
import xlsxwriter
import json
from firebase_backend import FirebaseBackend

class ExportToExcelUI(ctk.CTkFrame):
    def __init__(self, master, parent, container):
        super().__init__(master)
        self.parent = parent
        self.backend = FirebaseBackend()
        self.db = self.backend.db
        self.parent.title("Export to Excel")
        self.configure(fg_color="#0F172A")
        self.parsed_questions = []
        self.main_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=12)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.create_widgets()
    

    def create_widgets(self):
        # === Header Section ===
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(pady=20, padx=20, fill="x")
    
        ctk.CTkLabel(
            header_frame,
            text="Brainy Studio\nGenerate Your Questions to Excel Format!",
            font=("Segoe UI", 24, "bold"),
            text_color="#f8fafc",
            compound="top",
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\excel.png")), size=(50, 50))
        ).pack(pady=(0, 10), anchor="center")
    
        # === Tab Section ===
        tabview = ctk.CTkTabview(self.main_frame, fg_color="#1e293b", segmented_button_selected_color="#0ea5e9")
        tabview.pack(padx=20, pady=10, fill="both", expand=True)
    
        # === Local File Tab ===
        tab1 = tabview.add("Local Question Bank File")
        local_file_frame = ctk.CTkFrame(tab1, fg_color="#1e293b", corner_radius=12)
        local_file_frame.pack(padx=20, pady=20, fill="x", expand=True)
    
        ctk.CTkLabel(local_file_frame, text="Choose Encrypted File:", text_color="white", font=("Segoe UI", 14)).pack(anchor="w", padx=10, pady=(10, 0))
    
        file_input_frame = ctk.CTkFrame(local_file_frame, fg_color="transparent")
        file_input_frame.pack(padx=10, pady=10, fill="x")
    
        self.file_entry = ctk.CTkEntry(file_input_frame, placeholder_text="Select encrypted paper file",           width=300, fg_color=Colors.Inputs.BACKGROUND, border_color=Colors.Inputs.BORDER)
        self.file_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
    
        PrimaryButton(
            master=file_input_frame,
            text="Browse",
            command=lambda: self.select_file(),
            width=140,
            height=36
        ).pack(side="left")
    
        # === Cloud Export Tab ===
        tab2 = tabview.add("Cloud Exam Reports")
        cloud_frame = ctk.CTkFrame(tab2, fg_color="#1e293b", corner_radius=12)
        cloud_frame.pack(padx=20, pady=20, fill="x", expand=True)
    
        ctk.CTkLabel(cloud_frame, text="Enter Exam ID:", text_color="white", font=("Segoe UI", 14)).pack(anchor="w", padx=10, pady=(10, 0))
    
        cloud_input_frame = ctk.CTkFrame(cloud_frame, fg_color="transparent")
        cloud_input_frame.pack(padx=10, pady=10, fill="x")
    
        self.cloud_exam_id_entry = ctk.CTkEntry(cloud_input_frame, placeholder_text="e.g., #BS0786",        width=300, fg_color=Colors.Inputs.BACKGROUND, border_color=Colors.Inputs.BORDER)
        self.cloud_exam_id_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
    
        PrimaryButton(
            master=cloud_input_frame,
            text="Fetch from Cloud",
            command=lambda: self.fetch_cloud_results(),
            width=160,
            height=36
        ).pack(side="left")
    
        # === Convert Button Section ===
        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=30)
    
        excel_btn = PrimaryButton(
            master=btn_frame,
            text="🚀 Convert to Excel",
            command=lambda: self.process_data(),
            width=220,
            height=48
       )
        excel_btn.pack(anchor="center", padx=10)
    
        excel_btn.configure(
            fg_color=Colors.SUCCESS,
            border_color=Colors.Buttons.SUCCESS_BORDER,
            hover_color=Colors.Buttons.SUCCESS_HOVER,
            text_color=Colors.Texts.SUCCESS
        )

    
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

    def fetch_cloud_results(self):
        exam_id = self.cloud_exam_id_entry.get().strip()
        if not exam_id:
            messagebox.showwarning("Input Error", "Please enter Exam ID")
            return

        try:
            exam_ref = self.db.collection("exams").document(exam_id)
            exam_doc = exam_ref.get()
            if not exam_doc.exists:
                raise ValueError(f"Exam {exam_id} not found")
            exam_data = exam_doc.to_dict()
            subject_details = exam_data.get('subject_details', {})
            total_marks = int(subject_details.get('total_marks', 0))
            students_data = exam_data.get('students', {})

            self.parsed_results = []
            for enrollment_no, student_data in students_data.items():
                self.parsed_results.append({
                    "enrollment_no": enrollment_no,
                    "marks_obtained": student_data.get('total_score', 0),
                    "total_marks": total_marks,
                    "negative_marks": student_data.get('marks_wrong', 0),
                    "not_attempted": student_data.get('not_attempted', 0)
                })

            approval = messagebox.askyesno("Success", f"Processed {len(self.parsed_results)} student results!")
            if approval:
                sub_name = subject_details.get("subject_name")
                sub_date = subject_details.get("subject_date")
                title = sub_name + " | " + sub_date + " | " + "Result"
                self.process_result_data(title)

        except Exception as e:
            messagebox.showerror("Cloud Error", f"Fetch failed: {str(e)}")
            self.parsed_results = []

    def process_result_data(self, exam_title="Cloud Exam Result"):
        try:
            if not self.parsed_results:
                raise ValueError("No results data to process")

            processed = []
            for result in self.parsed_results:
                processed.append({
                    "Enrollment No": result.get("enrollment_no", ""),
                    "Marks Obtained": result.get("marks_obtained", 0),
                    "Total Marks": result.get("total_marks", 0),
                    "Negative Marks": result.get("wrong_marks", 0),
                    "Not Attempted": result.get("not_attempted", 0)
                })

            df = pd.DataFrame(processed)
            self.save_results_file(df, exam_title)

        except Exception as e:
            messagebox.showerror(
                "Processing Error", 
                f"Failed to process results:\n{type(e).__name__}: {str(e)}"
            )

    def save_results_file(self, df, title):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")],
                title="Save Exam Results As"
            )

            if not file_path:
                return

            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Results', startrow=1)

            workbook = writer.book
            worksheet = writer.sheets['Results']

            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#D9E1F2'
            })
            worksheet.merge_range(0, 0, 0, len(df.columns) - 1, title, title_format)

            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })

            normal_format = workbook.add_format({
                'border': 1,
                'valign': 'top',
            })
            alt_format = workbook.add_format({
                'bg_color': '#F2F2F2',
                'border': 1,
                'valign': 'top',
            })

            for col_num, column_name in enumerate(df.columns.values):
                worksheet.write(1, col_num, column_name, header_format)

            for row_num, row_data in enumerate(df.values, start=2):
                for col_num, cell_data in enumerate(row_data):
                    fmt = alt_format if (row_num - 2) % 2 == 0 else normal_format
                    worksheet.write(row_num, col_num, cell_data, fmt)

            for i, column in enumerate(df.columns):
                max_len = max(df[column].astype(str).map(len).max(), len(column))
                worksheet.set_column(i, i, max_len + 2)

            worksheet.freeze_panes(2, 0)

            writer.close()
            messagebox.showinfo("Success", f"Results exported successfully!\n{len(df)} records saved")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save results: {str(e)}")


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