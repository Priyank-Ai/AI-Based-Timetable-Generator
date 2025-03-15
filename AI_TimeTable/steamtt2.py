import streamlit as st
import pandas as pd
import random

# Constants
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
TIME_SLOTS = ["1", "2", "3", "4", "break", "5", "6"]  # Including break
FACULTY_MIN_HOURS = 20
FACULTY_MAX_HOURS = 22
SUBJECT_HOURS_PER_CLASS = 7  # Each class must have 7 hours per subject
POPULATION_SIZE = 50
GENERATIONS = 1000
MUTATION_RATE = 0.01

# Streamlit UI
st.title("AI-Based Timetable Generator")

# User input for subjects
num_subjects = st.number_input("Enter the number of subjects:", min_value=1, step=1)
courses = []
for i in range(num_subjects):
    name = st.text_input(f"Enter name of Subject {i + 1}", key=f"subject_{i}")
    courses.append({"id": i, "name": name, "hours": SUBJECT_HOURS_PER_CLASS})

# User input for faculties
num_faculties = st.number_input("Enter the number of faculties:", min_value=1, step=1)
faculties = []
faculty_courses = {}
faculty_hours = {i: 0 for i in range(num_faculties)}

for i in range(num_faculties):
    faculty_input = st.text_input(f"Enter name and subjects for Faculty {i + 1} (format: 'Faculty Name: Subject1, Subject2, ...')", key=f"faculty_{i}")
    if ":" in faculty_input:
        name, subjects = faculty_input.split(':', 1)
        subjects = [s.strip() for s in subjects.split(',') if s.strip()]
        faculties.append({"id": i, "name": name, "subjects": subjects, "max_daily": 4})
        for subject in subjects:
            if subject not in faculty_courses:
                faculty_courses[subject] = []
            faculty_courses[subject].append(i)

# User input for rooms (Considered as classes)
num_classes = st.number_input("Enter the number of classes:", min_value=1, step=1)
classes = []
for i in range(num_classes):
    class_name = st.text_input(f"Enter name of Class {i + 1}", key=f"class_{i}")
    classes.append({"id": i, "name": class_name})

# Genetic Algorithm Components
def initialize_population():
    population = []
    for _ in range(POPULATION_SIZE):
        schedule = []
        occupied_slots = {class_["name"]: {day: set() for day in DAYS} for class_ in classes}
        for class_ in classes:
            for course in courses:
                for _ in range(SUBJECT_HOURS_PER_CLASS):
                    assigned_faculty = random.choice(faculty_courses.get(course["name"], [])) if course["name"] in faculty_courses else None
                    day = random.choice(DAYS)
                    available_slots = [s for s in TIME_SLOTS if s not in occupied_slots[class_["name"]][day] and s != "break"]
                    if available_slots:
                        slot = random.choice(available_slots)
                        occupied_slots[class_["name"]][day].add(slot)
                        schedule.append({"class": class_["name"], "subject": course["name"], "faculty": faculties[assigned_faculty]["name"] if assigned_faculty is not None else "", "day": day, "time": slot})
        population.append(schedule)
    return population

def fitness(schedule):
    score = 0
    faculty_workload = {f["name"]: 0 for f in faculties}
    for entry in schedule:
        if entry["faculty"]:
            faculty_workload[entry["faculty"]] += 1
    score += sum(1 for hours in faculty_workload.values() if FACULTY_MIN_HOURS <= hours <= FACULTY_MAX_HOURS)
    return score

def mutate(schedule):
    if random.random() < MUTATION_RATE:
        random.shuffle(schedule)
    return schedule

def generate_timetable():
    population = initialize_population()
    for _ in range(GENERATIONS):
        population = sorted(population, key=fitness, reverse=True)
        population = population[:POPULATION_SIZE//2] + [mutate(ind) for ind in population[:POPULATION_SIZE//2]]
    return population[0]

if st.button("Generate Timetable"):
    best_timetable = generate_timetable()
    class_timetable = {class_["name"]: {day: {slot: "" for slot in TIME_SLOTS} for day in DAYS} for class_ in classes}
    faculty_timetable = {faculty["name"]: {day: {slot: "" for slot in TIME_SLOTS} for day in DAYS} for faculty in faculties}
    faculty_workload = {faculty["name"]: 0 for faculty in faculties}
    conflicts = []

    for entry in best_timetable:
        if class_timetable[entry["class"]][entry["day"]][entry["time"]]:
            conflicts.append(f"Conflict in {entry['class']} on {entry['day']} at {entry['time']}")
        else:
            class_timetable[entry["class"]][entry["day"]][entry["time"]] = f"{entry['subject']} ({entry['faculty']})"
            faculty_timetable[entry["faculty"]][entry["day"]][entry["time"]] = f"{entry['subject']} ({entry['class']})"
            faculty_workload[entry["faculty"]] += 1

    # Display Conflict Report
    st.subheader("Conflict and Constraint Violation Report")
    if conflicts:
        for conflict in conflicts:
            st.write(conflict)
    else:
        st.write("No conflicts found.")

    # Display Class-wise Timetables
    st.subheader("Class-wise Timetables")
    for class_name, timetable in class_timetable.items():
        st.write(f"### {class_name} Timetable")
        df = pd.DataFrame.from_dict(timetable, orient="index")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Days"}, inplace=True)
        st.dataframe(df)

    # Display Faculty-wise Timetables
    st.subheader("Faculty-wise Timetables")
    for faculty_name, timetable in faculty_timetable.items():
        st.write(f"### {faculty_name} Timetable ({faculty_workload[faculty_name]} hours/week)")
        df = pd.DataFrame.from_dict(timetable, orient="index")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Days"}, inplace=True)
        st.dataframe(df)

    # Generate Faculty Workload Report
    st.subheader("Faculty Workload Report")
    workload_df = pd.DataFrame.from_dict(faculty_workload, orient='index', columns=['Total Hours']).reset_index()
    workload_df.rename(columns={"index": "Faculty Name"}, inplace=True)
    st.dataframe(workload_df)
