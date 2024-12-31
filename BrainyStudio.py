import os
import sys
import pygame
import pyperclip
import yaml
import json
import base64
import pickle
import time
import bcrypt
import webbrowser
import customtkinter as ctk
import dropbox
from tkinter import messagebox, filedialog
from datetime import datetime
from PIL import Image
from math import floor
from random import random
from typing import Tuple
from icecream import ic
from threading import Thread
from socket import create_connection
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError, BadInputError, InternalServerError
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pygments.styles.dracula import comment
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from textwrap import wrap


ic.configureOutput(prefix="DEBUG :", includeContext=True, contextAbsPath=True)


class DropboxBackend:

    def __init__(self, access_token: str, app_key: str, app_secret: str, root_path: str):
        self.dbx = dropbox.Dropbox(access_token, app_key=app_key, app_secret=app_secret)
        self.root_path = root_path

    def upload_file(self, local_path: str, dropbox_path: str):
        try:
            with open(local_path, "rb") as f:
                self.dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"))
                return True
        except FileNotFoundError:
            messagebox.showerror("Error", f"Local file '{local_path}' not found.")
            return False
        except ApiError as e:
            if e.error.is_path() and e.error.get_path():
                messagebox.showerror("Error", f"Conflict error: File '{dropbox_path}' already exists.")
                return False
            else:
                messagebox.showerror("Error", f"API error during upload")
                return False
        except Exception as e:
            messagebox.showerror("Something went wrong", f"An unexpected error occurred during file upload")
            return False


class EncryptionService:

    def __init__(self, data: dict | None, filepath: str, password: str) -> None:
        self.data = data
        self.filepath = filepath
        self.password = password
        ic(f"Encryption Service - initialised with filepath: {self.filepath}")
        ic(f"Input Data: {self.data}")
        ic(f"Using Password: {'x' * len(self.password)}")

    def decryptData(self) -> None:
        ic("Encryption Service - Starting Decryption Process.")
        with open(self.filepath, 'rb') as file:
            if not file:
                return None
            salt = file.readline().strip().decode()
            encrypted_data = file.read()
            ic(f"Reading salt: {salt}")
            ic(f"Reading encrypted data size: {len(encrypted_data)} bytes")
            file.close()

        key, _ = self.getKey(salt=salt)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        ic("Decryption successful. Data loaded successfully.")
        ic(f"Decrypted data: {self.data}")
        data = pickle.loads(decrypted_data)
        self.data = data
        return

    def encryptData(self) -> None:
        ic("Encryption Service - Starting Encryption Process.")
        key, salt = self.getKey()
        fernet = Fernet(key)
        records = pickle.dumps(self.data)
        encrypted_data = fernet.encrypt(records)

        with open(self.filepath, 'wb') as file:
            if file:
                file.write(salt.encode() + b'\n' + encrypted_data)
                ic("Encryption successful. Data written to file.")
                ic(f"Wrote salt: {salt} and encrypted data of size: {len(encrypted_data)} bytes")
                file.close()
            else:
                pass

    def getKey(self, salt=None):
        if salt is None:
            salt = os.urandom(16)
            ic(f"Generated new salt: {salt}")
        else:
            salt = base64.urlsafe_b64decode(salt)
            ic(f"Decoded salt from input: {salt}")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend()
        )

        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        ic('Derived encryption key successfully.')
        return key, base64.urlsafe_b64encode(salt).decode()

    @staticmethod
    def encrypt_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


class GeneratePDF:
    def __init__(self, title, subject_details, instructions, questions, enrollment_no, logo_path):
        self.title = title
        self.subject_details = subject_details
        self.instructions = instructions
        self.questions = questions
        self.enrollment_no = enrollment_no
        self.logo_path = logo_path

    def add_footer(self, pdf, page_num, width):
        pdf.setLineWidth(1)
        pdf.setStrokeColor(colors.HexColor("#C1C1C1"))
        pdf.line(50, 40, width - 50, 40)

        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.HexColor("#4A4A4A"))
        pdf.drawString(50, 25, f"Page {page_num}")

        pdf.drawRightString(width - 100, 25, "Generated by Brainy Studio")

        if self.logo_path:
            logo = ImageReader(self.logo_path)
            pdf.drawImage(logo, width - 90, 10, width=30, height=30, mask='auto')

        bookmark_title = f"Page {page_num}"
        pdf.bookmarkPage(bookmark_title)
        pdf.addOutlineEntry(bookmark_title, bookmark_title, level=0)

    def generate_pdf(self):
        pdf_file = get_resource_path(f"data\\{self.title}_{self.subject_details["subject_date"]}.pdf", force_get=True)
        pdf = canvas.Canvas(pdf_file, pagesize=A4)
        width, height = A4

        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.HexColor("#4A4A4A"))
        pdf.drawString(50, height - 20, f"Enrollment No: {self.enrollment_no}")

        pdf.bookmarkPage("TitlePage")
        pdf.addOutlineEntry("Enhanced Examination Paper", "TitlePage", level=0)
        pdf.setFont("Helvetica-Bold", 24)
        pdf.setFillColor(colors.HexColor("#2E3B55"))
        pdf.drawCentredString(width / 2, height - 50, self.title)

        pdf.setLineWidth(3)
        pdf.setStrokeColor(colors.HexColor("#4CAF50"))
        pdf.line(50, height - 80, width - 50, height - 80)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.HexColor("#2E3B55"))
        pdf.drawString(50, height - 110, f"Subject Code: {self.subject_details['subject_code']}")
        pdf.drawString(width - 250, height - 110, f"Date: {self.subject_details['subject_date']}")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, height - 130, f"Subject Name: {self.subject_details['subject_name']}")
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, height - 150, f"Time Duration: {self.subject_details['time_duration']}")
        pdf.drawString(width - 250, height - 150, f"Total Marks: {self.subject_details['total_marks']}")

        pdf.setLineWidth(1)
        pdf.setDash(3, 3)
        pdf.line(50, height - 160, width - 50, height - 160)
        pdf.setDash()

        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.HexColor("#2E3B55"))
        y_position = height - 180
        pdf.drawString(50, y_position, "Instructions:")

        y_position -= 15
        text_object = pdf.beginText(50, y_position)
        text_object.setFont("Helvetica", 10)
        text_object.setFillColor(colors.HexColor("#4A4A4A"))
        text_object.textLines(self.instructions)
        pdf.drawText(text_object)

        y_position = text_object.getY() - 20
        pdf.setLineWidth(1)
        pdf.setDash(3, 3)
        pdf.line(50, y_position, width - 50, y_position)
        pdf.setDash()

        page_num = 1
        question_start_y = y_position - 20

        for i, (question_text, marks, correct_option, options_list) in enumerate(self.questions):
            wrapped_question = wrap(question_text, width=85)
            question_height = len(wrapped_question) * 15
            options_height = len(options_list) * 25
            total_question_height = question_height + options_height + 40

            if question_start_y - total_question_height < 100:
                self.add_footer(pdf, page_num, width)
                pdf.showPage()
                page_num += 1
                question_start_y = height - 120

            max_text_width = width - 100
            wrapped_question = wrap(question_text, width=85)


            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColor(colors.HexColor("#2E3B55"))
            y_offset = 0
            for line in wrapped_question:
                pdf.drawString(50, question_start_y - y_offset, line)
                y_offset += 15
            question_start_y -= y_offset

            pdf.drawRightString(width - 50, question_start_y, f"Marks: {marks}")

            pdf.setFont("Helvetica", 11)
            option_y = question_start_y - 25

            for j, option_text in enumerate(options_list):
                pdf.setStrokeColor(colors.HexColor("#2E3B55"))
                pdf.circle(70, option_y, 4)

                if j == correct_option:
                    pdf.setFillColor(colors.HexColor("#333333"))
                    pdf.circle(70, option_y, 3, stroke=0, fill=1)
                    pdf.setFillColor(colors.HexColor("#000000"))

                pdf.setFillColor(colors.HexColor("#4A4A4A"))
                pdf.drawString(90, option_y - 4, f"{option_text}")
                option_y -= 25

            question_start_y = option_y - 20

        self.add_footer(pdf, page_num, width)
        pdf.save()


# utils methods


