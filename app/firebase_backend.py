import firebase_admin
from firebase_admin import credentials, firestore
import os
import socket
import json
from tkinter import messagebox
import hashlib

class FirebaseBackend:
    def __init__(self):
        service_account_json = os.getenv("FIREBASE_CONFIG")
        self.database_connected = False

        if service_account_json:
            try:
                cred_dict = json.load(open(service_account_json))
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                self.database_connected = True
            except Exception as e:
                print(f"Error initializing Firebase: {e}")
                self.database_connected = False
        
    def create_exam(self, exam_id, access_code, subject_details):
        if not self.database_connected:
            print("Database is not connected!")
            return False

        try:
            exam_data = {
                "access_code": access_code,
                "subject_details": subject_details,
                "students": {}
            }

            doc_ref = self.db.collection("exams").document(exam_id)
            doc_ref.set(exam_data)

            print(f"Exam {exam_id} created successfully!")
            return True
        except Exception as e:
            print(f"Error creating exam: {e}")
            return False
