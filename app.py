from flask import Flask, render_template, request
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
DATABASE_FILE = "hostel_hms.db"
TOTAL_STUDENTS = 200

# --- Database Setup ---
def create_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def setup_database(conn):
    cursor = conn.cursor()

    # Students Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            student_id INTEGER PRIMARY KEY,
            reg_number TEXT UNIQUE, 
            name TEXT NOT NULL,
            room_number TEXT UNIQUE NOT NULL,
            phone_number TEXT
        );
    ''')

    # Attendance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Attendance (
            attendance_id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL, 
            FOREIGN KEY (student_id) REFERENCES Students(student_id),
            UNIQUE (student_id, date)
        );
    ''')

    # Complaints Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Complaints (
            complaint_id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            department TEXT NOT NULL,
            description TEXT NOT NULL,
            date_filed DATETIME NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES Students(student_id)
        );
    ''')

    # Feedback Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Feedback (
            feedback_id INTEGER PRIMARY KEY,
            student_id INTEGER,
            rating INTEGER,
            comments TEXT NOT NULL,
            date_submitted DATETIME NOT NULL,
            FOREIGN KEY (student_id) REFERENCES Students(student_id)
        );
    ''')

    # Clear all data for debugging
    cursor.execute("DELETE FROM Feedback") 
    cursor.execute("DELETE FROM Complaints") 
    cursor.execute("DELETE FROM Attendance") 
    cursor.execute("DELETE FROM Students")
    conn.commit()

def generate_dummy_students(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Students")
    current_student_count = cursor.fetchone()[0]

    if current_student_count == 0:
        print(f"Generating and inserting {TOTAL_STUDENTS} dummy student records...")

        first_names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack", 
                       "Kate", "Liam", "Mia", "Noah", "Olivia", "Peter", "Quinn", "Ryan", "Sara", "Tom"]
        last_names = ["Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson"]

        a_rooms = [f"A{j:03d}" for j in range(101, 201)]
        b_rooms = [f"B{j:03d}" for j in range(101, 201)]
        room_numbers = a_rooms + b_rooms
        random.shuffle(room_numbers)

        students_data = []
        for i in range(TOTAL_STUDENTS):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            room_number = room_numbers[i]
            reg_number = f"R{i + 100000:06d}"
            phone_number = f"9{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            students_data.append((reg_number, name, room_number, phone_number))

        cursor.executemany(
            "INSERT INTO Students (reg_number, name, room_number, phone_number) VALUES (?, ?, ?, ?)",
            students_data
        )
        conn.commit()
        print(f"Successfully inserted {TOTAL_STUDENTS} students.")

def get_student_info(conn, identifier):
    cursor = conn.cursor()
    identifier = identifier.upper()
    cursor.execute("SELECT student_id, name FROM Students WHERE room_number=? OR reg_number=?", (identifier, identifier))
    return cursor.fetchone()

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/facilities')
def facilities():
    return render_template('facilities.html')

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if request.method == 'POST':
        identifier = request.form['room']
        conn = create_connection()
        info = get_student_info(conn, identifier)
        if not info:
            return "Student not found."
        student_id, name = info
        date = datetime.now().strftime('%Y-%m-%d')
        try:
            conn.execute("INSERT INTO Attendance (student_id, date, status) VALUES (?, ?, ?)", (student_id, date, 'Present'))
            conn.commit()
            return "Checked In"
        except sqlite3.IntegrityError:
            return "Already checked in today."
    return render_template('checkin.html')

@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        identifier = request.form['room']
        department = request.form['department']
        description = request.form['description']
        conn = create_connection()
        info = get_student_info(conn, identifier)
        if not info:
            return "Student not found."
        student_id, name = info
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("INSERT INTO Complaints (student_id, department, description, date_filed, status) VALUES (?, ?, ?, ?, ?)",
                     (student_id, department, description, timestamp, "Pending"))
        conn.commit()
        return "Complaint registered"
    return render_template('complaint.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        identifier = request.form['room']
        rating = request.form['rating']
        comments = request.form.get('comments', '')
        conn = create_connection()
        student_id = None
        if identifier:
            info = get_student_info(conn, identifier)
            if info:
                student_id = info[0]
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("INSERT INTO Feedback (student_id, rating, comments, date_submitted) VALUES (?, ?, ?, ?)",
                     (student_id, rating, comments, timestamp))
        conn.commit()
        return "Thank You!"
    return render_template('feedback.html')

@app.route('/view')
def view_database():
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Students")
    students = cursor.fetchall()

    cursor.execute("SELECT * FROM Attendance")
    attendance = cursor.fetchall()

    cursor.execute("SELECT * FROM Complaints")
    complaints = cursor.fetchall()

    cursor.execute("SELECT * FROM Feedback")
    feedback = cursor.fetchall()

    conn.close()
    return render_template('view.html',
                           students=students,
                           attendance=attendance,
                           complaints=complaints,
                           feedback=feedback)

if __name__ == '__main__':
    conn = create_connection()
    setup_database(conn)
    generate_dummy_students(conn)
    conn.close()
    app.run(debug=True)


@app.route('/test')
def test():
    return "Flask is working!"