class AnimatedLabel(ctk.CTkLabel):
    def __init__(self, parent, texts, delay=100, erase_delay=1000, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.texts = texts
        self.delay = delay
        self.erase_delay = erase_delay
        self.current_text_index = 0
        self.current_char_index = 0
        self.typing = True
        self.animate_text()

    def animate_text(self):
        current_text = self.texts[self.current_text_index]

        if self.typing:
            if self.current_char_index < len(current_text):
                self.current_char_index += 1
                self.configure(text=current_text[:self.current_char_index])
                self.after(self.delay, self.animate_text)
            else:
                time.sleep(1)
                self.typing = False
                self.after(self.erase_delay, self.animate_text)

        else:
            if self.current_char_index > 0:
                self.current_char_index -= 1
                self.configure(text=current_text[:self.current_char_index])
                self.after(self.delay, self.animate_text)
            else:
                # Finished erasing, move to the next text and start typing again
                self.typing = True
                self.current_text_index = (self.current_text_index + 1) % len(self.texts)
                self.after(self.delay, self.animate_text)


def get_resource_path(resource_path: str, force_get: bool = False):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    filepath = os.path.join(base_path, resource_path)

    if force_get:
        return filepath

    if os.path.exists(filepath):
        return filepath

    return None




def center_window(parent: ctk.CTk, width: int, height: int, scale_factor: float = 1.0, variation: Tuple[int, int] = (0, 0)):
    screen_width = parent.winfo_screenwidth()
    screen_height = parent.winfo_screenheight()

    x = int(((screen_width/2) - (width/2)) * scale_factor)
    y = int(((screen_height/2) - (height/1.5)) * scale_factor)

    scaled_width = x + variation[0]
    scaled_height = y + variation[1]
    return f"{width}x{height}+{scaled_width}+{scaled_height}"


def play_sound(sound_type: str):
    if sound_type == "error":
        pygame.mixer.music.load(get_resource_path("assets\\tunes\\error-notify.mp3"))
    if sound_type == "success":
        pygame.mixer.music.load(get_resource_path("assets\\tunes\\success-notify.mp3"))
    pygame.mixer.music.play()


class LinkFrame:
    def __init__(self, master):
        self.master = master
        self.master.configure(fg_color="#ffffff")

        # Create the main frame for the links section
        self.link_frame = ctk.CTkFrame(self.master, fg_color="#F5F5DC", height=200)
        self.link_frame.pack(padx=10, pady=10, side="bottom", fill="x")
        self.link_frame.pack_propagate(False)

        self.transparent_frame = ctk.CTkFrame(self.link_frame, fg_color="transparent")
        self.transparent_frame.pack(padx=10, pady=10, anchor="center")

        self.title_label = ctk.CTkLabel(
            self.transparent_frame,
            text="Connect with Me",
            text_color="#4A232A",
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(padx=10, pady=10, anchor="center")

        self.github_button = ctk.CTkButton(
            self.transparent_frame,
            text="Visit My GitHub",
            text_color="#ffffff",
            fg_color="#333333",
            hover_color="#222222",
            font=("Arial", 14, "bold"),
            width=200,
            height=42,
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\github.png")), size=(30, 30)),
            command=self.open_github
        )
        self.github_button.pack(pady=20, padx=10, side="left", anchor="center")

        self.email_button = ctk.CTkButton(
            self.transparent_frame,
            text="Send an Email",
            text_color="#ffffff",
            fg_color="#0066CC",
            hover_color="#0057A3",
            font=("Arial", 14, "bold"),
            width=200,
            height=42,
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\gmail.png")),
                               size=(30, 30)),
            command=self.send_email
        )
        self.email_button.pack(pady=20, padx=10, side="left", anchor="center")

        self.linkedin_button = ctk.CTkButton(
            self.transparent_frame,
            text="Connect on LinkedIn",
            text_color="#ffffff",
            fg_color="#0077B5",
            hover_color="#005582",
            font=("Arial", 14, "bold"),
            width=200,
            height=42,
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\linkedin.png")), size=(30, 30)),
            command=self.open_linkedin
        )
        self.linkedin_button.pack(pady=20, padx=10, side="left", anchor="center")

    @staticmethod
    def open_github():
        webbrowser.open("https://github.com/AkshatBhatt-786")

    @staticmethod
    def open_linkedin():
        webbrowser.open("https://linkedin.com/in/akshat-bhatt-60a78a276")

    @staticmethod
    def send_email():
        email_address = "akshatbhatt0786@gmail.com"
        webbrowser.open(f"mailto:{email_address}")


class CloudRegisterPage(ctk.CTkFrame):
    def __init__(self, master, parent, **kwargs):
        super().__init__(master=master, **kwargs)
        self.configure(fg_color="#ffffff")
        self.master = master
        self.parent = parent
        self.header_frame = None
        self.content_frame = None
        self.filepath = self.parent.temp["export"]
        self.data = {}
        self.build()

    def build(self):
        if self.header_frame is None:
            self.header_frame = ctk.CTkFrame(
                self.master, fg_color="#F5F5DC", height=150
            )
            self.header_frame.pack(anchor="center", fill="x")
            self.header_frame.pack_propagate(False)

            self.title_label = ctk.CTkLabel(
                self.header_frame,
                text="Publish on CloudExam",
                text_color="#4A232A",
                font=("Arial", 24, "bold"),
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\cloud-code.png")),
                                   size=(30, 30)),
                padx=20,
                compound="right"
            )
            self.title_label.pack(padx=10, pady=10, side="left")

            self.separator = ctk.CTkFrame(
                self.header_frame,
                fg_color="#CD7F32",
                width=2, height=2)
            self.separator.pack(fill="y", padx=20, side="left")

            self.animation_label = AnimatedLabel(
                self.header_frame,
                texts=["BrainyStudio ~ Powered by Cloud Exam", "Publish Your Brainy Studio Paper on Cloud Exam Platform"], delay=100,
                text_color="#333333",
                font=ctk.CTkFont(family="Arial", weight="bold", size=28)
            )
            self.animation_label.pack(padx=20, pady=10, side="left")

            logo = ctk.CTkLabel(
                self.header_frame,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\images\\logo.png")),
                                   size=(80, 80)),
                text="BRAINY STUDIO", text_color="#333333", compound="top",
                font=ctk.CTkFont(family="Arial", size=18, weight="bold")
            )
            logo.pack(padx=10, anchor="center", side="right")

        if self.content_frame is None:
            self.content_frame = ctk.CTkFrame(
                self.master, fg_color="#D2B48C", height=400, corner_radius=0,
            )
            self.content_frame.pack(anchor="center", fill="x")
            self.content_frame.pack_propagate(False)

            encryption_service = EncryptionService(data=None, filepath=self.filepath, password="Dragon@Ocean72")
            encryption_service.decryptData()
            data = encryption_service.data
            headers = data["headers"]
            auth = data["authentication"]
            features = data["features"]
            questions = data["questions"]
            self.data = {"auth": auth, "headers": headers, "features": features, "questions": questions}

            if auth:
                auth_frame = ctk.CTkFrame(self.content_frame, width=400, height=400, fg_color="transparent")
                auth_frame.place(relx=0.5, rely=0.5, anchor="center")

                auth_title = ctk.CTkLabel(
                    auth_frame,
                    text="Secure Access Required",
                    text_color="#1A1A1A",
                    compound="top",
                    font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
                )
                auth_title.pack(pady=10, padx=10, anchor="center")

                password_label = ctk.CTkLabel(
                    auth_frame,
                    text="Password: ",
                    text_color="#1A1A1A",
                    compound="top",
                    font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
                )
                password_label.pack(padx=10, pady=10, side="left", anchor="center")

                password_entry = ctk.CTkEntry(
                    auth_frame,
                    fg_color="#F5F5DC",
                    text_color="#333333",
                    font=("Calibri", 14, "bold"),
                    border_color="#B87333",
                    border_width=2,
                    width=300,
                    height=32,
                    show="●"
                )
                password_entry.pack(padx=10, pady=10, side="left", anchor="center")

                authorise_btn = ctk.CTkButton(
                    auth_frame,
                    text="Authorize \u2192",
                    text_color="#ffffff",
                    fg_color="#0066CC",
                    hover_color="#0057A3",
                    font=("Arial", 14, "bold"),
                    width=200,
                    height=52,
                    corner_radius=10,
                    command=lambda: self.authenticate_user()
                )
                authorise_btn.pack(padx=10, pady=10, anchor="center")

            form_title = ctk.CTkLabel(
                self.content_frame,
                text="Cloud Exam File Registry Form",
                text_color="#1A1A1A",
                compound="top",
                font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
            )
            form_title.pack(pady=10, padx=10, anchor="center")

            ctk.CTkLabel(
                self.content_frame,
                text=f"{headers["exam_title"]}",
                text_color="#1A1A1A",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\file.png")), size=(30, 30)),
                compound="left",
                font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
            ).pack(padx=10, pady=10, anchor="center")

            time_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            time_frame.pack(padx=10, pady=10, anchor="center")

            time_label = ctk.CTkLabel(
                time_frame,
                text="Time (Minutes): ",
                text_color="#1A1A1A",
                compound="top",
                font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
            )
            time_label.pack(padx=10, pady=10, anchor="center", side="left")

            self.time_entry = ctk.CTkEntry(
                time_frame,
                fg_color="#F5F5DC",
                text_color="#333333",
                font=("Calibri", 14, "bold"),
                border_color="#B87333",
                border_width=2,
                width=60,
                height=32,
                justify="center"
            )
            self.time_entry.pack(padx=10, pady=10, anchor="center", side="left")

            passcode_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            passcode_frame.pack(padx=10, pady=10, anchor="center")

            passcode_label = ctk.CTkLabel(
                passcode_frame,
                text="PASSCODE: ",
                text_color="#1A1A1A",
                compound="top",
                font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
            )
            passcode_label.pack(padx=10, pady=10, anchor="center", side="left")

            self.passcode_entry = ctk.CTkEntry(
                passcode_frame,
                fg_color="#F5F5DC",
                text_color="#333333",
                font=("Calibri", 14, "bold"),
                border_color="#B87333",
                border_width=2,
                width=320,
                height=32,
                placeholder_text="Create Strong Passcode",
                show="●"
            )
            self.passcode_entry.pack(padx=10, pady=10, anchor="center", side="left")

            passcode_warning_label = ctk.CTkLabel(
                passcode_frame,
                text="Do not share your passcode.",
                text_color="red",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\triangle-warning.png")), size=(20, 20)),
                compound="left",
                font=ctk.CTkFont(family="Arial", size=12, weight="bold"), padx=10
            )
            passcode_warning_label.pack(padx=10, pady=(0, 10), anchor="w", side="left")

            access_code_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            access_code_frame.pack(padx=10, pady=10, anchor="center")

            access_code_label = ctk.CTkLabel(
                access_code_frame,
                text="ACCESS KEY: ",
                text_color="#1A1A1A",
                compound="top",
                font=ctk.CTkFont(family="Helvetica", size=16, weight="bold")
            )
            access_code_label.pack(padx=10, pady=10, anchor="center", side="left")

            self.access_code_entry = ctk.CTkEntry(
                access_code_frame,
                fg_color="#F5F5DC",
                text_color="#333333",
                font=("Calibri", 14, "bold"),
                border_color="#B87333",
                border_width=2,
                width=320,
                height=32,
                placeholder_text="Create Access Key",
                show="●"
            )
            self.access_code_entry.pack(padx=10, pady=10, anchor="center", side="left")

            access_code_info_label = ctk.CTkLabel(
                access_code_frame,
                text="Public Key: Shareable and visible to others.",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\info.png")),
                                   size=(20, 20)),
                compound="left",
                text_color="#4A4A4A",
                font=ctk.CTkFont(family="Arial", size=12, weight="normal"),
                anchor="w",
                padx=10
            )
            access_code_info_label.pack(padx=10, pady=(0, 10), anchor="w", side="left")

            register_btn = ctk.CTkButton(
                self.content_frame,
                text="PUBLISH NOW",
                text_color="#ffffff",
                fg_color="#0066CC",
                hover_color="#0057A3",
                font=("Arial", 14, "bold"),
                width=200,
                height=52,
                corner_radius=10,
                command=lambda: self.publish_on_dropbox()
            )
            register_btn.pack(padx=10, pady=10, anchor="center")


        link_frame = LinkFrame(self.master)

    def authenticate_user(self):
        pass

    def publish_on_dropbox(self):
        passcode_value = self.passcode_entry.get()
        access_code_value = self.access_code_entry.get()
        time_entry = self.time_entry.get()
        errors = []

        if passcode_value == "" or access_code_value == "" or time_entry == "":
            messagebox.showerror("All fields Required", "All the fields are compulsory to be filled!")
            return

        if not time_entry.isdigit():
            return

        if len(passcode_value) < 8:
            errors.append("Passcode must be at least 8 characters long.")
        if not any(char.isdigit() for char in passcode_value):
            errors.append("Passcode must contain at least one digit.")
        if not any(char.isupper() for char in passcode_value):
            errors.append("Passcode must contain at least one uppercase letter.")
        if not any(char.islower() for char in passcode_value):
            errors.append("Passcode must contain at least one lowercase letter.")
        if not any(char in "!@#$%^&*()_+[]{}|;:',.<>?/" for char in passcode_value):
            errors.append("Passcode must contain at least one special character.")

        if passcode_value == access_code_value:
            messagebox.showerror("Auth Error", "Passcode and Access-code Code cannot be Same!")
            return

        if errors:
            messagebox.showerror("Validation Errors", "\n".join(errors))
            return

        access_code = self.generate_access_code()
        hashed_passcode = EncryptionService.encrypt_password(passcode_value)
        current_timestamp = datetime.now()
        hashed_access_code = EncryptionService.encrypt_password(access_code_value)
        self.data["auth"] = {"access_code": access_code, "access_key": hashed_access_code, "passcode": hashed_passcode, "last-modified": current_timestamp}
        self.data["headers"]["time"] = time_entry

        encryption_service = EncryptionService(data=self.data, filepath=get_resource_path(f"data\\{access_code}.bin.enc", force_get=True), password="Dragon@Ocean87")
        encryption_service.encryptData()



        dbx_backend = DropboxBackend(self.parent.temp["config"]["access_token"], self.parent.temp["config"]["app_key"], self.parent.temp["config"]["app_secret"], "/cloud/")
        file_upload = dbx_backend.upload_file(get_resource_path(f"data\\{access_code}.bin.enc", force_get=True),
                                              f"/cloud/{access_code}.bin.enc")

        if file_upload:
            messagebox.showinfo(
                "File Successfully Uploaded to Dropbox",
                f"Your exam file has been published to Dropbox.\n\n"
                f"ACCESS CODE (Public Key) : {access_code}\n"
                f"ACCESS KEY  (Private Key): {access_code_value}\n\n"
                f"⚠ Keep your passcode private and do not share it with anyone."
            )

    @staticmethod
    def generate_access_code():
        characters = "123456789ABCDEFGHIJKLMNPQURSTVUWXYZ"
        access_code = ""

        for i in range(6):
            access_code += characters[floor(random() * len(characters))]

        return access_code


