

class ExamPDFGenerator:
    def __init__(self, title, subject_details, instructions, questions, enrollment_no, logo_path):
        """
        Initializes the PDF generator with exam details.

        Parameters:
            title (str): The title of the exam.
            subject_details (dict): Contains subject information like name, code, marks, and time.
            instructions (str): Instructions to display before the questions.
            questions (list): A list of tuples containing:
                              (question_text, marks, correct_option, options_list)
                              where options_list is a list of four option texts.
            enrollment_no (str): Enrollment number to display in the header.
            logo_path (str): Path to the logo image file.
        """
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
        pdf_file = "exam_with_options.pdf"
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
            if question_start_y < 100:  # Check for page space
                self.add_footer(pdf, page_num, width)
                pdf.showPage()
                page_num += 1
                question_start_y = height - 120

            pdf.setFont("Helvetica-Bold", 12)
            pdf.setFillColor(colors.HexColor("#2E3B55"))
            pdf.drawString(50, question_start_y, f"Q{i + 1}: {question_text}")
            pdf.drawRightString(width - 50, question_start_y, f"Marks: {marks}")

            pdf.setFont("Helvetica", 11)
            option_y = question_start_y - 25

            for j, option_text in enumerate(options_list):  # Options A, B, C, D
                pdf.setStrokeColor(colors.HexColor("#2E3B55"))
                pdf.circle(70, option_y, 4)

                if j == correct_option:  # Fill correct option
                    pdf.setFillColor(colors.HexColor("#333333"))
                    pdf.circle(70, option_y, 3, stroke=0, fill=1)
                    pdf.setFillColor(colors.HexColor("#000000"))

                pdf.setFillColor(colors.HexColor("#4A4A4A"))
                pdf.drawString(90, option_y - 4, f"{option_text}")
                option_y -= 25

            question_start_y = option_y - 20

        self.add_footer(pdf, page_num, width)
        pdf.save()

# Example usage
subject_details = {
    "subject_name": "Mathematics",
    "total_marks": "100",
    "subject_code": "MATH101",
    "time_duration": "2 Hours",
    "subject_date": "2024-12-29"
}

instructions = """Please read the instructions carefully before attempting the questions:
1. All questions are mandatory.
2. Each question carries equal marks.
3. Use of calculators is not allowed.
4. Write your answers legibly."""

questions = [
    ("What is the capital of France?", 5, 1, ["Berlin", "Paris", "Madrid", "Rome"]),
    ("Solve: 2 + 2 x 2?", 5, 2, ["4", "6", "8", "10"]),
    ("What is the square root of 16?", 5, 0, ["4", "8", "2", "16"]),
]

enrollment_no = "226490316024"
logo_path = r"C:\\Users\\aksha\\OneDrive\\Desktop\\Sem6\\LastyearProject\\brainy-studio\\assets\\images\\logo.png"

pdf_generator = ExamPDFGenerator(
    title="Enhanced Examination Paper",
    subject_details=subject_details,
    instructions=instructions,
    questions=questions,
    enrollment_no=enrollment_no,
    logo_path=logo_path
)

pdf_generator.generate_pdf()