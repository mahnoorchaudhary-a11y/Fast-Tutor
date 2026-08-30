import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# ============================================================
# FAST TUTOR
# Student Marks, Results & Academic Management System
# ============================================================

st.set_page_config(
    page_title="Fast Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "fast_tutor.db"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


conn = get_connection()


def execute(query, params=(), fetch=False, many=False):
    try:
        cursor = conn.cursor()

        if many:
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)

        conn.commit()

        if fetch:
            return cursor.fetchall()

        return True

    except sqlite3.IntegrityError as e:
        conn.rollback()
        st.error(f"Database integrity error: {e}")
        return False

    except sqlite3.Error as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return False


def initialize_database():

    execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            program TEXT,
            semester TEXT,
            section TEXT,
            created_at TEXT
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            credit_hours REAL DEFAULT 0,
            semester TEXT,
            created_at TEXT
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_name TEXT NOT NULL,
            total_marks REAL DEFAULT 100,
            created_at TEXT
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            course_code TEXT NOT NULL,
            assessment TEXT NOT NULL,
            obtained_marks REAL DEFAULT 0,
            total_marks REAL DEFAULT 100,
            percentage REAL DEFAULT 0,
            grade TEXT,
            entered_at TEXT,
            UNIQUE(roll_no, course_code, assessment)
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_name TEXT UNIQUE NOT NULL
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            institute_name TEXT,
            semester TEXT,
            academic_year TEXT
        )
    """)


initialize_database()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_grade(percentage):

    if percentage >= 90:
        return "A+"
    elif percentage >= 85:
        return "A"
    elif percentage >= 80:
        return "A-"
    elif percentage >= 75:
        return "B+"
    elif percentage >= 70:
        return "B"
    elif percentage >= 65:
        return "B-"
    elif percentage >= 60:
        return "C+"
    elif percentage >= 55:
        return "C"
    elif percentage >= 50:
        return "C-"
    elif percentage >= 45:
        return "D"
    else:
        return "F"


def safe_float(value, default=0):

    try:
        if pd.isna(value):
            return default
        return float(value)
    except:
        return default


def normalize_column_name(name):

    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def find_column(df, possible_names):

    normalized = {
        normalize_column_name(col): col
        for col in df.columns
    }

    for name in possible_names:

        key = normalize_column_name(name)

        if key in normalized:
            return normalized[key]

    return None


def load_students():

    rows = execute("""
        SELECT id, roll_no, student_name, program, semester, section
        FROM students
        ORDER BY roll_no
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Roll Number",
            "Student Name",
            "Program",
            "Semester",
            "Section"
        ]
    )


def load_courses():

    rows = execute("""
        SELECT id, course_code, course_name, credit_hours, semester
        FROM courses
        ORDER BY course_code
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Course Code",
            "Course Name",
            "Credit Hours",
            "Semester"
        ]
    )


def load_results():

    rows = execute("""
        SELECT
            r.id,
            r.roll_no,
            s.student_name,
            r.course_code,
            c.course_name,
            r.assessment,
            r.obtained_marks,
            r.total_marks,
            r.percentage,
            r.grade
        FROM results r
        LEFT JOIN students s
            ON r.roll_no = s.roll_no
        LEFT JOIN courses c
            ON r.course_code = c.course_code
        ORDER BY r.roll_no, r.course_code
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Roll Number",
            "Student Name",
            "Course Code",
            "Course Name",
            "Assessment",
            "Obtained Marks",
            "Total Marks",
            "Percentage",
            "Grade"
        ]
    )


# ============================================================
# HEADER / BRANDING
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 0;
}

.subtitle {
    font-size: 18px;
    color: #666;
    margin-bottom: 25px;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: #f7f7f7;
    border: 1px solid #ddd;
    text-align: center;
}

.card-number {
    font-size: 32px;
    font-weight: 800;
}

.card-label {
    font-size: 16px;
    color: #666;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    "<h1 style='text-align:center;'>🎓 Fast Tutor</h1>",
    unsafe_allow_html=True
)

st.sidebar.markdown(
    "<p style='text-align:center;'>Student Academic Management</p>",
    unsafe_allow_html=True
)