class EditPaperPage(ctk.CTkFrame):
    def __init__(self, master, parent, **kwargs):
        super().__init__(master=master, **kwargs)
        self.configure(fg_color="#ffffff")
        self.master = master
        self.parent = parent
        self.header_frame = None
        self.content_frame = None
        self.build()

    def build(self):
        if self.header_frame is None:
            self.header_frame = ctk.CTkFrame(
                self.master, fg_color="#F5F5DC", height=150
            )
            self.header_frame.pack(anchor="center", fill="x")
            self.header_frame.pack_propagate(False)

            self.title_label = ctk.CTkLabel(
                self.header_frame,
                text="Edit Paper",
                text_color="#4A232A",
                font=("Arial", 24, "bold"),
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\edit.png")), size=(30, 30)),
                padx=20,
                compound="right"
            )
            self.title_label.pack(padx=10, pady=10, side="left")

            self.separator = ctk.CTkFrame(
                self.header_frame,
                fg_color="#CD7F32",
                width=2, height=2)
            self.separator.pack(fill="y", padx=20, side="left")

            self.animation_label = AnimatedLabel(
                self.header_frame,
                texts=["Revise Your Paper, Powered by Brainy Studio", "Edit Your Brainy Studio Paper"], delay=100,
                text_color="#333333",
                font=ctk.CTkFont(family="Arial", weight="bold", size=28)
            )
            self.animation_label.pack(padx=20, pady=10, side="left")

            logo = ctk.CTkLabel(
                self.header_frame,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\images\\logo.png")), size=(80, 80)),
                text="BRAINY STUDIO", text_color="#333333", compound="top",
                font=ctk.CTkFont(family="Arial", size=18, weight="bold")
            )
            logo.pack(padx=10, anchor="center", side="right")

        if self.content_frame is None:
            self.content_frame = ctk.CTkFrame(
                self.master, fg_color="#D2B48C", height=400, corner_radius=0
            )
            self.content_frame.pack(anchor="center", fill="x")
            self.content_frame.pack_propagate(False)

            self.heading = ctk.CTkLabel(
                self.content_frame,
                text="Select A File",
                text_color="#4A232A",
                font=("Arial", 18, "bold")
            )
            self.heading.pack(padx=10, pady=10, anchor="center")

            self.export_frame = ctk.CTkFrame(self.content_frame, width=800, height=500, fg_color="#FFFFFF")
            self.export_frame.pack(padx=10, pady=10, anchor="center")
            self.export_frame.pack_propagate(False)

            self.export_btn = ctk.CTkButton(
                self.export_frame,
                text="Choose File",
                text_color="#ffffff",
                fg_color="#0066CC",
                hover_color="#0057A3",
                font=("Arial", 14, "bold"),
                width=200,
                height=52,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\selection.png")), size=(30, 30)), command=lambda: self.parent.edit_paper())
            self.export_btn.place(relx=0.5, rely=0.5, anchor="center")
            self.link_frame = LinkFrame(self.master)


class HomePage(ctk.CTkFrame):
    def __init__(self, master, parent, **kwargs):
        super().__init__(master=master, **kwargs)
        self.configure(fg_color="#ffffff")
        self.master = master
        self.parent = parent
        self.header_frame = None
        self.content_frame = None
        self.build()

    def build(self):
        if self.header_frame is None:
            self.header_frame = ctk.CTkFrame(
                self.master, fg_color="#F5F5DC", height=150
            )
            self.header_frame.pack(anchor="center", fill="x")
            self.header_frame.pack_propagate(False)

            self.title_label = ctk.CTkLabel(
                self.header_frame,
                text="Brainy Studio",
                text_color="#4A232A",
                font=("Arial", 24, "bold"),
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\images\\logo.png")), size=(80, 80)),
                padx=20,
                compound="right"
            )
            self.title_label.pack(padx=10, pady=10, side="left")

            self.separator = ctk.CTkFrame(
                self.header_frame,
                fg_color="#CD7F32",
                width=2, height=2)
            self.separator.pack(fill="y", padx=20, side="left")

            self.animation_label = AnimatedLabel(
                self.header_frame,
                texts=["Welcome to BrainyStudio", "Create Interactive Test Paper", "Powered by Cloud Exam", "Make Your Data Accessible Anytime, Anywhere", "Save and Share Instantly", "Start Exporting Now"], delay=100,
                text_color="#333333",
                font=ctk.CTkFont(family="Arial", weight="bold", size=28)
            )
            self.animation_label.pack(padx=20, pady=10, side="left")

        if self.content_frame is None:
            self.content_frame = ctk.CTkFrame(
                self.master, fg_color="#D2B48C", height=600, corner_radius=0
            )
            self.content_frame.pack(anchor="center", fill="x")
            self.content_frame.pack_propagate(False)
            self.heading = ctk.CTkLabel(
                self.content_frame,
                text="Explore Brainy Studio",
                text_color="#4A232A",
                font=("Arial", 18, "bold")
            )
            self.heading.pack(padx=10, pady=20, anchor="center")

            self.transparent_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            self.transparent_frame.place(relx=0.5, rely=0.5, anchor="center")

            self.create_paper_btn = ctk.CTkButton(
                self.transparent_frame,
                text="Create Paper",
                fg_color="#8B4513",
                hover_color="#6A2E1F",
                text_color="#F5F5DC",
                font=("Arial", 18, "bold"),
                width=180,
                height=180,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\add-document.png")),
                                   size=(60, 60)),
                compound="top",
                command=lambda: self.parent.display_content("create-exam")
            )
            self.create_paper_btn.pack(pady=20, padx=10, side="left", anchor="center")

            self.edit_paper_btn = ctk.CTkButton(
                self.transparent_frame,
                text="Edit Paper",
                fg_color="#8B4513",
                hover_color="#6A2E1F",
                text_color="#F5F5DC",
                font=("Arial", 18, "bold"),
                width=180,
                height=180,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\edit.png")),
                                   size=(60, 60)),
                compound="top",
                command=lambda: self.parent.display_content("edit-paper")
            )
            self.edit_paper_btn.pack(pady=20, padx=10, side="left", anchor="center")

            self.export_btn = ctk.CTkButton(
                self.transparent_frame,
                text="Export Now",
                fg_color="#8B4513",
                hover_color="#6A2E1F",
                text_color="#F5F5DC",
                font=("Arial", 18, "bold"),
                width=180,
                height=180,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\share.png")),
                                   size=(60, 60)),
                compound="top",
                command=lambda: self.parent.display_content("export-page"),
            )
            self.export_btn.pack(pady=20, padx=10, side="left", anchor="center")


class ExportPage(ctk.CTkFrame):
    def __init__(self, master, parent, **kwargs):
        super().__init__(master=master, **kwargs)
        self.configure(fg_color="#ffffff")
        self.master = master
        self.parent = parent
        self.header_frame = None
        self.content_frame = None
        self.build()


    def build(self):
        if self.header_frame is None:
            self.header_frame = ctk.CTkFrame(
                self.master, fg_color="#F5F5DC", height=150
            )
            self.header_frame.pack(anchor="center", fill="x")
            self.header_frame.pack_propagate(False)

            self.title_label = ctk.CTkLabel(
                self.header_frame,
                text="Export Options",
                text_color="#4A232A",
                font=("Arial", 24, "bold"),
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\share.png")), size=(30, 30)),
                padx=20,
                compound="right"
            )
            self.title_label.pack(padx=10, pady=10, side="left")

            self.separator = ctk.CTkFrame(
                self.header_frame,
                fg_color="#CD7F32",
                width=2, height=2)
            self.separator.pack(fill="y", padx=20, side="left")

            self.animation_label = AnimatedLabel(
                self.header_frame,
                texts=["Generate Professional PDFs", "Publish it on Cloud Exam", "Make Your Data Accessible Anytime, Anywhere", "Save and Share Instantly", "Start Exporting Now"], delay=100,
                text_color="#333333",
                font=ctk.CTkFont(family="Arial", weight="bold", size=28)
            )
            self.animation_label.pack(padx=20, pady=10, side="left")

            logo = ctk.CTkLabel(
                self.header_frame,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\images\\logo.png")), size=(80, 80)),
                text="BRAINY STUDIO", text_color="#333333", compound="top",
                font=ctk.CTkFont(family="Arial", size=18, weight="bold")
            )
            logo.pack(padx=10, anchor="center", side="right")

        if self.content_frame is None:
            self.content_frame = ctk.CTkFrame(
                self.master, fg_color="#D2B48C", height=400, corner_radius=0
            )
            self.content_frame.pack(anchor="center", fill="x")
            self.content_frame.pack_propagate(False)

            self.heading = ctk.CTkLabel(
                self.content_frame,
                text="Export Your Data",
                text_color="#4A232A",
                font=("Arial", 18, "bold")
            )
            self.heading.pack(padx=10, pady=10, anchor="center")

            self.export_frame = ctk.CTkFrame(self.content_frame, width=800, height=500, fg_color="#FFFFFF")
            self.export_frame.pack(padx=10, pady=10, anchor="center")
            self.export_frame.pack_propagate(False)

            self.export_btn = ctk.CTkButton(
                self.export_frame,
                text="Choose File",
                text_color="#ffffff",
                fg_color="#0066CC",
                hover_color="#0057A3",
                font=("Arial", 14, "bold"),
                width=200,
                height=52,
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\selection.png")), size=(30, 30)), command=lambda: self.ask_export_option())
            self.export_btn.place(relx=0.5, rely=0.5, anchor="center")
            self.link_frame = LinkFrame(self.master)

    def ask_export_option(self):
        self.filepath = filedialog.askopenfilename(defaultextension=".bin.enc", filetypes=[("brainy studio", ".bin.enc")])

        self.export_btn.destroy()

        self.option_frame = ctk.CTkFrame(self.export_frame, width=600, height=120, fg_color="#F5F5F5", corner_radius=10)
        self.option_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.option_frame.pack_propagate(False)

        self.filename_label = ctk.CTkEntry(
            self.option_frame,
            fg_color="#F5F5DC",
            text_color="#333333",
            font=("Calibri", 14, "bold"),
            border_color="#B87333",
            border_width=2,
            width=400,
            height=32,
        )
        self.filename_label.pack(padx=20, pady=10, anchor="center", fill="x")
        self.filename_label.insert(0, f"File: {self.filepath}")
        self.filename_label.configure(state="disabled")

        self.export_options = ctk.CTkComboBox(
            self.option_frame,
            values=["Export to PDF", "Publish it on Cloud Exam"],
            font=ctk.CTkFont(family="Calibri", size=14),
            dropdown_font=ctk.CTkFont(family="Calibri", size=14),
            fg_color="#F5DEB3",
            text_color="#4A232A",
            button_color="#D4A373",
            button_hover_color="#8B4513",
            dropdown_fg_color="#DEB887",
            dropdown_text_color="#4A232A",
            dropdown_hover_color="#D4A373",
            border_color="#B87333",
            height=32,
            width=300
        )
        self.export_options.pack(padx=20, anchor="center", side="left")
        self.export_options.set("Export to PDF")

        export_btn = ctk.CTkButton(
            self.option_frame,
            text="Export \u2192",
            text_color="#ffffff",
            fg_color="#0066CC",
            hover_color="#0057A3",
            font=("Arial", 14, "bold"),
            width=200,
            height=52,
            corner_radius=10,
            command=lambda: self.user_export_selection()
        )
        export_btn.pack(padx=20, side="right", anchor="center")

    def user_export_selection(self):
        user = self.export_options.get()
        if user.lower() == "export to pdf":
            self._generate_pdf()
        if user.lower() == "publish it on cloud exam":
            self._publish_on_cloud_exam()
        return

    def _publish_on_cloud_exam(self):
        self.parent.temp["export"] = self.filepath
        self.parent.display_content("publish-content")
        return

    def _generate_pdf(self):
        service = EncryptionService(data=None, filepath=self.filepath, password="Dragon@Ocean72")
        service.decryptData()
        data = service.data
        headers = data["headers"]
        questions = data["questions"]

        subject_details = {
            "subject_name": headers["subject_name"],
            "total_marks": headers["total_marks"],
            "subject_code": headers["subject_code"],
            "time_duration": headers["time"],
            "subject_date": headers["date_of_exam"]
        }

        instructions = f"""
• The duration of this exam is [{headers["time"]}] minutes.
• This is an open book/closed book/restricted open book exam. The following materials and provisions are permitted:
• Insert as necessary (be specific and clear)
• There are {len(questions)} questions in this exam and will be presented one all at once.
• Each question is worth the different marks.
• The examination is worth {headers["total_marks"]}% of the marks available in this subject. 
• The contribution each question makes to the total examination mark is indicated in points or as a percentage.
• During this exam you will/won’t be permitted to review previous questions.
"""

        formatted_questions = []
        number_format = {
            "A": 0,
            "B": 1,
            "C": 2,
            "D": 3
        }

        for i in questions.keys():
            option_entries = []
            options = questions[i].get("options")
            for j in options.keys():
                option_entries.append(options.get(j))
            answer = questions[i].get("answer")
            question = (
                questions[i].get("question"),
                questions[i].get("marks"), number_format.get(answer),
                option_entries
            )
            formatted_questions.append(question)

        enrollment_no = "____________"
        logo_path = get_resource_path("assets\\images\\logo.png")

        pdf_generator = GeneratePDF(
            title=headers["exam_title"],
            subject_details=subject_details,
            instructions=instructions,
            questions=formatted_questions,
            enrollment_no=enrollment_no,
            logo_path=logo_path
        )

        pdf_generator.generate_pdf()

        pdf_file = get_resource_path(f"data\\{headers["exam_title"]}_{subject_details["subject_date"]}.pdf", force_get=True)
        if messagebox.askyesno("PDF Generated", f"The PDF has been saved at:\n\n{pdf_file}\n\nPreview it now?"):
            webbrowser.open(pdf_file)
        self.parent.display_content("export-page")
        return


class DeveloperPage(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master=master, **kwargs)
        self.configure(fg_color="#ffffff")
        self.master = master

        self.header_frame = ctk.CTkFrame(
            self.master, fg_color="#F5F5DC", height=150
        )
        self.header_frame.pack(anchor="center", fill="x")
        self.header_frame.pack_propagate(False)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="About The Developer",
            text_color="#4A232A",
            font=("Arial", 24, "bold"),
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\python.png")), size=(30, 30)),
            padx=20,
            compound="right"
        )
        self.title_label.pack(padx=10, pady=10, side="left")

        self.separator = ctk.CTkFrame(
            self.header_frame,
            fg_color="#CD7F32",
            width=2, height=2)
        self.separator.pack(fill="y", padx=20, side="left")

        self.animation_label = AnimatedLabel(
            self.header_frame, ["AKSHAT BHATT", "CONNECT WITH ME ON GITHUB & LINKEDIN", "BUILT WITH THE POWER OF PYTHON", "STAY UPDATED WITH THE LATEST FEATURES", "THANK YOU FOR UTILIZING THIS TOOL!"], delay=100,
            text_color="#333333",
            font=ctk.CTkFont(family="Arial", weight="bold", size=28)
        )
        self.animation_label.pack(padx=20, pady=10, side="left")

        logo = ctk.CTkLabel(
            self.header_frame,
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\images\\logo.png")), size=(80, 80)),
            text="BRAINY STUDIO", text_color="#333333", compound="top",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold")
        )
        logo.pack(padx=10, anchor="center", side="right")

        self.content_frame = ctk.CTkFrame(
            self.master, fg_color="#D2B48C", height=400, corner_radius=0
        )
        self.content_frame.pack(anchor="center", fill="x")
        self.content_frame.pack_propagate(False)

        self.heading = ctk.CTkLabel(
            self.content_frame,
            text="The Vision Behind This Software",
            text_color="#4A232A",
            font=("Arial", 18, "bold")
        )
        self.heading.pack(padx=10, pady=10, anchor="center")

        self.description_text = ctk.CTkTextbox(
            self.content_frame,
            wrap="word",
            fg_color="#F5F5DC",
            text_color="#333333",
            font=("Calibri", 16, "bold"),
            border_color="#B87333",
            border_width=2,
            height=400
        )
        self.description_text.pack(padx=20, pady=10, anchor="w", fill="both")

        self.description_text.insert(
            "1.0",  # Start inserting at the beginning of the TextBox
            (
                "As a final-year Diploma IT student at SIR BPTI College, "
                "under Gujarat Technological University (GTU), I encountered a pivotal moment "
                "when GTU introduced the Diploma to Degree Common Entrance Test (DDCET)—a crucial exam "
                "for students aspiring to continue their education. This sparked an idea during a late-night "
                "brainstorming session:\n\n"
                "'What if there was a seamless way to empower both students and teachers with advanced tools for online examinations?'\n\n"
                "Driven by this thought, I developed two innovative solutions:\n\n"
                "1. Cloud Exam Software – A platform for students to take online exams effortlessly, including MCQs, True/False, and more.\n"
                "2. Brainy Studio Software – A professional-grade tool designed for teachers and organizations to easily create, manage, and publish exam papers.\n\n"
                "With these tools, educators can upload their exam papers to a secure cloud server, making them accessible to students and other authorized users through unique access codes and passwords.\n\n"
                "My mission was clear:\n"
                "- To simplify the exam process for educators.\n"
                "- To empower students with easy-to-use, reliable tools.\n"
                "- To promote innovation in education through technology.\n\n"
                "These solutions are not just products; they represent a vision to streamline the examination process, foster a culture of digital readiness, "
                "and make education accessible and efficient for everyone."
            )
        )
        self.description_text.configure(state="disabled")


        self.link_frame = LinkFrame(self.master)


