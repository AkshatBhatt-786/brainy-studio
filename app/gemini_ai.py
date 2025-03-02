import customtkinter as ctk
import google.generativeai as genai
import json
from tkinter import messagebox

# genai.configure(api_key="AIzaSyA270m_UGUSDDJZRWsUzYuSpGhNj7aY2Z4")

# Initialize Gemini AI
genai.configure(api_key='AIzaSyA270m_UGUSDDJZRWsUzYuSpGhNj7aY2Z4')
model = genai.GenerativeModel('gemini-pro')

# Function to generate questions using Gemini AI
def generate_questions(num_questions, difficulty, subject):
    prompt = f"""
    Generate {int(num_questions)} {difficulty} level multiple-choice questions on {subject}.
    Each question should have 4 options and a correct answer.
    Format the response as a JSON array of objects, where each object has the following keys:
    - question_id (integer)
    - question (string)
    - marks (integer)
    - options (array of strings)
    - correct_option (string)
    - tag (string)

    Example:
    [
        {{
            "question_id": 1,
            "question": "What is the capital of France?",
            "marks": 1,
            "options": ["A) Paris", "B) Berlin", "C) Rome", "D) Madrid"],
            "correct_option": "A",
            "tag": "Geography"
        }},
        {{
            "question_id": 2,
            "question": "What is 2 + 2?",
            "marks": 1,
            "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
            "correct_option": "B",
            "tag": "Math"
        }}
    ]

    IMPORTANT: Return only the JSON array. Do not include any additional text or explanations.
    """
    response = model.generate_content(prompt)
    return response.text

# Function to save questions as JSON
def save_to_json(questions, filename="questions.json"):
    try:
        # Validate if the response is valid JSON
        try:
            questions_json = json.loads(questions)
        except json.JSONDecodeError:
            # Attempt to extract JSON from the response
            start_index = questions.find('[')
            end_index = questions.rfind(']') + 1
            if start_index != -1 and end_index != -1:
                questions = questions[start_index:end_index]
                questions_json = json.loads(questions)
            else:
                raise ValueError("Response is not valid JSON.")
        
        # Save the questions as JSON
        with open(filename, "w") as f:
            json.dump(questions_json, f, indent=4)
        messagebox.showinfo("Success", f"Questions saved to {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save questions: {e}")

# GUI Application
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Question Generator")
        self.geometry("400x300")
        
        # Number of Questions
        self.num_questions_label = ctk.CTkLabel(self, text="Number of Questions:")
        self.num_questions_label.pack(pady=5)
        self.num_questions_entry = ctk.CTkEntry(self)
        self.num_questions_entry.pack(pady=5)
        
        # Difficulty Level
        self.difficulty_label = ctk.CTkLabel(self, text="Difficulty Level:")
        self.difficulty_label.pack(pady=5)
        self.difficulty_combobox = ctk.CTkComboBox(self, values=["Easy", "Medium", "Hard"])
        self.difficulty_combobox.pack(pady=5)
        
        # Subject
        self.subject_label = ctk.CTkLabel(self, text="Subject:")
        self.subject_label.pack(pady=5)
        self.subject_entry = ctk.CTkEntry(self)
        self.subject_entry.pack(pady=5)
        
        # Generate Button
        self.generate_button = ctk.CTkButton(self, text="Generate Questions", command=self.generate)
        self.generate_button.pack(pady=20)
    
    def generate(self):
        num_questions = self.num_questions_entry.get()
        difficulty = self.difficulty_combobox.get()
        subject = self.subject_entry.get()
        
        if not num_questions or not difficulty or not subject:
            messagebox.showerror("Error", "Please fill all fields")
            return
        
        try:
            num_questions = int(num_questions)
            questions = generate_questions(num_questions, difficulty, subject)
            save_to_json(questions)
        except ValueError:
            messagebox.showerror("Error", "Number of questions must be an integer")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate questions: {e}")

# Run the application
if __name__ == "__main__":
    app = App()
    app.mainloop()