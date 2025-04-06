import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
import json
import datetime
from ui_components import Colors, PrimaryButton, LinkButton
from create_paper import PasswordDialog
import customtkinter as ctk
from math import floor
from random import random
import base64
from utils import getPath, centerWindow
import os
from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag
from dropbox_backend import DropboxBackend
from firebase_backend import FirebaseBackend
from subject_db import SubjectManagerUI
import sys

DBX_PATH = os.getenv("DBX_BACKEND")

class TimePickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, initial_time=None):
        super().__init__(parent)
        self.title("Select Time")
        try:
            if sys.platform.startswith("win"):
                self.after(200, lambda: self.iconbitmap(getPath("assets\\icons\\icon.ico")))
        except Exception:
            pass
        self.geometry(centerWindow(parent, 380, 280, parent._get_window_scaling()))
        self.resizable(False, False)
        self.configure(fg_color=Colors.PRIMARY)
        self.transient(parent)
        self.grab_set()
        
        self.time_str = ""
        self.hours = 12
        self.minutes = 0
        self.am_pm = "AM"
        
        if initial_time:
            self._parse_initial_time(initial_time)
        
        self._create_widgets()
        self._center_on_parent(parent)

    def _parse_initial_time(self, time_str):
        try:
            time_obj = datetime.strptime(time_str, "%I:%M %p")
            self.hours = time_obj.hour % 12 or 12
            self.minutes = time_obj.minute
            self.am_pm = "AM" if time_obj.hour < 12 else "PM"
        except ValueError:
            pass

    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color=Colors.PRIMARY)
        container.pack(padx=20, pady=20, fill="both", expand=True)

        time_frame = ctk.CTkFrame(container, fg_color=Colors.SECONDARY, corner_radius=8)
        time_frame.pack(pady=10, fill="x")
        hours_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        hours_frame.pack(side="left", expand=True, padx=10)

        ctk.CTkButton(
            hours_frame, 
            text="↑", 
            width=30, 
            height=30,
            command=lambda: self._update_time("hours", 1),
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER,
            font=("Arial", 16)
        ).pack()

        self.hours_label = ctk.CTkLabel(
            hours_frame, 
            text=f"{self.hours:02d}", 
            font=("Arial", 32, "bold"), 
            text_color=Colors.Texts.HEADERS
        )
        self.hours_label.pack(pady=5)

        ctk.CTkButton(
            hours_frame, 
            text="↓", 
            width=30, 
            height=30,
            command=lambda: self._update_time("hours", -1),
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER,
            font=("Arial", 16)
        ).pack()

        minutes_frame = ctk.CTkFrame(time_frame, fg_color="transparent")
        minutes_frame.pack(side="left", expand=True, padx=10)

        ctk.CTkButton(
            minutes_frame, 
            text="↑", 
            width=30, 
            height=30,
            command=lambda: self._update_time("minutes", 1),
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER,
            font=("Arial", 16)
        ).pack()

        self.minutes_label = ctk.CTkLabel(
            minutes_frame, 
            text=f"{self.minutes:02d}", 
            font=("Arial", 32, "bold"), 
            text_color=Colors.Texts.HEADERS
        )
        self.minutes_label.pack(pady=5)

        ctk.CTkButton(
            minutes_frame, 
            text="↓", 
            width=30, 
            height=30,
            command=lambda: self._update_time("minutes", -1),
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER,
            font=("Arial", 16)
        ).pack()

        self.am_pm_selector = ctk.CTkSegmentedButton(
            container,
            values=["AM", "PM"],
            command=self._update_am_pm,
            selected_color=Colors.ACCENT,
            selected_hover_color=Colors.Buttons.PRIMARY_HOVER,
            unselected_color=Colors.Inputs.BACKGROUND,
            unselected_hover_color=Colors.Sidebar.HOVER,
            font=("Arial", 14, "bold"),
            text_color=Colors.Texts.HEADERS
        )
        self.am_pm_selector.pack(pady=10)
        self.am_pm_selector.set(self.am_pm)

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(pady=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            fg_color=Colors.Buttons.SECONDARY,
            hover_color=Colors.Buttons.SECONDARY_HOVER
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="OK",
            command=self._ok,
            fg_color=Colors.Buttons.PRIMARY,
            hover_color=Colors.Buttons.PRIMARY_HOVER
        ).pack(side="right", padx=5)

    def _update_time(self, unit, delta):
        if unit == "hours":
            self.hours = (self.hours + delta - 1) % 12 + 1
            self.hours_label.configure(text=f"{self.hours:02d}")
        elif unit == "minutes":
            self.minutes = (self.minutes + delta) % 60
            self.minutes_label.configure(text=f"{self.minutes:02d}")

    def _update_am_pm(self, value):
        self.am_pm = value

    def _ok(self):
        hour24 = self.hours if self.am_pm == "AM" else self.hours + 12
        if hour24 == 24: hour24 = 12
        if hour24 == 12 and self.am_pm == "AM": hour24 = 0
        self.time_str = f"{hour24:02d}:{self.minutes:02d}"
        self.destroy()

    def _center_on_parent(self, parent):
        # ! CREDITS/REFERENCES : stakeoverflow
        parent.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        
        self.geometry(f"+{x}+{y}")

    @staticmethod
    def get_time(parent, initial_time=None):
        dialog = TimePickerDialog(parent, initial_time)
        parent.wait_window(dialog)
        return dialog.time_str if hasattr(dialog, 'time_str') else ""

