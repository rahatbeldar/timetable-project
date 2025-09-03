import sqlite3

def init_db():
    """
    SQLite database aur zaroori tables banata hai.
    Agar tables pehle se hain to unhein drop karke naya banata hai.
    """
    conn = sqlite3.connect('timetable.db')
    cursor = conn.cursor()

    # Purani tables ko drop karein
    tables = ['courses', 'subjects', 'faculty', 'rooms', 'labs']
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # Nayi tables create karein
    cursor.execute('''
    CREATE TABLE courses (
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE subjects (
        subject_id TEXT PRIMARY KEY,
        subject_name TEXT NOT NULL,
        course_id TEXT NOT NULL,
        lecture_hours INTEGER NOT NULL,
        lab_hours INTEGER NOT NULL,
        is_elective TEXT,
        elective_group TEXT,
        FOREIGN KEY (course_id) REFERENCES courses (course_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE faculty (
        faculty_id TEXT PRIMARY KEY,
        faculty_name TEXT NOT NULL,
        subjects TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE rooms (
        room_id TEXT PRIMARY KEY
    )
    ''')

    cursor.execute('''
    CREATE TABLE labs (
        lab_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database 'timetable.db' safaltapoorvak ban gaya.")
