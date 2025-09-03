# timetable-project
# 🎓 AI-Powered College Timetable Generation System

**Version:** 2.8  
**Author:** Rahat Beldar  
**Copyright © 2025 Rahat Beldar. All Rights Reserved.**

---

## 📖 Introduction (Parichay)

This is an advanced **AI-powered web application** designed to automatically generate timetables for large institutions such as engineering colleges.  
The system leverages **Google OR-Tools**, a powerful AI solver, to handle multiple challenges like faculty availability, limited classrooms, multiple departments, and elective subjects to produce an optimized timetable.

---

## ✨ Features (Khaasiyat)

- **🌐 Web-Based User Interface** – Simple UI to upload and manage CSV files.  
- **🗄️ Centralized Database** – All data stored in **SQLite**, making management easy.  
- **🤖 Powerful AI Core** – Uses **Google OR-Tools** to solve complex scheduling problems.  
- **📚 Advanced Constraints** – Handles first-year to final-year courses, shared faculty, and electives.  
- **⚠️ Conflict Analysis** – Detects missing/invalid data and provides error messages (e.g., *“Is subject ke liye koi teacher nahi hai”*).  
- **📊 Excel Export** – Generates complete timetable with separate sheets for courses and faculty.  
- **📂 Sample Data** – Sample CSV files available to help users understand the format.

---

## 🛠️ Technology Stack (Takneek)

- **Backend:** Python, Flask  
- **Frontend:** HTML, CSS, JavaScript  
- **Database:** SQLite  
- **AI Solver:** Google OR-Tools (`ortools`)  
- **Data Handling:** Pandas  

---

## ⚙️ Setup and Installation (Kaise Install Karein)

Follow these steps to run the project on your local system:

### Step 1: Prerequisites
Ensure you have **Python 3.8 or higher** installed on your computer.

### Step 2: Project Download
Download or clone this repository:

```bash
git clone https://github.com/rahatbeldar/timetable-project.git
cd timetable-project
### Step 3: Install Dependencies
Run this command inside the project folder:

pip install -r requirements.txt

###Step 4: Initialize Database
Run this command once to create the database (timetable.db):

flask init-db

Step 5: Start the Application

Run the development server:

flask run


##You will see an output with a local URL, e.g. http://127.0.0.1:5000.

###🚀 How to Use (Kaise Istemal Karein)

Open the web app in your browser → http://127.0.0.1:5000

Initially, all tables will be empty.

For each tab (Courses, Subjects, Faculty, etc.):

Click Download Sample CSV to see the correct format.

Prepare your CSV files accordingly.

Upload CSV files using the Upload CSV button.

Once all data is uploaded, click Generate Timetable.

Monitor progress in the log panel.

When done, download the generated Excel timetable.

📜 Copyright and License

This project is proprietary and confidential.
Copyright © 2025 Rahat Beldar. All Rights Reserved.

Unauthorized copying, distribution, or use of this software, via any medium, is strictly prohibited.

