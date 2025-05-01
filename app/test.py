import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(r"D:\github_projects\brainy-studio\app\database\brainy-studio.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT UNIQUE,
    subject_name TEXT,
    instructions TEXT
)
""")

# Define the standardized instructions
instructions = """1. Stable Internet Required: Ensure a good connection.
2. Use Allowed Devices: Only a laptop/PC; no mobile phones or smartwatches.
3. No Switching Tabs: Changing windows may lead to disqualification.
4. Answer all questions within the given time limit. No extra time will be provided.
5. Submit the exam before the deadline, as responses will not be accepted afterward."""

# List of subjects to insert
subjects = [
    ("310034", "Mathematics I"),
    ("320001", "Mathematics II"),
    ("DI01000031", "Communication Skills in English"),
    ("3321601", "Fundamentals of Information Technology"),
    ("3320701", "Computer Programming"),
    ("3330702", "Database Management System"),
    ("3330703", "Operating System"),
    ("3340701", "Data Structures"),
    ("3350703", "Computer Networks"),
    ("3350704", "Web Programming"),
    ("3360701", "Software Engineering"),
    ("3360702", "Advanced Java Programming"),
    ("3360704", "Cyber Security"),
    ("3360705", "Mobile Computing and Application Development"),
    ("3360706", "Project and Seminar")
]

for code, name in subjects:
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO subjects (subject_code, subject_name, instructions)
            VALUES (?, ?, ?)
        """, (code, name, instructions))
    except Exception as e:
        print(f"Error inserting {code} - {name}: {e}")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("✅ Subjects have been successfully inserted into the database.")
