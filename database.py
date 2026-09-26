
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("studentai.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        class_level TEXT,
        board TEXT,
        exam TEXT,
        subjects TEXT,
        hobbies TEXT,
        long_term_goal TEXT,
        sports TEXT,
        activity_level TEXT,
        study_hours REAL DEFAULT 2,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        task TEXT NOT NULL,
        subject TEXT,
        due_date TEXT,
        priority TEXT DEFAULT 'Medium',
        completed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS syllabus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        chapter TEXT NOT NULL,
        topic TEXT,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT,
        minutes INTEGER NOT NULL,
        session_date TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT,
        chapter TEXT,
        topic TEXT,
        difficulty TEXT,
        question TEXT NOT NULL,
        correct_answer TEXT,
        student_answer TEXT,
        is_correct INTEGER,
        explanation TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS parent_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER UNIQUE NOT NULL,
        code TEXT UNIQUE NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

def create_student(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO students
        (name, phone, class_level, board, exam, subjects, hobbies,
         long_term_goal, sports, activity_level, study_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"], data["phone"], data["class_level"], data["board"],
        data["exam"], data["subjects"], data["hobbies"], data["long_term_goal"],
        data["sports"], data["activity_level"], data["study_hours"]
    ))
    conn.commit()
    student_id = cur.lastrowid
    conn.close()
    return student_id

def get_student_by_phone(phone):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE phone=?", (phone,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_student(student_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_student(student_id, data):
    conn = get_connection()
    conn.execute("""
        UPDATE students SET name=?, class_level=?, board=?, exam=?, subjects=?,
        hobbies=?, long_term_goal=?, sports=?, activity_level=?, study_hours=?
        WHERE id=?
    """, (
        data["name"], data["class_level"], data["board"], data["exam"],
        data["subjects"], data["hobbies"], data["long_term_goal"],
        data["sports"], data["activity_level"], data["study_hours"], student_id
    ))
    conn.commit()
    conn.close()

def add_task(student_id, task, subject, due_date, priority):
    conn = get_connection()
    conn.execute("""
        INSERT INTO tasks(student_id, task, subject, due_date, priority)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, task, subject, due_date, priority))
    conn.commit()
    conn.close()

def get_tasks(student_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM tasks WHERE student_id=?
        ORDER BY completed ASC, due_date ASC, id DESC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_task_completed(task_id, completed):
    conn = get_connection()
    conn.execute("UPDATE tasks SET completed=? WHERE id=?", (int(completed), task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def add_syllabus_item(student_id, subject, chapter, topic):
    conn = get_connection()
    conn.execute("""
        INSERT INTO syllabus(student_id, subject, chapter, topic)
        VALUES (?, ?, ?, ?)
    """, (student_id, subject, chapter, topic))
    conn.commit()
    conn.close()

def get_syllabus(student_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM syllabus WHERE student_id=?
        ORDER BY subject, chapter, topic
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_syllabus_completed(item_id, completed):
    conn = get_connection()
    conn.execute("UPDATE syllabus SET completed=? WHERE id=?", (int(completed), item_id))
    conn.commit()
    conn.close()

def add_session(student_id, subject, minutes, session_date):
    conn = get_connection()
    conn.execute("""
        INSERT INTO study_sessions(student_id, subject, minutes, session_date)
        VALUES (?, ?, ?, ?)
    """, (student_id, subject, minutes, session_date))
    conn.commit()
    conn.close()

def get_sessions(student_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM study_sessions WHERE student_id=?
        ORDER BY session_date DESC, id DESC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_question_result(student_id, subject, chapter, topic, difficulty,
                        question, correct_answer, student_answer,
                        is_correct, explanation):
    conn = get_connection()
    conn.execute("""
        INSERT INTO questions
        (student_id, subject, chapter, topic, difficulty, question,
         correct_answer, student_answer, is_correct, explanation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id, subject, chapter, topic, difficulty, question,
        correct_answer, student_answer, int(is_correct), explanation
    ))
    conn.commit()
    conn.close()

def get_question_results(student_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM questions WHERE student_id=?
        ORDER BY id DESC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_or_create_parent_code(student_id):
    import secrets
    conn = get_connection()
    row = conn.execute("SELECT code FROM parent_codes WHERE student_id=?", (student_id,)).fetchone()
    if row:
        conn.close()
        return row["code"]
    code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].upper()
    conn.execute("INSERT INTO parent_codes(student_id, code) VALUES (?, ?)", (student_id, code))
    conn.commit()
    conn.close()
    return code

def get_student_by_parent_code(code):
    conn = get_connection()
    row = conn.execute("""
        SELECT s.* FROM students s
        JOIN parent_codes p ON p.student_id=s.id
        WHERE p.code=?
    """, (code.upper().strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None