class TagDialog(ctk.CTkToplevel):

    def __init__(self, parent, title, text):
        super().__init__(parent)
        self.title(title)
        self.overrideredirect(True)
        self.geometry(center_window(parent, 400, 200, parent._get_window_scaling(), (0, 50)))

        self.configure(fg_color="#FAEBD7")
        self.attributes("-topmost", True)

        self.label = ctk.CTkLabel(self, text=text, font=ctk.CTkFont(family="Calibri", size=14),
                                  text_color="#4B0030")
        self.label.pack(pady=20)

        self.entry = ctk.CTkEntry(self,
                                  fg_color="#FAF0E6",
                                  text_color="#00695C",
                                  border_color="#B2DFDB")
        self.entry.pack(pady=10, padx=20, fill="x")

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.submit_btn = ctk.CTkButton(self.btn_frame, text="Add",
                                        fg_color="#00BCD4",
                                        hover_color="#0097A7",
                                        text_color="#FFFFFF",
                                        font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                                        command=self.submit, width=120, height=36, border_width=2)
        self.submit_btn.pack(side="left", padx=5)

        self.cancel_btn = ctk.CTkButton(self.btn_frame, text="Cancel",
                                        fg_color="#D32F2F",
                                        hover_color="#C62828",
                                        text_color="#FFFFFF",
                                        font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                                        command=self.destroy, width=120, height=36, border_width=2)
        self.cancel_btn.pack(side="right", padx=5)

        self.result = None
        self.entry.focus()

    def submit(self):
        self.result = self.entry.get()
        self.destroy()

    def get_input(self):
        self.wait_window()
        return self.result


