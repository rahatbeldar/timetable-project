# AI-Based Timetable Generation System - Version 2.8 (Data Validation)
# Yeh script database se data padhti hai aur timetable generate karti hai.

import pandas as pd
import sqlite3
from ortools.sat.python import cp_model
import collections
import sys

# Database ka path
DB_PATH = 'timetable.db'

def sanitize_sheet_name(name):
    """Removes invalid characters and shortens the name for a valid Excel sheet name."""
    invalid_chars = ['*', ':', '/', '\\', '?', '[', ']']
    clean_name = name
    for char in invalid_chars:
        clean_name = clean_name.replace(char, '')
    return clean_name[:31]

def load_data_from_db():
    """Database se data load karke DataFrames return karta hai."""
    try:
        conn = sqlite3.connect(DB_PATH)
        courses = pd.read_sql_query("SELECT * from courses", conn)
        subjects = pd.read_sql_query("SELECT * from subjects", conn)
        faculty = pd.read_sql_query("SELECT * from faculty", conn)
        rooms = pd.read_sql_query("SELECT * from rooms", conn)
        labs = pd.read_sql_query("SELECT * from labs", conn)
        conn.close()
        
        for col in ['lecture_hours', 'lab_hours']:
            subjects[col] = pd.to_numeric(subjects[col], errors='coerce').fillna(0).astype(int)

        print("Database se data safaltapoorvak load aur clean ho gaya.")

        if 'is_elective' not in subjects.columns:
            subjects['is_elective'] = 'N'
        if 'elective_group' not in subjects.columns:
            subjects['elective_group'] = ''
            
        return courses, subjects, faculty, rooms, labs
    except Exception as e:
        print(f"Error: Database se data load nahi ho saka: {e}", file=sys.stderr)
        return None

def analyze_infeasibility(courses, subjects, faculty, rooms, labs):
    """
    Jab solver solution nahi dhoondh pata, tab yeh function data ka analysis karke
    samasya ki ਸੰਭਾਵਿਤ (potential) vajah batata hai.
    """
    report = collections.defaultdict(list)
    
    # Jaanch 1: Kya kisi subject ke liye faculty nahi hai?
    for _, subject in subjects.iterrows():
        possible_faculty = faculty[faculty['subjects'].str.contains(subject['subject_id'], na=False, regex=False)]
        if possible_faculty.empty:
            report["Faculty Unassigned"].append(f"Subject '{subject['subject_name']}' ({subject['subject_id']}) ko padhane ke liye koi faculty nahi hai.")

    # Jaanch 2: Kya kisi lab subject ke liye lab room nahi hai?
    lab_subjects = subjects[subjects['lab_hours'] > 0]
    for _, subject in lab_subjects.iterrows():
        possible_labs = labs[labs['subject_id'].str.contains(subject['subject_id'], na=False, regex=False)]
        if possible_labs.empty:
            report["Lab Unassigned"].append(f"Lab Subject '{subject['subject_name']}' ({subject['subject_id']}) ke liye koi lab room assign nahi kiya gaya hai.")
            
    # Jaanch 3: Kya zaroori ghante (hours) uplabdh slots se zyada hain?
    total_required_lectures = subjects['lecture_hours'].sum()
    total_required_labs = subjects['lab_hours'].sum()
    total_available_room_slots = len(rooms) * len(DAYS) * AVAILABLE_SLOTS_PER_DAY
    total_available_lab_slots = len(labs) * len(DAYS) * AVAILABLE_SLOTS_PER_DAY

    if total_required_lectures > total_available_room_slots:
        report["Resource Shortage"].append(f"Zaroori Lecture Slots ({total_required_lectures}) Uplabdh Room Slots ({total_available_room_slots}) se zyada hain. Aur classrooms jodein.")
    if total_required_labs > total_available_lab_slots:
        report["Resource Shortage"].append(f"Zaroori Lab Slots ({total_required_labs}) Uplabdh Lab Slots ({total_available_lab_slots}) se zyada hain. Aur labs jodein.")

    return report

# --- Timetable Configuration ---
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
SLOT_TIMES = {
    0: "09:00 - 10:00", 1: "10:00 - 11:00", 2: "11:15 - 12:15", 3: "12:15 - 01:15",
    4: "02:00 - 03:00", 5: "03:00 - 04:00", 6: "04:00 - 05:00"
}
AVAILABLE_SLOTS_PER_DAY = len(SLOT_TIMES)