class CloudPublishUI(ctk.CTkFrame):
    def __init__(self, master, parent, subject_db):
        super().__init__(master, fg_color=Colors.BACKGROUND)
        self.master = master
        self.db_manager = subject_db
        self.parent = parent
        self.file_path = None
        self.parsed_questions = []
        self.registration_times = None
        
        self.create_widgets()
    
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)

    def get_subject_codes(self):
        subjects = self.db_manager.fetch_data()
        return [sub[0] for sub in subjects] 

    def update_subject_details(self, choice):
        subjects = self.db_manager.fetch_data()
        details = next((sub for sub in subjects if sub[0] == choice), None)

        if details:
            self.detail_labels['subject_name'].configure(text=details[1])
        else:
            self.detail_labels['subject_name'].configure(text="")
        
        self.time_duration_slider.set(5.0)
        self.update_time_label(5.0)
        self.calculate_total_marks()
        self.calculate_total_questions()
        
    def update_time_label(self, value):
        self.time_duration_label.configure(text=f"{round(value, 1)} min")
        self.calculate_total_marks()
    
    def calculate_total_marks(self):
        total_marks = sum(int(q['marks']) for q in self.parsed_questions) if self.parsed_questions else 0
        self.detail_labels['total_marks'].configure(text=str(total_marks))

    def calculate_total_questions(self):
        total_questions = len(self.parsed_questions)
        self.detail_labels['total_questions'].configure(text=str(total_questions))
        
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.decrypt_file(file_path)

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
                self.calculate_total_questions()
                self.calculate_total_marks()
                messagebox.showinfo("Success", "File decrypted successfully!")

            except Exception as e:
                messagebox.showerror("Error", f"Decryption failed: {str(e)}")
    
    def create_widgets(self):
        main_frame = ctk.CTkFrame(self.master, fg_color=Colors.Cards.BACKGROUND)
        main_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(
            main_frame,
            text="",
            image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\cloud-computing.png")), size=(50, 50)),
            compound="top"
        ).pack(anchor="center", padx=10, pady=10)

        ctk.CTkLabel(main_frame, 
                     text="\nExport your Exam to Cloud Exam Platform", 
                     font=("Arial", 21, "bold")
                     ).pack(padx=10, pady=10)
    

        file_frame = ctk.CTkFrame(main_frame, fg_color="#334155")
        file_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(file_frame, text="Encrypted Paper File:").pack(side="left", padx=5)
        self.file_entry = ctk.CTkEntry(
            file_frame, 
            placeholder_text="Select .enc file",
            width=300
        )
        self.file_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        PrimaryButton(
            master=file_frame, 
            text="Browse", 
            command=self.select_file, 
            width=120,
            height=42
        ).pack(side="left", pady=10, padx=5)

        subject_frame = ctk.CTkFrame(main_frame, fg_color=Colors.Cards.BACKGROUND)
        subject_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(subject_frame, text="Subject Code:").pack(side="left", padx=5)
        self.subject_combo = ctk.CTkComboBox(
            subject_frame,
            values=self.get_subject_codes(),
            width=200,
            fg_color=Colors.Inputs.BACKGROUND,
            text_color=Colors.Inputs.TEXT,
            border_color=Colors.Inputs.BORDER,
            command=self.update_subject_details
        )
        self.subject_combo.pack(side="left", padx=5)
        self.subject_combo.set("---SELECT---")

        LinkButton(subject_frame, text="update database", command=lambda parent=self.parent, frame=self: SubjectManagerUI(parent, frame)).pack(side="left", padx=10)

        details_frame = ctk.CTkFrame(main_frame, fg_color=Colors.Cards.BACKGROUND)
        details_frame.pack(fill="x", padx=10, pady=10)
        self.detail_labels = {}

        ctk.CTkLabel(details_frame, text="Subject Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.detail_labels['subject_name'] = ctk.CTkLabel(details_frame, text="")
        self.detail_labels['subject_name'].grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(details_frame, text="Total Questions:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.detail_labels['total_questions'] = ctk.CTkLabel(details_frame, text="0")
        self.detail_labels['total_questions'].grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(details_frame, text="Total Marks:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.detail_labels['total_marks'] = ctk.CTkLabel(details_frame, text="0")
        self.detail_labels['total_marks'].grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(details_frame, text="Exam Date:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.subject_date_picker = DateEntry(
            details_frame, 
            date_pattern='yyyy-mm-dd', 
            mindate=datetime.date.today())
        self.subject_date_picker.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(details_frame, text="Time per Question:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        time_duration_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        time_duration_frame.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        
        self.time_duration_slider = ctk.CTkSlider(
            time_duration_frame, 
            from_=1, 
            to=10, 
            number_of_steps=18, 
            command=self.update_time_label,
            width=200
        )
        self.time_duration_slider.set(5.0)
        self.time_duration_slider.pack(side="left", padx=5)
        self.time_duration_label = ctk.CTkLabel(time_duration_frame, text="5.0 min")
        self.time_duration_label.pack(side="left", padx=5)

        ctk.CTkLabel(details_frame, text="Registration Window:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        reg_time_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        reg_time_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        
        self.registration_time_label = ctk.CTkLabel(reg_time_frame, text="Not Set")
        self.registration_time_label.pack(side="left", padx=5)
        
        PrimaryButton(
            reg_time_frame, 
            text="Set Time", 
            command=self.set_registration_time,
            width=120,
            height=42
        ).pack(side="left", padx=5)

        submit_frame = ctk.CTkFrame(main_frame, fg_color=Colors.Cards.BACKGROUND)
        submit_frame.pack(fill="x", pady=5)

        PrimaryButton(
            submit_frame,
            text="Upload",
            command=self.export_to_dropbox,
            width=120,
            height=42
        ).pack(anchor="center", padx=5)

        ctk.CTkLabel(main_frame, 
                     text="Powered by Cloud Exam", 
                     font=("Consolas", 16, "bold"),
                     image=ctk.CTkImage(light_image=Image.open(getPath("assets\\images\\cloud_logo.png")), size=(80, 80)),
                     compound="right").pack(anchor="w", padx=10, pady=10)

    def set_registration_time(self):
        start_time_str = TimePickerDialog.get_time(self.parent)
        if not start_time_str:
            return
            
        duration_dialog = ctk.CTkToplevel(self.master)
        duration_dialog.title("Select Duration Extension")
        duration_dialog.geometry(centerWindow(self.parent, 600, 300, self.parent._get_window_scaling()))
        duration_dialog.transient(self.master)
        duration_dialog.configure(fg_color=Colors.BACKGROUND)
        
        ctk.CTkLabel(duration_dialog, text="Extend registration window by:").pack(pady=10)
        
        btn_frame = ctk.CTkFrame(duration_dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        selected_duration = ctk.IntVar(value=0)
        
        for mins in [10, 20, 30]:
            ctk.CTkRadioButton(
                btn_frame,
                text=f"{mins} minutes",
                variable=selected_duration,
                value=mins,
                fg_color=Colors.Radio.PRIMARY,
                hover_color=Colors.Radio.HOVER,
                text_color=Colors.Radio.TEXT
            ).pack(side="left", padx=10)
        
        def confirm_duration():
            duration_dialog.destroy()
            duration_dialog.grab_release()
            
        ctk.CTkButton(
            duration_dialog,
            text="Confirm",
            command=confirm_duration
        ).pack(pady=10)
        
        self.wait_window(duration_dialog)
        
        if selected_duration.get() == 0:
            return
    
        start_h, start_m = map(int, start_time_str.split(':'))
        start_dt = datetime.datetime.combine(datetime.date.today(), datetime.time(start_h, start_m))
        end_dt = start_dt + datetime.timedelta(minutes=selected_duration.get())
        
        self.registration_times = (
            start_dt.strftime("%H:%M"),
            end_dt.strftime("%H:%M")
        )
        self.registration_time_label.configure(
            text=f"{self.registration_times[0]} - {self.registration_times[1]}",
            text_color=Colors.Texts.FIELDS
        )

    @staticmethod
    def generate_exam_id():
        idx = ""
        characters = "123456789"

        for i in range(4):
            idx += characters[floor(random() * len(characters))]

        return f"BS{idx}"

    @staticmethod
    def generate_access_code():
        characters = "123456789"
        access_code = ""

        for i in range(4):
            access_code += characters[floor(random() * len(characters))]

        return f"CE{access_code}"
    
    @staticmethod
    def remove_correct_answers(parsed_questions):
        question_dict = {}

        for index, question in enumerate(parsed_questions, start=1):
            question_id = f"Q{index}" 
            question_copy = question.copy()

            if "correct" in question_copy:
                question_copy.pop("correct")

            question_dict[question_id] = question_copy

        return question_dict

    @staticmethod
    def extract_correct_answers(parsed_questions):
        correct_answers_dict = {}

        for index, question in enumerate(parsed_questions, start=1):
            if "correct" in question:
                question_id = f"Q{index}"
                correct_answers_dict[question_id] = question["correct"]

        return correct_answers_dict

    @staticmethod
    def create_question_id_mapping(parsed_questions):
        question_id_mapping = {}

        for index, question in enumerate(parsed_questions, start=1):
            if "id" in question:
                question_id_mapping[f"Q{index}"] = question["id"]

        return question_id_mapping


    def export_to_dropbox(self):
        total_duration = round(self.time_duration_slider.get() * len(self.parsed_questions), 1)
        instructions = self.db_manager.get_instructions(self.subject_combo.get()).split("\n")
        questions = self.remove_correct_answers(self.parsed_questions)
        answers = self.extract_correct_answers(self.parsed_questions)
        questions_blueprint = self.create_question_id_mapping(self.parsed_questions)
        access_code = self.generate_access_code()
        exam_id = self.generate_exam_id()

        exam_paper = {
            "brainy-studio": {
                "version": "1.2.0 (beta)"
            },
            "auth_data": {
                "exam-id": exam_id,
                "access-code": access_code,
                "registration_time": self.registration_times[0],
                "registration_end_time": self.registration_times[1],
                "registration_date": self.subject_date_picker.get_date().strftime("%d-%m-%Y")
            },
            "subject_details": {
                "subject_name": self.detail_labels["subject_name"].cget("text"),
                "subject_code": self.subject_combo.get(),
                "time_duration": total_duration,
                "registration_time": self.registration_times[0],
                "registration_end_time": self.registration_times[1],
                "exam_start_time": self.registration_times[1],
                "instructions": instructions,
                "subject_date": self.subject_date_picker.get_date().strftime("%d-%m-%Y"),
                "total_marks": self.detail_labels["total_marks"].cget("text")
            },
            "questions": questions,
            "question-mapping": questions_blueprint,
            "answer-key": answers
        }

        encrypted_data = self._encrypt_data(exam_paper, access_code)
        file_path = getPath(f"database\\CloudDB\\{exam_id}.enc")

        with open(file_path, 'w') as f:
            json.dump(encrypted_data, f)

        with open(DBX_PATH, "r") as f:
            data = json.load(f)

        access_token = data["access_token"]
        app_key = data["app_key"]
        app_secret = data["app_secret"]
        dbx_backend = DropboxBackend(access_token=access_token, app_key=app_key, app_secret=app_secret, root_path=getPath(r"database\CloudDB"))
        try:
            upload_file = dbx_backend.upload_file(file_path, f"/uploads/{exam_id}.enc")
            if upload_file:
                result_link = FirebaseBackend()
                try:
                    created = result_link.create_exam(exam_id=exam_id, access_code=access_code, subject_details=exam_paper["subject_details"])
                    if created:
                        messagebox.showinfo("Paper Generated Successfully!", f"EXAM-ID: {exam_id}, \nACCESS-CODE: {access_code}")
                except Exception as e:
                        messagebox.showerror("Something Went Wrong!, Try Again Later!")
        except Exception as e:
            messagebox.showerror("Something Went Wrong!", f"{e}")
        
        return

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

    def _encrypt_data(self, data, password):
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        iv = os.urandom(16)

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        data_str = json.dumps(data)

        pad_len = 16 - (len(data_str) % 16)
        padded_data = data_str + chr(pad_len) * pad_len

        ciphertext = encryptor.update(padded_data.encode()) + encryptor.finalize()

        return {
            'salt': base64.b64encode(salt).decode(),
            'iv': base64.b64encode(iv).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode()
        }


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