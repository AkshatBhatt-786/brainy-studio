import customtkinter as ctk
from tkinter import filedialog, messagebox
import random
import string
import json
import datetime
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidKey, InvalidTag
from ui_components import Colors, PrimaryButton
from create_paper import PasswordDialog

class TimePickerDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Set Registration Time")
        self.geometry("400x250")
        self.resizable(False, False)
        self.start_time = None
        self.end_time = None
        
        self.create_widgets()
    
    def create_widgets(self):
        time_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        time_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Start Time
        ctk.CTkLabel(time_frame, text="Start Time:", text_color=Colors.Texts.HEADERS).grid(row=0, column=0, padx=5, pady=5)
        self.start_hour = ctk.CTkComboBox(time_frame, values=[f"{h:02d}" for h in range(1, 13)], width=60)
        self.start_hour.grid(row=0, column=1, padx=5)
        self.start_min = ctk.CTkComboBox(time_frame, values=[f"{m:02d}" for m in range(0, 60, 5)], width=60)
        self.start_min.grid(row=0, column=2, padx=5)
        self.start_ampm = ctk.CTkComboBox(time_frame, values=["AM", "PM"], width=60)
        self.start_ampm.grid(row=0, column=3, padx=5)
        
        # End Time
        ctk.CTkLabel(time_frame, text="End Time:", text_color=Colors.Texts.HEADERS).grid(row=1, column=0, padx=5, pady=5)
        self.end_hour = ctk.CTkComboBox(time_frame, values=[f"{h:02d}" for h in range(1, 13)], width=60)
        self.end_hour.grid(row=1, column=1, padx=5)
        self.end_min = ctk.CTkComboBox(time_frame, values=[f"{m:02d}" for m in range(0, 60, 5)], width=60)
        self.end_min.grid(row=1, column=2, padx=5)
        self.end_ampm = ctk.CTkComboBox(time_frame, values=["AM", "PM"], width=60)
        self.end_ampm.grid(row=1, column=3, padx=5)
        
        # Set default values
        self.start_hour.set("09")
        self.start_min.set("00")
        self.start_ampm.set("AM")
        self.end_hour.set("10")
        self.end_min.set("00")
        self.end_ampm.set("AM")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        btn_frame.pack(pady=10)
        
        PrimaryButton(btn_frame, text="OK", command=self.set_times).pack(side="left", padx=10)
        PrimaryButton(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=10)
    
    def set_times(self):
        try:
            # Convert to 24-hour format
            start = f"{self.start_hour.get()}:{self.start_min.get()} {self.start_ampm.get()}"
            end = f"{self.end_hour.get()}:{self.end_min.get()} {self.end_ampm.get()}"
            
            self.start_time = datetime.datetime.strptime(start, "%I:%M %p").strftime("%H:%M")
            self.end_time = datetime.datetime.strptime(end, "%I:%M %p").strftime("%H:%M")
            self.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid time selection!")