def main():
    data = load_data_from_db()
    if data is None: return
    courses, subjects, faculty, rooms, labs = data

    # --- NAYA DATA VALIDATION SYSTEM ---
    # Jaanch karein ki zaroori data maujood hai ya nahi.
    if courses.empty:
        print("CRITICAL ERROR: 'Courses' ka data nahi mila. Kripya courses.csv upload karein.", file=sys.stderr)
        return
    if subjects.empty:
        print("CRITICAL ERROR: 'Subjects' ka data nahi mila. Kripya subjects.csv upload karein.", file=sys.stderr)
        return
    if faculty.empty:
        print("CRITICAL ERROR: 'Faculty' ka data nahi mila. Kripya faculty.csv upload karein.", file=sys.stderr)
        return
    if rooms.empty:
        print("CRITICAL ERROR: 'Classrooms' ka data nahi mila. Kripya rooms.csv upload karein.", file=sys.stderr)
        return
    if subjects['lab_hours'].sum() > 0 and labs.empty:
        print("CRITICAL ERROR: Aapke subjects mein labs hain, lekin 'Labs' ka data nahi mila. Kripya labs.csv upload karein.", file=sys.stderr)
        return

    model = cp_model.CpModel()
    assignments = {}

    # --- Variables Definition ---
    for _, subject_row in subjects.iterrows():
        course_id, subject_id = subject_row['course_id'], subject_row['subject_id']
        possible_faculty = faculty[faculty['subjects'].str.contains(subject_id, na=False, regex=False)]['faculty_id'].tolist()
        
        for fac in possible_faculty:
            for day_idx in range(len(DAYS)):
                for slot_idx in range(AVAILABLE_SLOTS_PER_DAY):
                    if subject_row['lecture_hours'] > 0:
                        for room in rooms['room_id']:
                            key = (course_id, subject_id, fac, day_idx, slot_idx, room, "Lecture")
                            assignments[key] = model.NewBoolVar(''.join(map(str,key)).replace('-', '_'))
                    if subject_row['lab_hours'] > 0:
                        possible_labs = labs[labs['subject_id'].str.contains(subject_id, na=False, regex=False)]['lab_id'].tolist()
                        for lab in possible_labs:
                            key = (course_id, subject_id, fac, day_idx, slot_idx, lab, "Lab")
                            assignments[key] = model.NewBoolVar(''.join(map(str,key)).replace('-', '_'))

    # --- Constraints ---
    core_subjects = subjects[subjects['is_elective'] == 'N']
    for _, subject_row in core_subjects.iterrows():
         course_id, subject_id = subject_row['course_id'], subject_row['subject_id']
         if subject_row['lecture_hours'] > 0:
            model.Add(sum(assignments[k] for k in assignments if k[0]==course_id and k[1]==subject_id and k[6]=="Lecture") == subject_row['lecture_hours'])
         if subject_row['lab_hours'] > 0:
            model.Add(sum(assignments[k] for k in assignments if k[0]==course_id and k[1]==subject_id and k[6]=="Lab") == subject_row['lab_hours'])
    elective_subjects = subjects[subjects['is_elective'] == 'Y']
    for course_id in elective_subjects['course_id'].unique():
        course_electives = elective_subjects[elective_subjects['course_id'] == course_id]
        for group in course_electives['elective_group'].unique():
            group_subjects = course_electives[course_electives['elective_group'] == group]
            chosen_vars = {sub_id: model.NewBoolVar(f'chosen_{course_id}_{group}_{sub_id}'.replace('-', '_')) for sub_id in group_subjects['subject_id']}
            model.AddExactlyOne(chosen_vars.values())
            for _, subject_row in group_subjects.iterrows():
                sub_id = subject_row['subject_id']
                if subject_row['lecture_hours'] > 0:
                    model.Add(sum(assignments[k] for k in assignments if k[0]==course_id and k[1]==sub_id and k[6]=="Lecture") == subject_row['lecture_hours']).OnlyEnforceIf(chosen_vars[sub_id])
                    model.Add(sum(assignments[k] for k in assignments if k[0]==course_id and k[1]==sub_id and k[6]=="Lecture") == 0).OnlyEnforceIf(chosen_vars[sub_id].Not())
                if subject_row['lab_hours'] > 0:
                    model.Add(sum(assignments[k] for k in assignments if k[0]==course_id and k[1]==sub_id and k[6]=="Lab") == subject_row['lab_hours']).OnlyEnforceIf(chosen_vars[sub_id])
                    model.Add(sum(assignments[k] for k in assignments if k[0]==course_id and k[1]==sub_id and k[6]=="Lab") == 0).OnlyEnforceIf(chosen_vars[sub_id].Not())
    all_courses = courses['course_id'].tolist(); all_faculty = faculty['faculty_id'].tolist(); all_rooms = rooms['room_id'].tolist(); all_labs = labs['lab_id'].tolist()
    for day_idx in range(len(DAYS)):
        for slot_idx in range(AVAILABLE_SLOTS_PER_DAY):
            for course_id in all_courses:
                 model.AddAtMostOne(assignments[key] for key in assignments if key[0]==course_id and key[3]==day_idx and key[4]==slot_idx)
            for fac in all_faculty:
                model.AddAtMostOne(assignments[key] for key in assignments if key[2]==fac and key[3]==day_idx and key[4]==slot_idx)
            for room in all_rooms:
                model.AddAtMostOne(assignments[key] for key in assignments if key[5]==room and key[3]==day_idx and key[4]==slot_idx and key[6]=='Lecture')
            for lab in all_labs:
                model.AddAtMostOne(assignments[key] for key in assignments if key[5]==lab and key[3]==day_idx and key[4]==slot_idx and key[6]=='Lab')

    # --- Solver & Results ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print('Ek feasible solution mil gaya!')
        with pd.ExcelWriter('timetable_output.xlsx', engine='openpyxl') as writer:
            for _, course_row in courses.iterrows():
                course_id = course_row['course_id']
                df = pd.DataFrame(index=[SLOT_TIMES[i] for i in range(AVAILABLE_SLOTS_PER_DAY)], columns=DAYS)
                for key, var in assignments.items():
                    if solver.Value(var) == 1 and key[0] == course_id:
                        day, slot = key[3], key[4]
                        sub_name = subjects.loc[subjects['subject_id'] == key[1], 'subject_name'].iloc[0]
                        fac_name = faculty.loc[faculty['faculty_id'] == key[2], 'faculty_name'].iloc[0]
                        loc, type = key[5], key[6]
                        df.loc[SLOT_TIMES[slot], DAYS[day]] = f"{sub_name}\n({fac_name})\n@{loc} [{type}]"
                sheet_name = sanitize_sheet_name(f"C_{course_id}")
                df.to_excel(writer, sheet_name=sheet_name)
            
            for _, fac_row in faculty.iterrows():
                fac_id, fac_name = fac_row['faculty_id'], fac_row['faculty_name']
                df = pd.DataFrame(index=[SLOT_TIMES[i] for i in range(AVAILABLE_SLOTS_PER_DAY)], columns=DAYS)
                for key, var in assignments.items():
                    if solver.Value(var) == 1 and key[2] == fac_id:
                        day, slot = key[3], key[4]
                        course_name = courses.loc[courses['course_id'] == key[0], 'course_name'].iloc[0]
                        sub_name = subjects.loc[subjects['subject_id'] == key[1], 'subject_name'].iloc[0]
                        loc, type = key[5], key[6]
                        df.loc[SLOT_TIMES[slot], DAYS[day]] = f"{sub_name}\n({course_name})\n@{loc} [{type}]"
                sheet_name = sanitize_sheet_name(f"F_{fac_name}")
                df.to_excel(writer, sheet_name=sheet_name)
        print("\nTimetable 'timetable_output.xlsx' file mein generate ho gaya hai.")
    else:
        print('KOI FEASIBLE SOLUTION NAHI MILA. Data mein samasya ho sakti hai.', file=sys.stderr)
        report = analyze_infeasibility(courses, subjects, faculty, rooms, labs)
        if not report:
            print("Basic analysis mein koi saaf samasya nahi mili. Ho sakta hai ki constraints bahut zyada sakht hon (jaise ek hi faculty ke liye bahut zyada classes).", file=sys.stderr)
        else:
            print("\n--- CONFLICT REPORT ---", file=sys.stderr)
            for category, messages in report.items():
                print(f"\n* {category}:", file=sys.stderr)
                for msg in messages:
                    print(f"  - {msg}", file=sys.stderr)
            print("-----------------------", file=sys.stderr)

if __name__ == '__main__':
    main()