st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "👨‍🎓 Students",
        "📚 Courses",
        "📝 Assessments",
        "📥 Bulk Student Import",
        "📊 Bulk Marks Upload",
        "📈 Results",
        "📋 Student Transcript",
        "📊 Performance Analysis",
        "📤 Import / Export",
        "⚙️ Settings"
    ]
)

st.sidebar.divider()

st.sidebar.caption("Fast Tutor")
st.sidebar.caption("Student Marks & Results Management")


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        "<div class='main-title'>🎓 Fast Tutor</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='subtitle'>Student Marks, Results & Academic Management System</div>",
        unsafe_allow_html=True
    )

    students_count = execute(
        "SELECT COUNT(*) FROM students",
        fetch=True
    )[0][0]

    courses_count = execute(
        "SELECT COUNT(*) FROM courses",
        fetch=True
    )[0][0]

    results_count = execute(
        "SELECT COUNT(*) FROM results",
        fetch=True
    )[0][0]

    assessments_count = execute(
        "SELECT COUNT(*) FROM assessments",
        fetch=True
    )[0][0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👨‍🎓 Students", students_count)

    with col2:
        st.metric("📚 Courses", courses_count)

    with col3:
        st.metric("📝 Assessments", assessments_count)

    with col4:
        st.metric("📊 Results", results_count)

    st.divider()

    results_df = load_results()

    if not results_df.empty:

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("📈 Average Course Performance")

            course_average = (
                results_df
                .groupby("Course Code")["Percentage"]
                .mean()
                .sort_values(ascending=False)
            )

            st.bar_chart(course_average)

        with col2:

            st.subheader("🎯 Grade Distribution")

            grade_distribution = (
                results_df["Grade"]
                .value_counts()
                .sort_index()
            )

            st.bar_chart(grade_distribution)

    else:

        st.info(
            "No results have been uploaded yet. "
            "Use 'Bulk Marks Upload' to upload student marks."
        )

    st.divider()

    st.subheader("⚡ Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:

        if st.button("📥 Import Students", use_container_width=True):
            st.info("Open 'Bulk Student Import' from the sidebar.")

    with col2:

        if st.button("📊 Upload Marks", use_container_width=True):
            st.info("Open 'Bulk Marks Upload' from the sidebar.")

    with col3:

        if st.button("📈 View Results", use_container_width=True):
            st.info("Open 'Results' from the sidebar.")


# ============================================================
# STUDENTS
# ============================================================

elif page == "👨‍🎓 Students":

    st.title("👨‍🎓 Student Management")

    tab1, tab2 = st.tabs([
        "Student List",
        "Add Student"
    ])

    with tab1:

        students_df = load_students()

        if students_df.empty:
            st.info("No students have been added yet.")
        else:

            st.dataframe(
                students_df,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ Download Student List",
                students_df.to_csv(index=False).encode("utf-8"),
                "fast_tutor_students.csv",
                "text/csv"
            )

    with tab2:

        with st.form("add_student_form"):

            roll_no = st.text_input(
                "Roll Number",
                placeholder="e.g. CS-001"
            )

            student_name = st.text_input(
                "Student Name",
                placeholder="e.g. Ali Ahmed"
            )

            program = st.text_input(
                "Program",
                placeholder="e.g. BS Computer Science"
            )

            semester = st.text_input(
                "Semester",
                placeholder="e.g. 1"
            )

            section = st.text_input(
                "Section",
                placeholder="e.g. A"
            )

            submitted = st.form_submit_button(
                "➕ Add Student",
                use_container_width=True
            )

        if submitted:

            if not roll_no or not student_name:

                st.error(
                    "Roll Number and Student Name are required."
                )

            else:

                success = execute("""
                    INSERT INTO students
                    (roll_no, student_name, program, semester, section, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    roll_no.strip(),
                    student_name.strip(),
                    program.strip(),
                    semester.strip(),
                    section.strip(),
                    datetime.now().isoformat()
                ))

                if success:
                    st.success("Student added successfully.")
                    st.rerun()


# ============================================================
# COURSES
# ============================================================

elif page == "📚 Courses":

    st.title("📚 Course Management")

    tab1, tab2 = st.tabs([
        "Course List",
        "Add Course"
    ])

    with tab1:

        courses_df = load_courses()

        if courses_df.empty:
            st.info("No courses have been added.")
        else:

            st.dataframe(
                courses_df,
                use_container_width=True,
                hide_index=True
            )

    with tab2:

        with st.form("course_form"):

            course_code = st.text_input(
                "Course Code",
                placeholder="CS101"
            )

            course_name = st.text_input(
                "Course Name",
                placeholder="Programming Fundamentals"
            )

            credit_hours = st.number_input(
                "Credit Hours",
                min_value=0.0,
                max_value=10.0,
                value=3.0,
                step=0.5
            )

            semester = st.text_input(
                "Semester",
                placeholder="1"
            )

            submitted = st.form_submit_button(
                "➕ Add Course",
                use_container_width=True
            )

        if submitted:

            if not course_code or not course_name:

                st.error(
                    "Course Code and Course Name are required."
                )

            else:

                success = execute("""
                    INSERT INTO courses
                    (course_code, course_name, credit_hours, semester, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    course_code.strip().upper(),
                    course_name.strip(),
                    credit_hours,
                    semester.strip(),
                    datetime.now().isoformat()
                ))

                if success:
                    st.success("Course added successfully.")
                    st.rerun()


# ============================================================
# ASSESSMENTS
# ============================================================

elif page == "📝 Assessments":

    st.title("📝 Assessment Management")

    tab1, tab2 = st.tabs([
        "Assessment List",
        "Add Assessment"
    ])

    with tab1:

        rows = execute("""
            SELECT id, assessment_name, total_marks, created_at
            FROM assessments
            ORDER BY id DESC
        """, fetch=True)

        assessment_df = pd.DataFrame(
            rows,
            columns=[
                "ID",
                "Assessment",
                "Total Marks",
                "Created At"
            ]
        )

        if assessment_df.empty:
            st.info("No assessments created.")
        else:
            st.dataframe(
                assessment_df,
                use_container_width=True,
                hide_index=True
            )

    with tab2:

        with st.form("assessment_form"):

            assessment_name = st.text_input(
                "Assessment Name",
                placeholder="Midterm Examination"
            )

            total_marks = st.number_input(
                "Total Marks",
                min_value=1.0,
                value=100.0
            )

            submitted = st.form_submit_button(
                "➕ Add Assessment",
                use_container_width=True
            )

        if submitted:

            if not assessment_name:

                st.error("Assessment name is required.")

            else:

                success = execute("""
                    INSERT INTO assessments
                    (assessment_name, total_marks, created_at)
                    VALUES (?, ?, ?)
                """, (
                    assessment_name.strip(),
                    total_marks,
                    datetime.now().isoformat()
                ))

                if success:
                    st.success("Assessment added.")
                    st.rerun()


# ============================================================
# BULK STUDENT IMPORT
# ============================================================

elif page == "📥 Bulk Student Import":

    st.title("📥 Bulk Student Import")

    st.write(
        "Upload one Excel or CSV file containing all your students. "
        "You do not need to enter students one by one."
    )

    st.info(
        "Recommended columns: Roll Number, Student Name, Program, "
        "Semester, Section"
    )

    sample_students = pd.DataFrame({
        "Roll Number": [
            "CS001",
            "CS002",
            "CS003"
        ],
        "Student Name": [
            "Ali Ahmed",
            "Sara Khan",
            "Usman Malik"
        ],
        "Program": [
            "BS Computer Science",
            "BS Computer Science",
            "BS Computer Science"
        ],
        "Semester": [
            "1",
            "1",
            "1"
        ],
        "Section": [
            "A",
            "A",
            "A"
        ]
    })

    st.subheader("📄 Required File Format")

    st.dataframe(
        sample_students,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Student Template",
        sample_students.to_csv(index=False).encode("utf-8"),
        "fast_tutor_student_template.csv",
        "text/csv"
    )

    uploaded_file = st.file_uploader(
        "Upload Student File",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file:

        try:

            if uploaded_file.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.subheader("Preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True
            )

            roll_col = find_column(
                df,
                [
                    "roll number",
                    "roll_no",
                    "roll",
                    "registration number",
                    "registration_no",
                    "student id",
                    "student_id"
                ]
            )

            name_col = find_column(
                df,
                [
                    "student name",
                    "student_name",
                    "name",
                    "student"
                ]
            )

            program_col = find_column(
                df,
                [
                    "program",
                    "degree",
                    "programme"
                ]
            )

            semester_col = find_column(
                df,
                [
                    "semester",
                    "sem"
                ]
            )

            section_col = find_column(
                df,
                [
                    "section",
                    "class",
                    "group"
                ]
            )

            if not roll_col:

                st.error(
                    "Could not find a Roll Number column."
                )

            elif not name_col:

                st.error(
                    "Could not find a Student Name column."
                )

            else:

                st.success(
                    f"Detected Roll Number: {roll_col} | "
                    f"Student Name: {name_col}"
                )

                if st.button(
                    "🚀 IMPORT ALL STUDENTS",
                    type="primary",
                    use_container_width=True
                ):

                    inserted = 0
                    updated = 0
                    skipped = 0

                    for _, row in df.iterrows():

                        roll = str(row[roll_col]).strip()

                        name = str(row[name_col]).strip()

                        if (
                            not roll
                            or roll.lower() == "nan"
                            or not name
                            or name.lower() == "nan"
                        ):
                            skipped += 1
                            continue

                        program = ""

                        if program_col:
                            program = str(
                                row[program_col]
                            ).strip()

                        semester = ""

                        if semester_col:
                            semester = str(
                                row[semester_col]
                            ).strip()

                        section = ""

                        if section_col:
                            section = str(
                                row[section_col]
                            ).strip()

                        existing = execute("""
                            SELECT id
                            FROM students
                            WHERE roll_no = ?
                        """, (roll,), fetch=True)

                        if existing:

                            execute("""
                                UPDATE students
                                SET student_name = ?,
                                    program = ?,
                                    semester = ?,
                                    section = ?
                                WHERE roll_no = ?
                            """, (
                                name,
                                program,
                                semester,
                                section,
                                roll
                            ))

                            updated += 1

                        else:

                            success = execute("""
                                INSERT INTO students
                                (roll_no, student_name, program,
                                 semester, section, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                roll,
                                name,
                                program,
                                semester,
                                section,
                                datetime.now().isoformat()
                            ))

                            if success:
                                inserted += 1
                            else:
                                skipped += 1

                    st.success(
                        f"Import complete: {inserted} new students, "
                        f"{updated} updated, {skipped} skipped."
                    )

                    st.rerun()

        except Exception as e:

            st.error(
                f"Could not read the file: {e}"
            )


# ============================================================
# BULK MARKS UPLOAD
# ============================================================

elif page == "📊 Bulk Marks Upload":

    st.title("📊 Bulk Marks Upload")

    st.write(
        "Upload all student marks at once using Excel or CSV. "
        "You do NOT need to enter marks individually."
    )

    st.warning(
        "Make sure the Roll Number in the marks file matches "
        "the Roll Number in the student database."
    )

    st.subheader("📄 Recommended Marks File")

    sample_marks = pd.DataFrame({
        "Roll Number": [
            "CS001",
            "CS002",
            "CS003"
        ],
        "Course Code": [
            "CS101",
            "CS101",
            "CS101"
        ],
        "Assessment": [
            "Midterm",
            "Midterm",
            "Midterm"
        ],
        "Obtained Marks": [
            78,
            85,
            64
        ],
        "Total Marks": [
            100,
            100,
            100
        ]
    })

    st.dataframe(
        sample_marks,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Marks Template",
        sample_marks.to_csv(index=False).encode("utf-8"),
        "fast_tutor_marks_template.csv",
        "text/csv"
    )

    uploaded_marks = st.file_uploader(
        "Upload Complete Marks File",
        type=["csv", "xlsx", "xls"],
        key="marks_upload"
    )

    if uploaded_marks:

        try:

            if uploaded_marks.name.lower().endswith(".csv"):
                marks_df = pd.read_csv(uploaded_marks)
            else:
                marks_df = pd.read_excel(uploaded_marks)

            st.subheader("Marks Preview")

            st.dataframe(
                marks_df.head(30),
                use_container_width=True,
                hide_index=True
            )

            roll_col = find_column(
                marks_df,
                [
                    "roll number",
                    "roll_no",
                    "roll",
                    "registration number",
                    "registration_no",
                    "student id",
                    "student_id"
                ]
            )

            course_col = find_column(
                marks_df,
                [
                    "course code",
                    "course_code",
                    "course",
                    "subject code",
                    "subject"
                ]
            )

            assessment_col = find_column(
                marks_df,
                [
                    "assessment",
                    "exam",
                    "exam type",
                    "assessment name",
                    "test",
                    "paper"
                ]
            )

            obtained_col = find_column(
                marks_df,
                [
                    "obtained marks",
                    "obtained_marks",
                    "marks obtained",
                    "marks",
                    "score",
                    "obtained"
                ]
            )

            total_col = find_column(
                marks_df,
                [
                    "total marks",
                    "total_marks",
                    "maximum marks",
                    "max marks",
                    "max_marks",
                    "total"
                ]
            )

            missing = []

            if not roll_col:
                missing.append("Roll Number")

            if not course_col:
                missing.append("Course Code")

            if not assessment_col:
                missing.append("Assessment")

            if not obtained_col:
                missing.append("Obtained Marks")

            if missing:

                st.error(
                    "Missing required columns: "
                    + ", ".join(missing)
                )

            else:

                st.success(
                    "All required columns detected."
                )

                st.write(
                    f"**Rows ready for import:** {len(marks_df)}"
                )

                if st.button(
                    "🚀 UPLOAD ALL MARKS",
                    type="primary",
                    use_container_width=True
                ):

                    inserted = 0
                    updated = 0
                    skipped = 0
                    errors = []

                    for index, row in marks_df.iterrows():

                        try:

                            roll = str(
                                row[roll_col]
                            ).strip()

                            course = str(
                                row[course_col]
                            ).strip().upper()

                            assessment = str(
                                row[assessment_col]
                            ).strip()

                            obtained = safe_float(
                                row[obtained_col]
                            )

                            if total_col:

                                total = safe_float(
                                    row[total_col],
                                    100
                                )

                            else:

                                total = 100

                            if (
                                not roll
                                or roll.lower() == "nan"
                                or not course
                                or not assessment
                            ):

                                skipped += 1
                                continue

                            student_exists = execute("""
                                SELECT id
                                FROM students
                                WHERE roll_no = ?
                            """, (roll,), fetch=True)

                            if not student_exists:

                                skipped += 1

                                errors.append(
                                    f"Row {index + 2}: "
                                    f"Student {roll} does not exist."
                                )

                                continue

                            course_exists = execute("""
                                SELECT id
                                FROM courses
                                WHERE course_code = ?
                            """, (course,), fetch=True)

                            if not course_exists:

                                # Automatically create the course
                                # if it isn't already registered.
                                execute("""
                                    INSERT OR IGNORE INTO courses
                                    (course_code, course_name,
                                     credit_hours, semester,
                                     created_at)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    course,
                                    course,
                                    0,
                                    "",
                                    datetime.now().isoformat()
                                ))

                            if total <= 0:

                                skipped += 1

                                errors.append(
                                    f"Row {index + 2}: "
                                    f"Total marks must be greater than zero."
                                )

                                continue

                            percentage = (
                                obtained / total
                            ) * 100

                            grade = get_grade(
                                percentage
                            )

                            existing = execute("""
                                SELECT id
                                FROM results
                                WHERE roll_no = ?
                                AND course_code = ?
                                AND assessment = ?
                            """, (
                                roll,
                                course,
                                assessment
                            ), fetch=True)

                            if existing:

                                execute("""
                                    UPDATE results
                                    SET obtained_marks = ?,
                                        total_marks = ?,
                                        percentage = ?,
                                        grade = ?,
                                        entered_at = ?
                                    WHERE roll_no = ?
                                    AND course_code = ?
                                    AND assessment = ?
                                """, (
                                    obtained,
                                    total,
                                    percentage,
                                    grade,
                                    datetime.now().isoformat(),
                                    roll,
                                    course,
                                    assessment
                                ))

                                updated += 1

                            else:

                                success = execute("""
                                    INSERT INTO results
                                    (
                                        roll_no,
                                        course_code,
                                        assessment,
                                        obtained_marks,
                                        total_marks,
                                        percentage,
                                        grade,
                                        entered_at
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    roll,
                                    course,
                                    assessment,
                                    obtained,
                                    total,
                                    percentage,
                                    grade,
                                    datetime.now().isoformat()
                                ))

                                if success:
                                    inserted += 1
                                else:
                                    skipped += 1

                        except Exception as row_error:

                            skipped += 1

                            errors.append(
                                f"Row {index + 2}: "
                                f"{row_error}"
                            )

                    st.success(
                        f"Marks upload complete: "
                        f"{inserted} new results, "
                        f"{updated} updated, "
                        f"{skipped} skipped."
                    )

                    if errors:

                        with st.expander(
                            f"⚠️ {len(errors)} rows need attention"
                        ):

                            for error in errors[:100]:
                                st.write(error)

                    st.rerun()

        except Exception as e:

            st.error(
                f"Could not read marks file: {e}"
            )


# ============================================================
# RESULTS
# ============================================================

elif page == "📈 Results":

    st.title("📈 Student Results")

    results_df = load_results()

    if results_df.empty:

        st.info(
            "No results available. Upload marks using "
            "'Bulk Marks Upload'."
        )

    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            student_filter = st.text_input(
                "Search Roll Number"
            )

        with col2:

            course_filter = st.text_input(
                "Search Course"
            )

        with col3:

            grade_filter = st.selectbox(
                "Grade",
                ["All"] + sorted(
                    results_df["Grade"]
                    .dropna()
                    .unique()
                    .tolist()
                )
            )

        filtered = results_df.copy()

        if student_filter:

            filtered = filtered[
                filtered["Roll Number"]
                .astype(str)
                .str.contains(
                    student_filter,
                    case=False,
                    na=False
                )
            ]

        if course_filter:

            filtered = filtered[
                filtered["Course Code"]
                .astype(str)
                .str.contains(
                    course_filter,
                    case=False,
                    na=False
                )
            ]

        if grade_filter != "All":

            filtered = filtered[
                filtered["Grade"] == grade_filter
            ]

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Filtered Results",
            filtered.to_csv(index=False).encode("utf-8"),
            "fast_tutor_results.csv",
            "text/csv"
        )


# ============================================================
# STUDENT TRANSCRIPT
# ============================================================

elif page == "📋 Student Transcript":

    st.title("📋 Student Transcript")

    students_df = load_students()

    if students_df.empty:

        st.info(
            "Import students first."
        )

    else:

        roll_numbers = students_df[
            "Roll Number"
        ].tolist()

        selected_roll = st.selectbox(
            "Select Student",
            roll_numbers
        )

        student_info = students_df[
            students_df["Roll Number"] == selected_roll
        ]

        if not student_info.empty:

            student = student_info.iloc[0]

            st.subheader(
                f"🎓 {student['Student Name']}"
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.write(
                    f"**Roll Number:** {student['Roll Number']}"
                )

            with c2:
                st.write(
                    f"**Program:** {student['Program']}"
                )

            with c3:
                st.write(
                    f"**Semester:** {student['Semester']}"
                )

            transcript = execute("""
                SELECT
                    course_code,
                    assessment,
                    obtained_marks,
                    total_marks,
                    percentage,
                    grade
                FROM results
                WHERE roll_no = ?
                ORDER BY course_code
            """, (selected_roll,), fetch=True)

            transcript_df = pd.DataFrame(
                transcript,
                columns=[
                    "Course Code",
                    "Assessment",
                    "Obtained Marks",
                    "Total Marks",
                    "Percentage",
                    "Grade"
                ]
            )

            if transcript_df.empty:

                st.info(
                    "No marks found for this student."
                )

            else:

                st.dataframe(
                    transcript_df,
                    use_container_width=True,
                    hide_index=True
                )

                average = transcript_df[
                    "Percentage"
                ].mean()

                st.metric(
                    "Overall Average",
                    f"{average:.2f}%"
                )


# ============================================================
# PERFORMANCE ANALYSIS
# ============================================================

elif page == "📊 Performance Analysis":

    st.title("📊 Performance Analysis")

    results_df = load_results()

    if results_df.empty:

        st.info(
            "Upload student marks first."
        )

    else:

        st.subheader("Course Performance")

        course_performance = (
            results_df
            .groupby(
                ["Course Code", "Course Name"]
            )["Percentage"]
            .agg(
                ["mean", "min", "max", "count"]
            )
            .reset_index()
        )

        course_performance.columns = [
            "Course Code",
            "Course Name",
            "Average %",
            "Lowest %",
            "Highest %",
            "Students"
        ]

        st.dataframe(
            course_performance,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("📈 Average Performance by Course")

        chart_data = (
            results_df
            .groupby("Course Code")["Percentage"]
            .mean()
        )

        st.bar_chart(chart_data)

        st.subheader("⚠️ Students Requiring Attention")

        weak_students = (
            results_df[
                results_df["Percentage"] < 50
            ]
            .groupby(
                ["Roll Number", "Student Name"]
            )
            .agg(
                Weak_Assessments=("Percentage", "count"),
                Average_Percentage=("Percentage", "mean")
            )
            .reset_index()
        )

        if weak_students.empty:

            st.success(
                "No results below 50%."
            )

        else:

            st.dataframe(
                weak_students,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# IMPORT / EXPORT
# ============================================================

elif page == "📤 Import / Export":

    st.title("📤 Import / Export")

    st.subheader("Export Complete Database")

    students_df = load_students()
    courses_df = load_courses()
    results_df = load_results()

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        students_df.to_excel(
            writer,
            index=False,
            sheet_name="Students"
        )

        courses_df.to_excel(
            writer,
            index=False,
            sheet_name="Courses"
        )

        results_df.to_excel(
            writer,
            index=False,
            sheet_name="Results"
        )

    st.download_button(
        "⬇️ Download Complete Excel Report",
        output.getvalue(),
        "fast_tutor_complete_database.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    st.subheader("CSV Exports")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            "Students CSV",
            students_df.to_csv(
                index=False
            ).encode("utf-8"),
            "students.csv",
            "text/csv"
        )

    with col2:

        st.download_button(
            "Courses CSV",
            courses_df.to_csv(
                index=False
            ).encode("utf-8"),
            "courses.csv",
            "text/csv"
        )

    with col3:

        st.download_button(
            "Results CSV",
            results_df.to_csv(
                index=False
            ).encode("utf-8"),
            "results.csv",
            "text/csv"
        )


# ============================================================
# SETTINGS
# ============================================================

elif page == "⚙️ Settings":

    st.title("⚙️ Fast Tutor Settings")

    institute_name = st.text_input(
        "Institute / University Name"
    )

    academic_year = st.text_input(
        "Academic Year",
        placeholder="2026-2027"
    )

    semester = st.text_input(
        "Current Semester",
        placeholder="Fall 2026"
    )

    if st.button(
        "💾 Save Settings",
        use_container_width=True
    ):

        existing = execute(
            "SELECT id FROM settings WHERE id = 1",
            fetch=True
        )

        if existing:

            execute("""
                UPDATE settings
                SET institute_name = ?,
                    semester = ?,
                    academic_year = ?
                WHERE id = 1
            """, (
                institute_name,
                semester,
                academic_year
            ))

        else:

            execute("""
                INSERT INTO settings
                (
                    id,
                    institute_name,
                    semester,
                    academic_year
                )
                VALUES (1, ?, ?, ?)
            """, (
                institute_name,
                semester,
                academic_year
            ))

        st.success(
            "Settings saved successfully."
        )

    st.divider()

    st.subheader("Database Information")

    student_count = execute(
        "SELECT COUNT(*) FROM students",
        fetch=True
    )[0][0]

    result_count = execute(
        "SELECT COUNT(*) FROM results",
        fetch=True
    )[0][0]

    course_count = execute(
        "SELECT COUNT(*) FROM courses",
        fetch=True
    )[0][0]

    st.write(
        f"👨‍🎓 Students: **{student_count}**"
    )

    st.write(
        f"📚 Courses: **{course_count}**"
    )

    st.write(
        f"📊 Results: **{result_count}**"
    )

    st.divider()

    st.info(
        "Fast Tutor is designed for bulk student and marks management. "
        "You can upload complete Excel/CSV files instead of entering "
        "students and marks individually."
    )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.markdown(
    "<div style='text-align:center; color:gray;'>"
    "© 2026 Fast Tutor"
    "</div>",
    unsafe_allow_html=True
)