class App(ctk.CTk):

    def __init__(self):
        super().__init__()
        self._windows_set_titlebar_color("light")
        self._icon_path = get_resource_path("icon.ico")
        if self._icon_path:
            self.iconbitmap(self._icon_path)
        self.title("Get started with BrainyStudio")
        self.geometry(center_window(self, 1400, 600, self._get_window_scaling(), (0, 50)))
        self.running = True
        self.isConnected = self.checkNetwork()
        # sidebar configurations
        self.sidebar, self.name_frame, self.icon_frame, self.frame = None, None, None, None
        self.message_box = None
        self.start_pos = 0
        self.end_pos = -0.2
        self.in_start_pos = True
        self.pos = self.start_pos
        self.start_pos = self.start_pos + 0.02
        self.width = abs(self.start_pos - self.end_pos)
        self.halfway_pos = ((self.start_pos + self.end_pos) / 2) - 0.06
        # API Configurations
        self.bind_all('<Control-i>', self.show_api_configurations)
        self.bind_all('<Control-j>', self.clearFrame)
        self.dbx_frame = None
        self.btn_frame = None
        # Create Exam configuration
        self.count = 0
        self.temp = {"workspace": {}, "export": None, "config": {}}
        self.tags = ["None"]
        self.questions = {}
        self.loadApiConfigurations()

    def build(self):
        self.configure(fg_color="#E5D3FF")
        if self.frame is None:
            self.frame = ctk.CTkFrame(
                self, fg_color="#FFFFFF",
                border_color="#7E57C2",
                border_width=2, corner_radius=10
            )
            self.frame.place(relx=0.08, rely=0.09, relwidth=0.9, relheight=0.9)

        if self.sidebar is None:
            self.sidebar = ctk.CTkFrame(
                self, fg_color="#B39DDB",
                border_color="#7E57C2",
                border_width=2, corner_radius=10
            )
            self.sidebar.place(relx=self.start_pos, rely=0.14, relwidth=self.width, relheight=0.8)
            self.sidebar.columnconfigure((0, 1), weight=1)
            self.sidebar.rowconfigure(0, weight=1)

            if self.name_frame is None:
                self.name_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="#E1F5FE", corner_radius=8, width=140,
                                                         scrollbar_fg_color="#E1F5FE", scrollbar_button_color="#E1F5FE",
                                                         scrollbar_button_hover_color="#E1F5FE")
                self.name_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
                # self.name_frame.pack_propagate(False)
                self.name_frame.grid_propagate(flag=False)

                logo = ctk.CTkLabel(
                    self.name_frame, image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\images\\logo.png")), size=(50, 50)),
                    text="BRAINY STUDIO", text_color="#333333", compound="top"
                )
                logo.pack(padx=10, pady=10, anchor="center", side="top")

                nav_dashboard_btn = ctk.CTkButton(
                    self.name_frame, text="Dashboard  ", image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\home.png")), size=(20, 20)),
                    fg_color="#E1F5FE", text_color="#4A4A4A",
                    hover_color="#BBDEFB", corner_radius=8, height=32, width=180,
                    font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                    command=self.display_content("home-page")
                )
                nav_dashboard_btn.pack(padx=10, pady=10, anchor="center", side="top")

                create_paper_btn = ctk.CTkButton(
                    self.name_frame, text="Create Paper",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\add-document.png")),
                                       size=(20, 20)),
                    fg_color="#E1F5FE", text_color="#4A4A4A",
                    hover_color="#BBDEFB", corner_radius=8, height=32, width=180,
                    font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                    command=lambda: self.display_content("create-exam")
                )
                create_paper_btn.pack(padx=10, pady=10, anchor="center", side="top")

                edit_paper_btn = ctk.CTkButton(
                    self.name_frame, text="Edit Paper    ",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\edit.png")),
                                       size=(20, 20)),
                    fg_color="#E1F5FE", text_color="#4A4A4A",
                    hover_color="#BBDEFB", corner_radius=8, height=32, width=180,
                    font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                    command=lambda: self.display_content("edit-paper")
                )
                edit_paper_btn.pack(padx=10, pady=10, anchor="center", side="top")

                export_btn = ctk.CTkButton(
                    self.name_frame, text="Export          ",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\share.png")),
                                       size=(20, 20)),
                    fg_color="#E1F5FE", text_color="#4A4A4A",
                    hover_color="#BBDEFB", corner_radius=8, height=32, width=180,
                    font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                    command=lambda: self.display_content("export-page")
                )
                export_btn.pack(padx=10, pady=10, anchor="center", side="top")


                info_btn = ctk.CTkButton(
                    self.name_frame, text="About Us     ",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\info.png")),
                                       size=(20, 20)),
                    fg_color="#E1F5FE", text_color="#4A4A4A",
                    hover_color="#BBDEFB", corner_radius=8, height=32, width=180,
                    font=ctk.CTkFont(family="Calibri", size=16, weight="bold"),
                    command=lambda: self.display_content("info-page")
                )
                info_btn.pack(padx=10, pady=10, anchor="center", side="top")

            if self.icon_frame is None:
                self.icon_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="#C4E4E7", corner_radius=8, width=60,
                                                         scrollbar_fg_color="#C4E4E7", scrollbar_button_color="#C3E4E7",
                                                         scrollbar_button_hover_color="#C3E4E7")
                self.icon_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
                self.icon_frame.pack_propagate(False)
                self.icon_frame.grid_propagate(flag=False)

                self.toggle_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\menu-burger.png")), size=(25, 25)), width=20, height=20, command=self.animate)
                self.toggle_btn.grid(row=0, column=0, pady=20, padx=5, sticky="nsew")

                self.dashboard_nav_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\home.png")),
                                       size=(20, 20)), width=20, height=20,
                    command=lambda: self.display_content("home-page"))
                self.dashboard_nav_btn.grid(row=1, column=0, pady=20, padx=5, sticky="nsew")

                self.create_paper_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\add-document.png")),
                                       size=(20, 20)), width=20, height=20, command=lambda: self.display_content("create-exam"))
                self.create_paper_btn.grid(row=2, column=0, pady=20, padx=5, sticky="nsew")

                self.edit_paper_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\edit.png")),
                                       size=(20, 20)), width=20, height=20, command=lambda: self.display_content("edit-paper"))
                self.edit_paper_btn.grid(row=3, column=0, pady=20, padx=5, sticky="nsew")

                self.export_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\share.png")),
                                       size=(20, 20)), width=20, height=20, command=lambda: self.display_content("export-page"))
                self.export_btn.grid(row=5, column=0, pady=20, padx=5, sticky="nsew")

                self.info_btn = ctk.CTkButton(
                    self.icon_frame, fg_color="#C4E4E7", text_color="#4A4A4A",
                    hover_color="#A8DADC", corner_radius=18, text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\info.png")),
                                       size=(25, 25)), width=20, height=20, command=lambda: self.display_content("info-page"))
                self.info_btn.grid(row=7, column=0, pady=20, padx=5, sticky="nsew")

        self.display_content("home-page")

    def showMessageBox(self):
        if self.message_box is None:
            self.message_box = ctk.CTkFrame(
                self, fg_color="#FDEDEC",
                border_color="#E74C3C",
                border_width=2, height=40
            )
            self.message_box.pack_propagate(False)
            self.message_box.pack(padx=10, pady=10, anchor="center", fill="x")
            if self.message_box is not None:
                self.message_title = ctk.CTkLabel(
                    self.message_box,
                    text_color="#FFFFFF",
                    text="",
                    fg_color="#FDEDEC",
                    image=None
                )
                self.message_title.pack(side="left", fill="both")

                self.message_desc = ctk.CTkLabel(
                    self.message_box,
                    text_color="#212121",
                    text="",
                    fg_color="transparent"
                )
                self.message_desc.pack(padx=10, pady=10, side="left")

                self.close_btn = ctk.CTkButton(
                    self.message_box,
                    text="",
                    image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\cross.png")), size=(10, 10)),
                    width=10, height=10,
                    fg_color="#FDEDEC",
                    hover_color="#FDEDEC",
                    border_color="#FDEDEC",
                    border_width=2, corner_radius=50,
                    command=self.onMessageboxClose
                )
                self.close_btn.pack(padx=10, pady=10, side="right")

    def loadApiConfigurations(self):
        config_file_path = get_resource_path("data\\config.json")
        if config_file_path:
            with open(config_file_path, "r") as f:
                data = json.load(f)
                self.temp["config"] = data

    def clearFrame(self, event=None):
        for widget in self.frame.winfo_children():
            if widget:
                widget.destroy()
        if self.dbx_frame:
            self.dbx_frame = None

    def onMessageboxClose(self):
        if self.message_box:
            self.message_box.pack_forget()
        self.message_box = None

    def animate(self):
        if self.in_start_pos:
            self.animate_to(self.halfway_pos)
        else:
            self.animate_to(self.start_pos)

    def animate_to(self, target_pos):
        if abs(self.pos - target_pos) > 0.008:
            step = -0.008 if self.pos > target_pos else 0.008
            self.pos += step
            self.sidebar.place(relx=self.pos, rely=0.14, relwidth=self.width, relheight=0.8)
            self.sidebar.after(10, self.animate_to, target_pos)
        else:
            self.pos = target_pos
            self.sidebar.place(relx=self.pos, rely=0.14, relwidth=self.width, relheight=0.8)
            self.in_start_pos = self.pos == self.start_pos

    def display_content(self, content_type):
        for widget in self.frame.winfo_children():
            widget.destroy()

        if content_type == "api-configurations":
            self.show_api_configurations()
        if content_type == "create-exam":
            self.show_create_exam_view()
        if content_type == "info-page":
            self.show_info_page()
        if content_type == "edit-paper":
            self.redirect_to_edit_page()
        if content_type == "export-page":
            self.redirect_to_export_page()
        if content_type == "publish-content":
            self.redirect_to_publish_cloud_exam()
        if content_type == "home-page":
            self.redirect_to_home_page()

    def redirect_to_home_page(self):
        home_page = HomePage(master=self.frame, parent=self)
        home_page.place(rely=0.5, relx=0.5, anchor="center")

    def redirect_to_publish_cloud_exam(self):
        self.publishFrame = CloudRegisterPage(master=self.frame, parent=self)
        self.publishFrame.place(relx=0.5, rely=0.5, anchor="center")

    def redirect_to_export_page(self):
        self.export_page = ExportPage(master=self.frame, parent=self)
        self.export_page.place(relx=0.5, rely=0.5, anchor="center")

    def show_info_page(self):
        if self.frame:
            frame = DeveloperPage(master=self.frame, height=800)
            frame.pack(padx=25, pady=10, anchor="center", fill="both")

    def show_create_exam_view(self):

        self.header_frame = ctk.CTkFrame(self.frame, fg_color="#F5F5DC", corner_radius=0)
        self.header_frame.pack(padx=25, pady=10, anchor="center", fill="x")

        self.symbols_frame = ctk.CTkScrollableFrame(
            self.header_frame, fg_color="#C8C8A9",
            corner_radius=0, width=600,
            scrollbar_fg_color="#C8C8A9",
            scrollbar_button_color="#6A5D4D",
            scrollbar_button_hover_color="#4A232A"
        )
        self.symbols_frame.pack(side="left")

        self.create_symbols_frame()

        self.marking_frame = ctk.CTkFrame(
            self.header_frame,
            fg_color="#D2B48C",
            corner_radius=0, width=200
        )
        self.marking_frame.pack(fill="y", side="left")
        self.marking_frame.pack_propagate(False)

        self.marking_label = ctk.CTkLabel(
            self.marking_frame,
            text="Marking Options",
            text_color="#4A232A",
            font=("Arial", 14, "bold")
        )
        self.marking_label.pack(padx=10, pady=5, anchor="w")

        self.separator = ctk.CTkFrame(self.marking_frame, fg_color="#CD7F32", height=2)
        self.separator.pack(fill="x", pady=10)

        self.allow_negative_marking_chb = ctk.CTkCheckBox(
            self.marking_frame,
            text="Negative Marking",
            fg_color="#F5F5DC",
            border_color="#CD7F32",
            checkmark_color="#556B2F",
            text_color="#333333",
            hover_color="#DAA520"
        )
        self.allow_negative_marking_chb.pack(padx=10, pady=5, anchor="w")

        self.enable_time_limit_chb = ctk.CTkCheckBox(
            self.marking_frame,
            text="Enable Time Limit",
            fg_color="#F5F5DC",
            border_color="#CD7F32",
            checkmark_color="#556B2F",
            text_color="#333333",
            hover_color="#DAA520"
        )
        self.enable_time_limit_chb.pack(padx=10, pady=5, anchor="w")

        self.shuffle_questions_chb = ctk.CTkCheckBox(
            self.marking_frame,
            text="Shuffle Questions",
            fg_color="#F5F5DC",
            border_color="#CD7F32",
            checkmark_color="#556B2F",
            text_color="#333333",
            hover_color="#DAA520"
        )
        self.shuffle_questions_chb.pack(padx=10, pady=5, anchor="w")

        self.action_btn_frame = ctk.CTkFrame(self.header_frame,
                                             fg_color="#D2B48C",
                                             corner_radius=0, width=200)
        self.action_btn_frame.pack(fill="y", side="left")
        self.action_btn_frame.pack_propagate(False)

        self.separator = ctk.CTkFrame(self.action_btn_frame, fg_color="#CD7F32", width=2, height=2)
        self.separator.pack(fill="y", padx=10, side="left")

        self.grading_label = ctk.CTkLabel(
            self.action_btn_frame,
            text="Grading System",
            text_color="#4A232A",
            font=("Arial", 14, "bold")
        )
        self.grading_label.pack(padx=10, pady=5, anchor="w")

        self.separator = ctk.CTkFrame(
            self.action_btn_frame, fg_color="#CD7F32",
            height=2
        )
        self.separator.pack(fill="x", pady=10)

        self.grading_options = ctk.CTkComboBox(
            self.action_btn_frame,
            values=["Percentage", "Points-based", "Pass/Fail"],
            fg_color="#F5DEB3",
            text_color="#4A232A",
            button_color="#D4A373",
            button_hover_color="#8B4513",
            dropdown_fg_color="#DEB887",
            dropdown_text_color="#4A232A",
            dropdown_hover_color="#D4A373",
            border_color="#B87333",
            width=200
        )
        self.grading_options.set("Percentage")
        self.grading_options.pack(padx=10, pady=5)

        self.difficulty_label = ctk.CTkLabel(
            self.action_btn_frame,
            text="Difficulty Level",
            text_color="#4A232A",
            font=("Calibri", 14, "bold")
        )
        self.difficulty_label.pack(padx=10, pady=5, anchor="w")

        self.difficulty_level = ctk.CTkComboBox(
            self.action_btn_frame,
            values=["Easy", "Medium", "Hard"],
            fg_color="#F5DEB3",
            text_color="#4A232A",
            button_color="#D4A373",
            button_hover_color="#8B4513",
            dropdown_fg_color="#DEB887",
            dropdown_text_color="#4A232A",
            dropdown_hover_color="#D4A373",
            border_color="#B87333",
            width=200
        )
        self.difficulty_level.set("Easy")
        self.difficulty_level.pack(padx=10, pady=5)

        self.action_btn_frame2 = ctk.CTkFrame(
            self.header_frame, fg_color="#D2B48C",
            corner_radius=0, width=200
        )
        self.action_btn_frame2.pack(fill="both", side="left", expand=True)
        self.action_btn_frame2.pack_propagate(False)

        self.separator = ctk.CTkFrame(
            self.action_btn_frame2, fg_color="#CD7F32",
            width=2, height=2)
        self.separator.pack(fill="y", padx=10, side="left")

        self.exam_mode_label = ctk.CTkLabel(
            self.action_btn_frame2,
            text="Exam Mode",
            text_color="#4A232A",
            font=("Arial", 14, "bold")
        )
        self.exam_mode_label.pack(padx=10, pady=5, anchor="w")

        self.separator = ctk.CTkFrame(self.action_btn_frame2, fg_color="#CD7F32", height=2)
        self.separator.pack(fill="x", pady=10)
        self.exam_mode_var = ctk.StringVar(value="Exam Mode")

        self.practice_mode_rb = ctk.CTkRadioButton(
            self.action_btn_frame2,
            text="Practice Mode",
            variable=self.exam_mode_var,
            value="Practice Mode",
            text_color="#4A232A",
            fg_color="#F5DEB3",
            border_color="#B87333",
            hover_color="#D4A373"
        )
        self.practice_mode_rb.pack(padx=10, pady=5, anchor="w")

        self.exam_mode_rb = ctk.CTkRadioButton(
            self.action_btn_frame2,
            text="Exam Mode",
            variable=self.exam_mode_var,
            value="Exam Mode",
            text_color="#4A232A",
            fg_color="#F5DEB3",
            border_color="#B87333",
            hover_color="#D4A373"
        )
        self.exam_mode_rb.pack(padx=10, pady=5, anchor="w")

        self.submit_button = ctk.CTkButton(
            self.action_btn_frame2,
            text="SAVE",
            image=ctk.CTkImage(Image.open(get_resource_path("assets\\symbols\\diskette.png")), size=(30, 30)),
            fg_color="#8B4513",
            hover_color="#6A2E1F",
            text_color="#F5F5DC",
            compound="left",
            width=200,
            height=50,
            command=lambda: self.saving_new_paper_process()
        )
        self.submit_button.pack(padx=10, pady=10)

        self.workspace_frame = ctk.CTkScrollableFrame(
            self.frame, fg_color="#F5F5DC"
            , border_color="#333333",
            border_width=0, corner_radius=10,
            scrollbar_fg_color="#F5F5DC",
            scrollbar_button_color="#F5F5DC",
            scrollbar_button_hover_color="#F5F5DC"
        )
        self.workspace_frame.pack(padx=25, pady=10, anchor="center", fill="both", expand=True)

        self.create_digital_workspace()

    def create_digital_workspace(self):
        if self.workspace_frame:
            self.temp["workspace"] = {}
            self.tags = ["None"]
            self.questions = {}
            self.count = 0
            self.detail_frame = ctk.CTkFrame(
                self.workspace_frame, border_color="#B87333", border_width=2,
                fg_color="#F5F5DC", corner_radius=0, width=200, height=400
            )
            self.detail_frame.pack(padx=10, pady=10, fill="x", anchor="center")
            self.detail_frame.pack_propagate(False)

            self.title_entry = ctk.CTkEntry(
                self.detail_frame, placeholder_text="Exam Title",
                height=60, font=ctk.CTkFont(family="Arial", size=32, weight="bold"),
                border_color="#F5F5DC", justify="center",
                fg_color="#F5F5DC",
                text_color="#333333"
            )
            self.title_entry.pack(padx=10, pady=10, anchor="center", fill="x")

            self.subject_frame = ctk.CTkFrame(
                self.detail_frame, fg_color="#F5F5DC", corner_radius=0, width=200, height=400
            )
            self.subject_frame.pack(padx=10, pady=10, fill="x", anchor="center")

            self.subject_code_label = ctk.CTkLabel(
                self.subject_frame,
                text="Subject Code: ",
                text_color="#333333",
                font=("Arial", 14, "bold")
            )
            self.subject_code_label.pack(pady=5, side="left")

            self.subject_code = ctk.CTkEntry(
                self.subject_frame, placeholder_text="Enter Subject Code",
                height=40, font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                border_color="#B87333",
                border_width=2,
                fg_color="#F5F5DC",
                text_color="#333333", width=200
            )
            self.subject_code.pack(padx=5, pady=10, side="left")

            self.exam_date = ctk.CTkEntry(
                self.subject_frame, placeholder_text="DD | MM | YYYY",
                height=40, font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                border_color="#B87333",
                border_width=2,
                fg_color="#F5F5DC",
                text_color="#333333",
                width=200
            )
            self.exam_date.pack(padx=10, pady=10, side="right")

            self.exam_date_label = ctk.CTkLabel(
                self.subject_frame,
                text="Date: ",
                text_color="#4A232A",
                font=("Arial", 14, "bold")
            )
            self.exam_date_label.pack(pady=5, side="right")

            self.subject_frame2 = ctk.CTkFrame(
                self.detail_frame, fg_color="#F5F5DC",
                corner_radius=0, width=200, height=400
            )
            self.subject_frame2.pack(padx=10, pady=10, fill="x", anchor="center")

            self.subject_name_label = ctk.CTkLabel(
                self.subject_frame2,
                text="Subject Name: ",
                text_color="#4A232A",
                font=("Arial", 14, "bold")
            )
            self.subject_name_label.pack(pady=5, side="left")

            self.subject_name = ctk.CTkEntry(
                self.subject_frame2, placeholder_text="Enter Subject Name",
                height=40, font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                border_color="#B87333",
                border_width=2,
                fg_color="#F5F5DC",
                text_color="#333333",
                width=600
            )
            self.subject_name.pack(pady=10, side="left")

            self.timings_marks_frame = ctk.CTkFrame(
                self.detail_frame, fg_color="#F5F5DC", corner_radius=0, width=200, height=400
            )
            self.timings_marks_frame.pack(padx=10, pady=10, fill="x", anchor="center")

            self.time_label = ctk.CTkLabel(
                self.timings_marks_frame,
                text="Time: ",
                text_color="#4A232A",
                font=("Arial", 14, "bold")
            )
            self.time_label.pack(pady=5, side="left")

            self.total_marks = ctk.CTkEntry(
                self.timings_marks_frame, placeholder_text="",
                height=40, font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
                fg_color="#F5F5DC",
                text_color="#333333",
                border_color="#F5F5DC", border_width=2,
                width=200,
                state="disabled"
            )
            self.total_marks.pack(padx=10, pady=10, side="right")

            self.total_marks_label = ctk.CTkLabel(
                self.timings_marks_frame,
                text="Total Marks: ",
                text_color="#4A232A",
                font=("Arial", 14, "bold")
            )
            self.total_marks_label.pack(pady=5, side="right")

            self.instructions_frame = ctk.CTkFrame(
                self.detail_frame, fg_color="#F5F5DC", corner_radius=0, width=200, height=400
            )
            self.instructions_frame.pack(padx=10, pady=10, fill="x", anchor="center")

            self.instruction_label = ctk.CTkLabel(
                self.instructions_frame,
                text="Instructions: ",
                text_color="#4A232A",
                font=("Arial", 14, "bold")
            )
            self.instruction_label.pack(pady=5, side="left")

            self.instruction_option = ctk.CTkComboBox(
                self.instructions_frame,
                values=["Default"],
                fg_color="#F5DEB3",
                text_color="#4A232A",
                button_color="#D4A373",
                button_hover_color="#8B4513",
                dropdown_fg_color="#DEB887",
                dropdown_text_color="#4A232A",
                dropdown_hover_color="#D4A373",
                border_color="#B87333",
                width=200
            )
            self.instruction_option.pack(pady=10, side="left")

            self.submit_paper_details_btn = ctk.CTkButton(
                self.workspace_frame,
                text="Submit Details",
                fg_color="#8B4513",
                hover_color="#6A2E1F",
                text_color="#F5F5DC",
                width=200, height=42,
                command=lambda: self.authenticate_paper_details()
            )
            self.submit_paper_details_btn.pack(padx=10, pady=10, side="right")

    def authenticate_paper_details(self):
        exam_title = self.title_entry.get()
        subject_code = self.subject_code.get()
        date_of_exam = self.exam_date.get()
        subject_name = self.subject_name.get()

        if subject_code == "" or date_of_exam == "" or subject_name == "" or exam_title == "":
            self.showMessageBox()
            play_sound("error")
            self.message_title.configure(
                image=ctk.CTkImage(
                    light_image=Image.open(get_resource_path("assets\\symbols\\triangle-warning.png")), size=(20, 20)
                ), text="All Fields Are Required", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                fg_color="#D32F2F"
            )
            self.message_desc.configure(
                text="To proceed, please ensure every field is filled out accurately. All fields are mandatory for successful submission.")
            return

        try:
            exam_date = datetime.strptime(date_of_exam, "%d-%m-%Y")

            if exam_date < datetime.today():
                self.showMessageBox()
                play_sound("error")
                self.message_title.configure(
                    image=ctk.CTkImage(
                        light_image=Image.open(get_resource_path("assets\\symbols\\calendar.png")),
                        size=(20, 20)
                    ), text="Invalid Date", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                    fg_color="#D32F2F"
                )
                self.message_desc.configure(text="The exam date cannot be in the past. Please enter a valid future date to proceed.")
                return
        except ValueError:
            play_sound("error")
            self.showMessageBox()
            self.message_title.configure(
                image=ctk.CTkImage(
                    light_image=Image.open(get_resource_path("assets\\symbols\\calendar.png")),
                    size=(20, 20)
                ), text="Invalid Date Format", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                fg_color="#D32F2F"
            )
            self.message_desc.configure(text="The date entered does not match the required format. Please use the format DD-MM-YYYY.")
            return

        play_sound("success")
        self.showMessageBox()
        self.message_title.configure(text="Validation Successful", image=ctk.CTkImage(
            light_image=(Image.open(get_resource_path("assets\\symbols\\check-circle.png"))),
            size=(20, 20)
        ), text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#4CAF50")
        self.message_desc.configure(text="The details have been successfully validated and saved. You may make any further changes if required before finalizing.")
        self.temp["workspace"]["details"] = {
            "exam_title": exam_title.upper(), "subject_code": subject_code.upper(), "subject_name": subject_name.upper(),
            "date_of_exam": date_of_exam.upper(), "total_marks": 0, "time": None, "instructions": self.instruction_option.get()
        }
        self.title_entry.delete(0, len(exam_title))
        self.title_entry.insert(0, exam_title.upper())
        self.subject_code.delete(0, len(subject_code))
        self.subject_code.insert(0, subject_code.upper())
        self.subject_name.delete(0, len(subject_name))
        self.subject_name.insert(0, subject_name.upper())
        self.title_entry.configure(state="disabled")
        self.subject_code.configure(state="disabled", border_color="#F5F5DC")
        self.exam_date.configure(state="disabled", border_color="#F5F5DC")
        self.subject_name.configure(state="disabled", border_color="#F5F5DC")
        self.instruction_option.configure(state="disabled")
        self.submit_paper_details_btn.pack_forget()
        self.submit_paper_details_btn.destroy()
        ic(self.temp["workspace"])
        self.create_action_btn()

    def create_action_btn(self):

        self.workspace_button_bottom_frame = ctk.CTkFrame(
            self.workspace_frame,
            fg_color="#F5F5DC", corner_radius=0, width=200, height=100
        )
        self.workspace_button_bottom_frame.pack(padx=10, fill="x", anchor="center")
        self.workspace_button_bottom_frame.pack_propagate(False)

        self.add_question_btn = ctk.CTkButton(
            self.workspace_button_bottom_frame,
            text="Add Question",
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\add.png")), size=(20, 20)),
            fg_color="#8B4513",
            hover_color="#6A2E1F",
            text_color="#F5F5DC",
            width=120, height=42,
            command=lambda: self.addQuestion()
        )
        self.add_question_btn.pack(padx=10, pady=10, side="right")

        self.tag_btn = ctk.CTkButton(
            self.workspace_button_bottom_frame,
            text="Add Tag",
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\tags.png")), size=(20, 20)),
            fg_color="#8B4513",
            hover_color="#6A2E1F",
            text_color="#F5F5DC",
            width=120, height=42,
            command=lambda: self.addTag()
        )
        self.tag_btn.pack(padx=10, pady=10, side="right")

    def saving_new_paper_process(self):
        questions = self.collect_data()
        if questions == {}:
            messagebox.showerror("Minimum Question Required", "You need to add at least 1 question before saving the paper. Please create a question and try again.")
            return
        if not questions:
            return

        features = {
            "enable-negative-markings": self.allow_negative_marking_chb.get(),
            "enable-time-limit": self.enable_time_limit_chb.get(),
            "enable-shuffling": self.shuffle_questions_chb.get(),
            "grading-system": self.grading_options.get(),
            "difficulty-level": self.difficulty_level.get(),
            "exam-mode": self.exam_mode_var.get()
        }

        total_marks = 0
        count = 0
        questions_list = {}
        for i in questions.keys():
            count += 1
            questions_list[count] = questions.get(i)
            total_marks += int(questions.get(i).get("marks"))
            ic(total_marks)
            ic(int(questions.get(i).get("marks")))

        self.temp["workspace"]["details"]["total_marks"] = total_marks

        paper = {"authentication": None, "headers": self.temp["workspace"]["details"], "features": features, "questions": questions_list}

        default_filename: str = self.temp["workspace"]["details"]["exam_title"].replace(" ", "_") + "_" + self.temp["workspace"]["details"]["date_of_exam"].replace(" ", "_") + ".bin.enc"
        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            filetypes=[("Brainy Studio Encrypted File", ".bin.enc")]
        )
        service = EncryptionService(paper, file_path, "Dragon@Ocean72")
        service.encryptData()
        messagebox.showinfo("File Saved", "Your test paper has been successfully saved! It is now available for access and distribution\nYou can access it anytime from your saved documents.")
        play_sound("success")
        self.showMessageBox()
        self.message_title.configure(text="File Saved", image=ctk.CTkImage(
            light_image=(Image.open(get_resource_path("assets\\symbols\\check-circle.png"))),
            size=(20, 20)
        ), text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#4CAF50")
        self.message_desc.configure(text=f"File successfully saved at {file_path}")
        self.display_content("home-page")
        return

    def addQuestion(self):
        self.count += 1
        question_frame = ctk.CTkFrame(
            self.workspace_frame, corner_radius=10, height=450,
            fg_color="#FAEBD7", border_color="#A9A9A9", border_width=2
        )
        question_frame.pack(padx=20, pady=20, anchor="center", expand=True, fill="both")
        question_frame.pack_propagate(False)

        info_frame = ctk.CTkFrame(
            question_frame, fg_color="#F5F5DC", border_color="#8B4513"
        )
        info_frame.pack(padx=10, pady=10, anchor="w", fill="x")

        tag_label = ctk.CTkLabel(
            info_frame, text="Tag: ", font=ctk.CTkFont(family="Calibri", size=18), text_color="#6B8E23",
            image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\tags.png")), size=(20, 20)),
            padx=10, compound="right"
        )
        tag_label.pack(padx=10, pady=10, side="left")

        tag_entry = ctk.CTkComboBox(
            info_frame,
            values=self.tags,
            width=210,
            font=ctk.CTkFont(family="Calibri", size=18),
            fg_color="#F5F5DC",
            text_color="#4B0030",
            button_color="#8B4513",
            button_hover_color="#A0522D",
            dropdown_fg_color="#FAF0E6",
            dropdown_text_color="#4B0030",
            dropdown_hover_color="#D2B48C",
            dropdown_font=ctk.CTkFont(family="Calibri", size=18)
        )
        tag_entry.pack(padx=0, pady=10, side="left")

        delete_button = ctk.CTkButton(
            info_frame, text="", image=ctk.CTkImage(Image.open(get_resource_path("assets\\symbols\\delete_btn.png")), size=(20, 20)),
            font=ctk.CTkFont(family="Calibri", size=14),
            fg_color="#B22222",
            hover_color="#8B0000",
            width=40,
            command=lambda qn=self.count: self.delete_question(qn)
        )
        delete_button.pack(padx=10, pady=10, side="right")

        marks_entry = ctk.CTkEntry(
            info_frame, placeholder_text="marks: ",
            text_color="#4B0030",
            fg_color="#F5F5DC",
            border_color="#8B4513",
            placeholder_text_color="#8B4513",
            border_width=2,
            font=ctk.CTkFont(family="Calibri", size=14, slant="italic"),
            width=60
        )
        marks_entry.pack(side="right")

        question_text_box = ctk.CTkTextbox(
            question_frame, width=1000, height=100,
            corner_radius=10, font=ctk.CTkFont(family="Calibri", size=20),
            fg_color="#FAF0E6",
            border_color="#A0522D",
            text_color="#4B0030",
            border_width=2
        )
        question_text_box.pack(padx=10, pady=10, anchor="w", fill="x")

        options = ["A", "B", "C", "D"]
        checkbox_states = {option: False for option in options}
        checkboxes = {}
        option_entries = {}

        for i, option in enumerate(options, start=1):
            option_frame = ctk.CTkFrame(
                question_frame, width=950, height=50, fg_color="#FAF0E6",
                border_color="#8B4513",  border_width=2
            )
            option_frame.pack(padx=10, pady=5, anchor="w")
            option_frame.grid_propagate(False)

            checkbox = ctk.CTkCheckBox(
                option_frame, text=f"{options[i - 1]}. ",
                height=20, fg_color="#F5F5DC",
                font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                hover_color="#A0522D",
                checkmark_color="#4B0030",
                border_color="#8B4513",
                text_color="#4B0030",
                corner_radius=50,
                command=lambda opt=option, qn=self.count: self.on_checkbox_click(opt, qn)
            )
            checkbox.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            checkboxes[option] = checkbox

            options_entry = ctk.CTkEntry(
                option_frame,
                placeholder_text=f"Option {i}",
                border_width=2,
                width=800,
                height=30,
                font=ctk.CTkFont(family="Calibri", size=18),
                fg_color="#F5F5DC",
                border_color="#F5F5DC",
                placeholder_text_color="#A0522D",
                text_color="#4B0030"
            )
            options_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
            option_entries[option] = options_entry

            self.questions[self.count] = {
                "frame": question_frame,
                "question": question_text_box,
                "checkbox_states": checkbox_states,
                "checkboxes": checkboxes,
                "option_entries": option_entries,
                "tag": tag_entry,
                "marks": marks_entry,
                "type": "question"
            }

            self.workspace_button_bottom_frame.pack_forget()
            self.workspace_button_bottom_frame.pack(padx=20, pady=20, expand=True, fill="both")

    def on_checkbox_click(self, selected_option, question_number):
        checkbox_states = self.questions[question_number]["checkbox_states"]

        for option in checkbox_states:
            checkbox_states[option] = False

        checkbox_states[selected_option] = True

        self.questions[question_number]["checkbox_states"] = checkbox_states

        checkboxes = self.questions[question_number]["checkboxes"]
        for option, checkbox in checkboxes.items():
            if checkbox_states[option]:
                checkbox.select()
            else:
                checkbox.deselect()

    def addTag(self):
        dialog = TagDialog(self, title="Add a New Subject Tag", text="Please enter a unique tag name to categorize your subject. \nTags help in organizing and improving navigation.")

        tag = dialog.get_input()
        if tag is not None:
            if tag == "" or tag in self.tags:
                return
            else:
                self.tags.append(tag)
                for question in self.questions.keys():
                    data = self.questions.get(question)
                    combo = data.get("tag")
                    combo.configure(values=self.tags)
                play_sound("success")
                self.showMessageBox()
                self.message_title.configure(text="Tag Added", image=ctk.CTkImage(
                    light_image=(Image.open(get_resource_path("assets\\symbols\\check-circle.png"))),
                    size=(20, 20)
                ), text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#4CAF50")
                self.message_desc.configure(
                    text=f"The {tag} tag added successfully")

    def delete_question(self, question_id):
        if question_id in self.questions:
            question_frame = self.questions[question_id].get("frame")

            if question_frame:
                question_frame.destroy()

            del self.questions[question_id]

            self.workspace_button_bottom_frame.pack_forget()
            self.workspace_button_bottom_frame.pack(padx=20, pady=20, expand=True, fill="both")

    def redirect_to_edit_page(self):
        self.edit_page = EditPaperPage(master=self.frame, parent=self)
        self.edit_page.pack(padx=10, pady=10, anchor="center")

    def edit_paper(self):
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.count = 0
        self.questions = {}
        self.temp["workspace"] = {}
        self.tags = ["None"]
        filepath = filedialog.askopenfilename(initialdir=get_resource_path("data"), defaultextension=".bin.enc", filetypes=[("brainy-studio", ".bin.enc")])
        if not filepath:
            return
        service = EncryptionService(data=None, filepath=filepath, password="Dragon@Ocean72")
        service.decryptData()
        self.show_create_exam_view()
        features = service.data.get("features")
        if features.get("enable-negative-markings"):
            self.allow_negative_marking_chb.select()
        if features.get("enable-time-limit"):
            self.enable_time_limit_chb.select()
        if features.get("enable-shuffling"):
            self.shuffle_questions_chb.select()
        self.grading_options.set(features.get("grading-system"))
        self.difficulty_level.set(features.get("difficulty-level"))
        self.exam_mode_var.set(features.get("exam-mode"))
        exam_title = service.data["headers"]["exam_title"]
        subject_code = service.data["headers"]["subject_code"]
        subject_name = service.data["headers"]["subject_name"]
        exam_date = service.data["headers"]["date_of_exam"]
        questions = service.data["questions"]
        total_marks = service.data["headers"]["total_marks"]
        tags: set[str] = set()
        self.total_marks.configure(state="normal")
        self.total_marks.insert(0, str(total_marks))
        self.total_marks.configure(state="disabled")
        self.title_entry.delete(0, len(exam_title))
        self.title_entry.insert(0, exam_title.upper())
        self.subject_code.delete(0, len(subject_code))
        self.subject_code.insert(0, subject_code.upper())
        self.subject_name.delete(0, len(subject_name))
        self.subject_name.insert(0, subject_name.upper())
        self.title_entry.configure(state="disabled")
        self.subject_code.configure(state="disabled", border_color="#F5F5DC")
        self.exam_date.insert(0, exam_date)
        self.exam_date.configure(state="disabled", border_color="#F5F5DC")
        self.subject_name.configure(state="disabled", border_color="#F5F5DC")
        self.instruction_option.configure(state="disabled")
        self.submit_paper_details_btn.pack_forget()
        self.submit_paper_details_btn.destroy()
        self.authenticate_paper_details()

        for i in range(len(questions)):
            self.addQuestion()

        for j in self.questions.keys():
            question = self.questions.get(j)
            marks = question.get("marks").insert(0, questions[j].get("marks"))
            question.get("tag").set(questions[j].get("tag"))
            tags.add(questions[j].get("tag"))
            text_box: ctk.CTkTextbox = question.get("question").insert("1.0", questions[j].get("question"))
            checkbox_states = question.get("checkbox_states")
            checkbox_states[questions[j].get("answer")] = True
            checkboxes = self.questions[j]["checkboxes"]
            for option, checkbox in checkboxes.items():
                if checkbox_states[option]:
                    checkbox.select()
                else:
                    checkbox.deselect()
            entries = question.get("option_entries")
            for entry in entries.keys():
                options = entries.get(entry)
                options.insert(0, questions.get(j).get("options").get(entry))

        for tag in tags:
            self.tags.append(tag)
        for question in self.questions.keys():
            data = self.questions.get(question)
            combo = data.get("tag")
            combo.configure(values=self.tags)

    @staticmethod
    def validate_marks(marks: str):
        if marks.isdigit():
            return True
        else:
            return False

    def collect_data(self):
        if self.temp["workspace"] == {}:
            self.showMessageBox()
            play_sound("error")
            self.message_title.configure(
                image=ctk.CTkImage(
                    light_image=Image.open(get_resource_path("assets\\symbols\\triangle-warning.png")), size=(20, 20)
                ), text="Submission Needed!", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                fg_color="#D32F2F"
            )
            self.message_desc.configure(
                text="To proceed, please ensure every field is filled out accurately. All fields are mandatory for successful submission.")
            return
        formatted_questions = {}
        for qn, details in self.questions.items():
            question_text = details["question"].get("1.0", "end-1c").strip()
            marks = details["marks"].get().strip()
            is_valid_marks = self.validate_marks(marks)
            if not is_valid_marks:
                messagebox.showerror("Invalid Marks",
                                     f"Question {qn}: Please enter a valid numeric value for marks. Ensure it is not empty and contains only numbers.")
                return
            question_type = details["type"]
            tag = details["tag"].get().strip()
            selected_option = None

            if question_type == "question":
                options = {key: entry.get().strip() for key, entry in details["option_entries"].items()}
                for option, selected in details["checkbox_states"].items():
                    if selected:
                        selected_option = option

                if selected_option is None:
                    messagebox.showerror("No Answer Selected",
                                         "Please select the correct answer for the question before proceeding.")
                    return
                formatted_questions[qn] = {
                    "type": question_type,
                    "question": question_text,
                    "marks": marks,
                    "options": options,
                    "answer": selected_option,
                    "tag": tag
                }
        return formatted_questions

    def create_symbols_frame(self):

        # Math Symbols
        ctk.CTkLabel(self.symbols_frame, text="Math Symbols", font=("Arial", 14, "bold"), text_color="#333333").pack(
            padx=10, pady=10, anchor="w")
        math_buttons = [
            ("x²", "x²"),
            ("x³", "x³"),
            ("ln", "ln"),
            ("log₁₀", "log₁₀"),
            ("logₐ", "logₐ"),
            ("√", "√"),
            ("π", "π"),
            ("∞", "∞"),
            ("∑", "∑"),
            ("α", "α"),
            ("β", "β"),
            ("γ", "γ"),
            ("δ", "δ"),
            ("θ", "θ"),
            ("λ", "λ"),
            ("μ", "μ"),
            ("σ", "σ"),
            ("Δ", "Δ"),
            ("Φ", "Φ"),
            ("ω", "ω"),
            ("≠", "≠"),
            ("≈", "≈"),
            ("≡", "≡"),
            ("≤", "≤"),
            ("≥", "≥"),
            ("∈", "∈"),
            ("⊂", "⊂"),
            ("⊃", "⊃"),
            ("∩", "∩"),
            ("∪", "∪"),
            ("∅", "∅"),
            ("∫", "∫"),
            ("∑", "∑"),
            ("∏", "∏"),
            ("∝", "∝"),
            ("∥", "∥"),
            ("∃", "∃"),
            ("∀", "∀"),
            ("⇒", "⇒"),
            ("⇔", "⇔"),
            ("ℕ", "ℕ"),
            ("ℝ", "ℝ"),
            ("ℤ", "ℤ"),
            ("ℂ", "ℂ"),
            ("ℚ", "ℚ"),
            ("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV"), ("V", "V"),
            ("VI", "VI"), ("VII", "VII"), ("VIII", "VIII"), ("IX", "IX"), ("X", "X")
        ]
        self.create_button_frame(self.symbols_frame, math_buttons)

        # Chemistry Symbols
        ctk.CTkLabel(self.symbols_frame, text="Chemistry Symbols", font=("Arial", 14, "bold"),
                     text_color="#333333").pack(padx=10, pady=10, anchor="w")
        chemistry_buttons = [
            ("→", "→"),
            ("⇌", "⇌"),
            ("Δ", "Δ"),
            ("≠", "≠"),
            ("±", "±"),
            ("∑", "∑"),
            ("∫", "∫"),
            ("•", "•"),
            ("°", "°"),
            ("ℳ", "ℳ"),
            ("⌀", "⌀"),
            ("⧫", "⧫"),
            ("⊕", "⊕"),
            ("⊖", "⊖"),
            ("⊗", "⊗"),
            ("‡", "‡"),
            ("∅", "∅"),
            ("∩", "∩"),
            ("⊂", "⊂"),
            ("≡", "≡"),
            ("≠", "≠"),
            ("→", "→"),
            ("⇌", "⇌"),
            ("→", "→"),
            ("𝑀", "𝑀"),
            ("𝑁", "𝑁"),
            ("H₂O", "H₂O"),
            ("CO₂", "CO₂"),
            ("C₆H₁₂O₆", "C₆H₁₂O₆")
        ]
        self.create_button_frame(self.symbols_frame, chemistry_buttons)

        # Physics Symbols
        ctk.CTkLabel(self.symbols_frame, text="Physics Symbols", font=("Arial", 14, "bold"), text_color="#333333").pack(
            padx=10, pady=10, anchor="w")
        physics_buttons = [
            ("α", "α"),
            ("β", "β"),
            ("γ", "γ"),
            ("Δ", "Δ"),
            ("λ", "λ"),
            ("μ", "μ"),
            ("ω", "ω"),
            ("Σ", "Σ"),
            ("Ω", "Ω"),
            ("π", "π"),
            ("∞", "∞"),
            ("∑", "∑"),
            ("≈", "≈"),
            ("≡", "≡"),
            ("⊗", "⊗"),
            ("⊕", "⊕"),
            ("⊂", "⊂"),
            ("∇", "∇"),
            ("∂", "∂"),
            ("∅", "∅"),
            ("↑", "↑"),
            ("↓", "↓"),
            ("→", "→"),
            ("←", "←"),
            ("∩", "∩"),
            ("∪", "∪"),
            ("∈", "∈"),
            ("ℵ", "ℵ"),
            ("ℏ", "ℏ"),
            ("≠", "≠"),
            ("≡", "≡"),
            ("⇒", "⇒"),
            ("⇔", "⇔"),
            ("∀", "∀"),
            ("∃", "∃"),
            ("∝", "∝"),
            ("∥", "∥"),
            ("∫", "∫"),
            ("∑", "∑"),
            ("∏", "∏"),
            ("ℂ", "ℂ"),
            ("ℤ", "ℤ"),
            ("ℝ", "ℝ"),
            ("ℕ", "ℕ"),
            ("ℚ", "ℚ"),
            ("ρ", "ρ"),
            ("ε", "ε"),
            ("k", "k"),
            ("ε₀", "ε₀")
        ]
        self.create_button_frame(self.symbols_frame, physics_buttons)

    def create_button_frame(self, parent_frame, buttons_list):
        button_count = 0
        for text, symbol in buttons_list:
            if button_count % 12 == 0:
                button_frame = ctk.CTkFrame(parent_frame, fg_color="#C8C8A9", corner_radius=10)
                button_frame.pack(fill="x", anchor="w")

            button = ctk.CTkButton(
                button_frame,
                text=text,
                fg_color="#F5F5DC",
                text_color="#333333",
                width=40, height=40,
                corner_radius=5,
                hover_color="#C8C8A9",
                command=lambda text=text, symbol=symbol: self.copyText(symbol, text)
            )
            button.pack(side="left", padx=5, pady=5)
            button_count += 1

    def show_api_configurations(self, event=None):

        ERROR_404 = False
        config_file_path = get_resource_path("data\\config.json")
        if config_file_path:
            with open(config_file_path, "r") as f:
                data = json.load(f)
        else:
            self.showMessageBox()
            self.message_title.configure(
                image=ctk.CTkImage(
                    light_image=Image.open(get_resource_path("assets\\symbols\\not-found.png")), size=(20, 20)
                ), text="File not Found", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                fg_color="#D32F2F"
            )
            self.message_desc.configure(text="The API configurations file is missing!")
            ERROR_404 = True

        if not ERROR_404:
            try:
                access_token = data["access_token"]
                app_key = data["app_key"]
                app_secret = data["app_secret"]
                self.temp["config"] = {"access-token": access_token, "app-key": app_key, "app-secret": app_secret}
            except Exception as e:
                self.showMessageBox()
                self.message_title.configure(
                    image=ctk.CTkImage(
                        light_image=Image.open(get_resource_path("assets\\symbols\\not-found.png")), size=(20, 20)
                    ), text="File not Found", text_color="#FFFFFF", compound="right", padx=10, pady=10,
                    fg_color="#D32F2F"
                )
                self.message_desc.configure(text="The API configurations file is missing!")
                return
        else:
            return

        if self.dbx_frame is None:
            self.clearFrame()
            (ctk.CTkLabel(
                self.frame, text="API CONFIGURATIONS",
                font=ctk.CTkFont(family="Game Of Squids", size=28, weight="bold"),
                text_color="#212121")
             .pack(padx=10, pady=20, anchor="center"))

            self.dbx_frame = ctk.CTkFrame(self.frame, fg_color="#F5F5F5")
            self.dbx_frame.pack(padx=25, pady=10, anchor="center", fill="x")

            self.btn_frame = ctk.CTkFrame(self.frame, fg_color="#FFFFFF")
            self.btn_frame.pack(padx=25, pady=10, anchor="center", fill="x")

            (ctk.CTkLabel(
                self.dbx_frame, text=f"Access Token", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                text_color="#333333"
            ).grid(row=0, column=1, padx=10, pady=10, sticky="w"))

            self.access_token_entry = ctk.CTkEntry(
                self.dbx_frame, text_color="#212121", fg_color="#F5F5F5", border_color="#F5F5F5", width=810, height=30)
            self.access_token_entry.grid(row=0, column=2, padx=10, pady=10, sticky="w")
            self.access_token_entry.insert(0, f"{access_token}")
            self.access_token_entry.configure(state="disabled")

            ctk.CTkButton(
                self.dbx_frame, text="", image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\copy.png")), size=(20, 20)),
                width=30, height=30, fg_color="#F5F5F5", hover_color="#F5F5F5", command=lambda: self.copyText(text=access_token, name="access token")
            ).grid(row=0, column=3, padx=10, pady=10, sticky="e")

            (ctk.CTkLabel(
                self.dbx_frame, text=f"App Key", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                text_color="#333333"
            ).grid(row=1, column=1, padx=10, pady=10, sticky="w"))

            self.app_key_entry = ctk.CTkEntry(
                self.dbx_frame, text_color="#212121", fg_color="#F5F5F5", width=810, height=30, border_color="#F5F5F5")
            self.app_key_entry.grid(row=1, column=2, padx=10, pady=10, sticky="w")
            self.app_key_entry.insert(0, f"{app_key}")
            self.app_key_entry.configure(state="disabled")

            ctk.CTkButton(
                self.dbx_frame, text="",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\copy.png")), size=(20, 20)),
                width=30, height=30, fg_color="#F5F5F5", hover_color="#F5F5F5", command=lambda: self.copyText(text=app_key, name="app key")
            ).grid(row=1, column=3, padx=10, pady=10, sticky="e")

            (ctk.CTkLabel(
                self.dbx_frame, text=f"App Secret", font=ctk.CTkFont(family="Calibri", size=18, weight="bold"),
                text_color="#333333",
            ).grid(row=2, column=1, padx=10, pady=10, sticky="w"))

            self.app_secret_entry = ctk.CTkEntry(
                self.dbx_frame, text_color="#212121", fg_color="#F5F5F5", width=810, height=30, border_color="#F5F5F5")
            self.app_secret_entry.grid(row=2, column=2, padx=10, pady=10, sticky="w")
            self.app_secret_entry.insert(0, f"{app_secret}")
            self.app_secret_entry.configure(state="disabled")

            ctk.CTkButton(
                self.dbx_frame, text="",
                image=ctk.CTkImage(light_image=Image.open(get_resource_path("assets\\symbols\\copy.png")), size=(20, 20)),
                width=30, height=30, fg_color="#F5F5F5", hover_color="#F5F5F5", command=lambda: self.copyText(text=app_secret, name="app secret")
            ).grid(row=2, column=3, padx=10, pady=10, sticky="e")

            self.edit_configuration_btn = (ctk.CTkButton(
                self.btn_frame, text="Edit Configurations", width=120, height=38,
                fg_color="#2196F3", hover_color="#1E88E5", text_color="#FFFFFF",
                border_color="#1565C0", border_width=2, corner_radius=8, command=lambda: self.editConfigurations()
            ))
            self.edit_configuration_btn.pack(padx=10, pady=10, side="right")

    def copyText(self, text: str, name: str):
        pyperclip.copy(text)
        play_sound("success")
        self.showMessageBox()
        self.message_title.configure(text="Copy Successful", image=ctk.CTkImage(
            light_image=(Image.open(get_resource_path("assets\\symbols\\check-circle.png"))),
            size=(20, 20)
        ), text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#4CAF50")
        self.message_desc.configure(text=f"The {name} has been successfully copied to your clipboard.")

    def saveConfigurations(self):
        data = {
            "access_token": self.access_token_entry.get(),
            "app_key": self.app_key_entry.get(),
            "app_secret": self.app_secret_entry.get()
        }
        try:
            with open(get_resource_path("data\\config.json", force_get=True), "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            return

        self.save_btn.destroy()

        self.access_token_entry.configure(state="disabled")
        self.app_secret_entry.configure(state="disabled")
        self.app_key_entry.configure(state="disabled")

        self.edit_configuration_btn = ctk.CTkButton(
            self.btn_frame, text="Edit Configurations", width=120, height=38,
            fg_color="#2196F3", hover_color="#1E88E5", text_color="#FFFFFF",
            border_color="#1565C0", border_width=2, corner_radius=8, command=lambda: self.editConfigurations()
        )
        self.edit_configuration_btn.pack(padx=10, pady=10, side="right")

    def editConfigurations(self):
        self.app_secret_entry.configure(state="normal")
        self.app_key_entry.configure(state="normal")
        self.access_token_entry.configure(state="normal")

        if hasattr(self, 'edit_configuration_btn'):
            self.edit_configuration_btn.destroy()

        self.save_btn = ctk.CTkButton(
            self.btn_frame, text="Save Configurations", width=120, height=38,
            fg_color="#2196F3", hover_color="#1E88E5", text_color="#FFFFFF",
            border_color="#1565C0", border_width=2, corner_radius=8, command=lambda: self.saveConfigurations()
        )
        self.save_btn.pack(padx=10, pady=10, side="right")

    def run(self):
        self.configureThreadManagement()
        self.build()
        self.mainloop()

    def configureThreadManagement(self):
        self.network_thread = Thread(target=self.runNetworkCheck, daemon=True)
        self.network_thread.start()

    @staticmethod
    def checkNetwork():
        try:
            create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False

    def updateNetworkStatus(self):
        if not self.running:
            return

        self.isConnected = self.checkNetwork()
        if self.isConnected:
            self.title("Get Started with BrainyStudio")
        else:
            self.showMessageBox()
            self.title("Server Not Found ~ BrainyStudio")
            if self.message_box:
                self.message_title.configure(
                    image=ctk.CTkImage(
                        light_image=Image.open(get_resource_path("assets\\symbols\\not-found.png")), size=(20, 20)
                    ), text="No Internet Connection", text_color="#FFFFFF", compound="right", padx=10, pady=10, fg_color="#D32F2F"
                )
                self.message_desc.configure(text="Oops! It seems we are having trouble connecting to the server. Please check your connection and retry.")

    def runNetworkCheck(self):
        while True:
            self.updateNetworkStatus()
            time.sleep(5)


if __name__ == '__main__':
    pygame.mixer.init()
    App().run()
