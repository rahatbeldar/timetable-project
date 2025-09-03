# Flask Web App for AI Timetable Generator
# Yeh backend server hai jo data management aur timetable generation ko handle karta hai.

import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import subprocess # To run the generator script

# Flask App Configuration
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'csv'}
DB_PATH = 'timetable.db'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to get DB connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- Main Route ---
@app.route('/')
def index():
    """Home page render karta hai."""
    return render_template('index.html')

# --- API Routes for Data Management ---

@app.route('/api/data/<table_name>', methods=['GET'])
def get_data(table_name):
    """Database se data fetch karke JSON format mein bhejta hai."""
    conn = get_db_connection()
    try:
        data = conn.execute(f'SELECT * FROM {table_name}').fetchall()
        conn.close()
        return jsonify([dict(row) for row in data])
    except sqlite3.OperationalError:
        return jsonify({"error": "Table not found"}), 404

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """CSV files ko upload karke database ko update karta hai."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    table_name = request.form.get('table_name')
    if not table_name:
        return jsonify({"error": "Table name is missing"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # CSV data se database table ko update/replace karein
        try:
            df = pd.read_csv(filepath)
            conn = get_db_connection()
            # 'if_exists='replace'' se purana data hat jayega aur naya aa jayega
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            return jsonify({"message": f"'{filename}' safaltapoorvak upload hua aur {table_name} table update ho gayi."})
        except Exception as e:
            return jsonify({"error": f"File process karne mein error: {str(e)}"}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/generate', methods=['POST'])
def generate_timetable():
    """Timetable generator script ko run karta hai."""
    print("Timetable generation request prapt hui.")
    try:
        # Hum ek alag process mein script chalate hain taaki web server block na ho.
        # 'capture_output=True' se hum script ka output (print statements/errors) le sakte hain.
        result = subprocess.run(
            ['python', 'timetable_generator_db.py'],
            capture_output=True,
            text=True,
            check=True # Agar script error se fail hoti hai to exception raise karega
        )
        # Script ka output (stdout) frontend ko bhejein
        return jsonify({"message": "Timetable safaltapoorvak generate hua!", "log": result.stdout, "output_file": "timetable_output.xlsx"})
    except subprocess.CalledProcessError as e:
        # Script fail hone par, error (stderr) bhejein
        return jsonify({"error": "Timetable generate karne mein error aayi.", "log": e.stderr + "\n" + e.stdout}), 500
    except FileNotFoundError:
        return jsonify({"error": "timetable_generator_db.py script nahi mili."}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Generated file ya sample data ko download ke liye bhejta hai."""
    directory = '.'
    if 'sample' in filename:
        directory = os.path.join('data', 'samples')
        filename = filename.replace('sample_', '') # 'sample_courses.csv' -> 'courses.csv'

    return send_from_directory(directory=directory, path=filename, as_attachment=True)


# --- Database Initialization ---
@app.cli.command('init-db')
def init_db_command():
    """Database ko initialize karta hai."""
    from database import init_db
    init_db()
    print('Database initialize ho gaya.')

if __name__ == '__main__':
    # Pehle check karein ki data folder hai ya nahi
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # App run karein
    app.run(debug=True)