class CloudPublishUI(ctk.CTkFrame):
    def __init__(self, master, dropbox_client, jsonurlbin_client):
        super().__init__(master, fg_color=Colors.BACKGROUND)
        self.master = master
        self.dropbox_client = dropbox_client
        self.jsonurlbin_client = jsonurlbin_client
        self.file_path = None
        self.registration_password = None
        self.registration_times = None
        self.create_widgets()

    # [Keep all cryptographic methods the same...]
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
        
        padded_data = data + (16 - len(data) % 16) * chr(16 - len(data) % 16)
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
    

    def create_widgets(self):
        self.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # File Selection Section
        file_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        
        ctk.CTkLabel(file_frame, text="Select Encrypted Paper (.enc)", 
                    text_color=Colors.Texts.HEADERS).pack(side="left", padx=5)
        self.file_entry = ctk.CTkEntry(file_frame, width=300, 
                                     placeholder_text="Select a valid .enc file",
                                     fg_color=Colors.Inputs.BACKGROUND)
        self.file_entry.pack(side="left", padx=5, fill="x", expand=True)
        PrimaryButton(file_frame, text="Browse", command=self.select_file, width=80).pack(side="left", padx=5)
        
        # Exam Details Section
        details_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        details_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        
        # Subject and Date
        ctk.CTkLabel(details_frame, text="Subject Code:", text_color=Colors.Texts.HEADERS).grid(row=0, column=0, sticky="w")
        self.subject_entry = ctk.CTkEntry(details_frame, fg_color=Colors.Inputs.BACKGROUND)
        self.subject_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(details_frame, text="Exam Date:", text_color=Colors.Texts.HEADERS).grid(row=1, column=0, sticky="w")
        self.date_entry = ctk.CTkEntry(details_frame, fg_color=Colors.Inputs.BACKGROUND)
        self.date_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Registration Time
        self.time_button = PrimaryButton(details_frame, text="Set Registration Time", 
                                        command=self.set_registration_time)
        self.time_button.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Features Section
        features_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        features_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.negative_marking_var = ctk.IntVar()
        ctk.CTkCheckBox(features_frame, text="Enable Negative Marking",
                       variable=self.negative_marking_var,
                       command=self.toggle_negative_marking).pack(anchor="w")
        self.negative_marks_entry = ctk.CTkEntry(features_frame, 
                                                placeholder_text="Negative marks per wrong answer",
                                                fg_color=Colors.Inputs.BACKGROUND,
                                                state="disabled")
        self.negative_marks_entry.pack(fill="x", pady=5)
        
        self.shuffle_var = ctk.IntVar()
        ctk.CTkCheckBox(features_frame, text="Shuffle Questions", variable=self.shuffle_var).pack(anchor="w")
        
        # Filename Section
        filename_frame = ctk.CTkFrame(self, fg_color=Colors.BACKGROUND)
        filename_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(filename_frame, text="Cloud Filename:", text_color=Colors.Texts.HEADERS).pack(side="left", padx=5)
        self.filename_entry = ctk.CTkEntry(filename_frame, width=150, fg_color=Colors.Inputs.BACKGROUND)
        self.filename_entry.pack(side="left", padx=5)
        PrimaryButton(filename_frame, text="Generate", command=self.generate_filename, width=80).pack(side="left", padx=5)
        
        # Upload Button
        PrimaryButton(self, text="Upload to Cloud", command=self.upload_file).grid(row=4, column=0, columnspan=2, pady=10)
        
        self.columnconfigure(0, weight=1)

    def set_registration_time(self):
        time_dialog = TimePickerDialog(self)
        self.wait_window(time_dialog)
        if time_dialog.start_time and time_dialog.end_time:
            self.registration_times = (time_dialog.start_time, time_dialog.end_time)
            self.time_button.configure(text=f"Registration Time: {time_dialog.start_time} - {time_dialog.end_time}")

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Encrypted Files", "*.enc")])
        if file_path:
            pass_dialog = PasswordDialog(self.master, mode="decrypt")
            self.master.wait_window(pass_dialog)

            if pass_dialog.password:
                try:
                    with open(file_path, "r") as f:
                        encrypted_data = json.load(f)
                    
                    decrypted_data = self._decrypt_data(encrypted_data, pass_dialog.password)
                    if decrypted_data is None:
                        raise ValueError("Invalid password")
                        
                    # Auto-fill subject and date from decrypted data
                    paper_data = json.loads(decrypted_data)
                    self.subject_entry.delete(0, "end")
                    self.subject_entry.insert(0, paper_data.get("subject_code", ""))
                    self.date_entry.delete(0, "end")
                    self.date_entry.insert(0, paper_data.get("exam_date", ""))
                    
                    self.file_path = file_path
                    self.registration_password = pass_dialog.password
                    self.file_entry.delete(0, "end")
                    self.file_entry.insert(0, file_path)
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                    self.file_entry.delete(0, "end")
    
    def toggle_negative_marking(self):
        if self.negative_marking_var.get():
            self.negative_marks_entry.configure(state="normal")
        else:
            self.negative_marks_entry.configure(state="disabled")

    def generate_filename(self):
        random_filename = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        self.filename_entry.delete(0, "end")
        self.filename_entry.insert(0, random_filename)

    def limit_filename_length(self, event):
        if len(self.filename_entry.get()) > 8:
            self.filename_entry.delete(8, "end")

    def upload_file(self):
        if not all([self.file_path, self.filename_entry.get(), self.registration_times]):
            messagebox.showerror("Error", "Please complete all fields!")
            return
        
        try:
            filename = self.filename_entry.get() + ".enc"
            
            # Upload to Dropbox
            self.dropbox_client.upload_file(self.file_path, filename, self.registration_password)
            
            # Prepare paper details
            paper_details = {
                "subject_code": self.subject_entry.get(),
                "exam_date": self.date_entry.get(),
                "registration_time": f"{self.registration_times[0]}-{self.registration_times[1]}",
                "negative_marking": bool(self.negative_marking_var.get()),
                "negative_mark_value": float(self.negative_marks_entry.get()) if self.negative_marking_var.get() else 0,
                "shuffle_questions": bool(self.shuffle_var.get()),
                "upload_date": datetime.datetime.now().isoformat(),
                "enable": True,
                "results": []
            }
            
            # Store metadata
            self.jsonurlbin_client.store_paper_details(filename, paper_details)
            messagebox.showinfo("Success", "Paper uploaded successfully!")
            
        except Exception as e:
            messagebox.showerror("Upload Error", f"Failed to upload: {str(e)}")

app = ctk.CTk()
CloudPublishUI(app, None, None)
app.mainloop()