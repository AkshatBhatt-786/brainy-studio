# Define the test data structure with additional questions covering Physics, Chemistry, True/False, and One Word types
import pandas as pd

data = {
    "Question ID": ["A1B2C3", "X9Y8Z7", "M3N4P5", "Q7R8S9", "L5M6N7", "P2Q3R4", "T1U2V3", "W4X5Y6", "Z7A8B9", "C1D2E3"],
    "Question": [
        "What is the capital of France?",
        "Which programming language is known as the 'mother of all languages'?",
        "What is 2 + 2?",
        "Who wrote 'Hamlet'?",
        "What is the speed of light in vacuum?",
        "Which planet is known as the Red Planet?",
        "Water boils at 100°C at sea level. (True/False)",
        "The chemical symbol for Gold is 'Au'. (True/False)",
        "What is the chemical formula of water?",
        "Name the force that keeps planets in orbit around the sun."
    ],
    "Tags": ["Geography", "Programming", "Math", "Literature", "Physics", "Astronomy", "Physics", "Chemistry", "Chemistry", "Physics"],
    "Marks": [5, 3, 2, 4, 6, 3, 2, 2, 3, 4],
    "Options": [
        "A: Paris, B: London, C: Berlin, D: Rome",
        "A: C, B: Assembly, C: Python, D: Java",
        "A: 3, B: 4, C: 5, D: 6",
        "A: William Shakespeare, B: Charles Dickens, C: Jane Austen, D: Mark Twain",
        "A: 299,792 km/s, B: 150,000 km/s, C: 3,000 km/s, D: 30,000 km/s",
        "A: Mars, B: Venus, C: Jupiter, D: Saturn",
        "",  # True/False type, no options needed
        "",  # True/False type, no options needed
        "",  # One-word type, no options needed
        ""   # One-word type, no options needed
    ],
    "Question Type": ["MCQ", "MCQ", "MCQ", "MCQ", "MCQ", "MCQ", "True/False", "True/False", "One Word", "One Word"],
    "Answer": ["A", "B", "B", "A", "A", "A", "1", "1", "H2O", "Gravity"]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Save to an Excel file
test_file_path = "question_bank.xlsx"
df.to_excel(test_file_path, index=False)
