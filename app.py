import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from io import BytesIO

# ============================================================
# FAST TUTOR
# Simple Student Marks & Results Management System
# ============================================================

st.set_page_config(
    page_title="Fast Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "fast_tutor.db"
LOGO_FILE = "fast_tutor_logo.png"


# ============================================================
# DATABASE
# ============================================================

def get_db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


db = get_db()


def create_database():

    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            program TEXT DEFAULT '',
            semester TEXT DEFAULT '',
            section TEXT DEFAULT ''
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            course_code TEXT NOT NULL,
            assessment TEXT NOT NULL,
            obtained REAL DEFAULT 0,
            total REAL DEFAULT 100,
            percentage REAL DEFAULT 0,
            grade TEXT DEFAULT '',
            UNIQUE(roll_no, course_code, assessment)
        )
    """)

    db.commit()


create_database()


# ============================================================
# DATABASE HELPERS
# ============================================================

def run_query(query, parameters=(), fetch=False):

    try:

        cursor = db.cursor()
        cursor.execute(query, parameters)
        db.commit()

        if fetch:
            return cursor.fetchall()

        return True

    except sqlite3.IntegrityError:
        db.rollback()
        return False

    except sqlite3.Error as e:
        db.rollback()
        st.error(f"Database error: {e}")
        return False


# ============================================================
# GRADING
# ============================================================

def calculate_grade(percentage):

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


# ============================================================
# DATA LOADERS
# ============================================================

def get_students():

    rows = run_query("""
        SELECT
            roll_no,
            student_name,
            program,
            semester,
            section
        FROM students
        ORDER BY roll_no
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "Roll Number",
            "Student Name",
            "Program",
            "Semester",
            "Section"
        ]
    )


def get_courses():

    rows = run_query("""
        SELECT
            course_code,
            course_name
        FROM courses
        ORDER BY course_code
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "Course Code",
            "Course Name"
        ]
    )


def get_results():

    rows = run_query("""
        SELECT
            r.roll_no,
            s.student_name,
            r.course_code,
            r.assessment,
            r.obtained,
            r.total,
            r.percentage,
            r.grade
        FROM results r
        LEFT JOIN students s
            ON r.roll_no = s.roll_no
        ORDER BY r.roll_no, r.course_code
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "Roll Number",
            "Student Name",
            "Course Code",
            "Assessment",
            "Obtained Marks",
            "Total Marks",
            "Percentage",
            "Grade"
        ]
    )


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_column(df, names):

    normalized = {}

    for column in df.columns:

        clean = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        normalized[clean] = column

    for name in names:

        clean = (
            name
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if clean in normalized:
            return normalized[clean]

    return None


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.fast-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 0;
}

.fast-subtitle {
    font-size: 17px;
    color: #6b7280;
    margin-top: -5px;
    margin-bottom: 25px;
}

.hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(135deg, #eaf7ff, #f7fbff);
    border: 1px solid #d7eefe;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 34px;
    margin-bottom: 5px;
}

.hero p {
    color: #5f6b7a;
    font-size: 17px;
}

.quick-card {
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e5e7eb;
    background: white;
    min-height: 145px;
    box-shadow: 0 3px 12px rgba(0,0,0,0.04);
}

.quick-card h3 {
    margin-top: 0;
}

.logo-text {
    font-size: 28px;
    font-weight: 800;
    color: #0795d1;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    if os.path.exists(LOGO_FILE):

        st.image(
            LOGO_FILE,
            use_container_width=True
        )

    else:

        st.markdown(
            "<div class='logo-text'>🎓 FAST TUTOR</div>",
            unsafe_allow_html=True
        )

    st.caption("Student Marks & Results")

    st.divider()

    page = st.radio(
        "MENU",
        [
            "🏠 Dashboard",
            "👨‍🎓 Students",
            "📥 Upload Students",
            "📊 Upload Marks",
            "📈 Results",
            "🧾 Student Report",
            "📚 Courses",
            "📤 Export"
        ]
    )

    st.divider()

    st.caption("Fast Tutor")
    st.caption("Simple • Fast • Smart")


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        "<div class='fast-title'>Fast Tutor</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='fast-subtitle'>"
        "Student Marks & Results Management"
        "</div>",
        unsafe_allow_html=True
    )

    student_count = run_query(
        "SELECT COUNT(*) FROM students",
        fetch=True
    )[0][0]

    course_count = run_query(
        "SELECT COUNT(*) FROM courses",
        fetch=True
    )[0][0]

    result_count = run_query(
        "SELECT COUNT(*) FROM results",
        fetch=True
    )[0][0]

    passed_count = run_query(
        "SELECT COUNT(*) FROM results WHERE grade != 'F'",
        fetch=True
    )[0][0]

    # --------------------------------------------------------
    # STAT CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "👨‍🎓 Students",
            student_count
        )

    with c2:
        st.metric(
            "📚 Courses",
            course_count
        )

    with c3:
        st.metric(
            "📊 Results",
            result_count
        )

    with c4:
        st.metric(
            "✅ Passed",
            passed_count
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # HERO
    # --------------------------------------------------------

    st.markdown("""
    <div class="hero">
        <h1>Welcome to Fast Tutor 👋</h1>
        <p>
        Manage students, upload complete marks files,
        calculate results automatically and generate
        student reports — all in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------

    st.subheader("⚡ Quick Actions")

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        st.markdown("""
        <div class="quick-card">
        <h3>👨‍🎓 Students</h3>
        <p>View and manage all students.</p>
        </div>
        """, unsafe_allow_html=True)

    with q2:

        st.markdown("""
        <div class="quick-card">
        <h3>📥 Upload Students</h3>
        <p>Import hundreds of students using Excel.</p>
        </div>
        """, unsafe_allow_html=True)

    with q3:

        st.markdown("""
        <div class="quick-card">
        <h3>📊 Upload Marks</h3>
        <p>Upload complete marks in one file.</p>
        </div>
        """, unsafe_allow_html=True)

    with q4:

        st.markdown("""
        <div class="quick-card">
        <h3>🧾 Reports</h3>
        <p>View individual student performance.</p>
        </div>
        """, unsafe_allow_html=True)

    # --------------------------------------------------------
    # PERFORMANCE CHART
    # --------------------------------------------------------

    results = get_results()

    if not results.empty:

        st.markdown("<br>", unsafe_allow_html=True)

        left, right = st.columns(2)

        with left:

            st.subheader("📈 Course Performance")

            course_average = (
                results
                .groupby("Course Code")["Percentage"]
                .mean()
                .round(2)
            )

            st.bar_chart(course_average)

        with right:

            st.subheader("🎯 Grade Distribution")

            grade_counts = (
                results["Grade"]
                .value_counts()
            )

            st.bar_chart(grade_counts)


# ============================================================
# STUDENTS
# ============================================================

elif page == "👨‍🎓 Students":

    st.title("👨‍🎓 Students")

    students = get_students()

    if students.empty:

        st.info(
            "No students yet. Use 'Upload Students' "
            "to import your student list."
        )

    else:

        search = st.text_input(
            "🔎 Search by roll number or student name"
        )

        display = students.copy()

        if search:

            display = display[
                display["Roll Number"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                display["Student Name"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        st.write(
            f"Showing **{len(display)}** students"
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# BULK STUDENT UPLOAD
# ============================================================

elif page == "📥 Upload Students":

    st.title("📥 Upload Students")

    st.write(
        "Upload your complete student list using Excel or CSV."
    )

    st.info(
        "You can upload hundreds or thousands of students at once."
    )

    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    template = pd.DataFrame({
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
            "3",
            "3",
            "3"
        ],
        "Section": [
            "A",
            "A",
            "A"
        ]
    })

    st.subheader("📄 File Format")

    st.dataframe(
        template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Student Template",
        template.to_csv(index=False).encode(),
        "Fast_Tutor_Student_Template.csv",
        "text/csv"
    )

    st.divider()

    uploaded = st.file_uploader(
        "Choose Student Excel/CSV File",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded:

        try:

            if uploaded.name.lower().endswith(".csv"):

                df = pd.read_csv(uploaded)

            else:

                df = pd.read_excel(uploaded)

            st.success(
                f"File loaded successfully — {len(df)} rows found."
            )

            st.subheader("Preview")

            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True
            )

            roll_col = find_column(
                df,
                [
                    "roll_number",
                    "roll_no",
                    "roll",
                    "registration_number",
                    "registration_no",
                    "student_id"
                ]
            )

            name_col = find_column(
                df,
                [
                    "student_name",
                    "student",
                    "name"
                ]
            )

            program_col = find_column(
                df,
                [
                    "program",
                    "programme",
                    "degree"
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
                    "Roll Number column was not found."
                )

            elif not name_col:

                st.error(
                    "Student Name column was not found."
                )

            else:

                st.success(
                    f"Detected: {roll_col} + {name_col}"
                )

                if st.button(
                    "🚀 IMPORT ALL STUDENTS",
                    type="primary",
                    use_container_width=True
                ):

                    new_students = 0
                    updated_students = 0
                    skipped = 0

                    for _, row in df.iterrows():

                        roll = str(
                            row[roll_col]
                        ).strip()

                        name = str(
                            row[name_col]
                        ).strip()

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

                        existing = run_query(
                            """
                            SELECT id
                            FROM students
                            WHERE roll_no = ?
                            """,
                            (roll,),
                            fetch=True
                        )

                        if existing:

                            run_query(
                                """
                                UPDATE students
                                SET student_name = ?,
                                    program = ?,
                                    semester = ?,
                                    section = ?
                                WHERE roll_no = ?
                                """,
                                (
                                    name,
                                    program,
                                    semester,
                                    section,
                                    roll
                                )
                            )

                            updated_students += 1

                        else:

                            success = run_query(
                                """
                                INSERT INTO students
                                (
                                    roll_no,
                                    student_name,
                                    program,
                                    semester,
                                    section
                                )
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    roll,
                                    name,
                                    program,
                                    semester,
                                    section
                                )
                            )

                            if success:
                                new_students += 1
                            else:
                                skipped += 1

                    st.success(
                        f"Import complete! "
                        f"{new_students} new students, "
                        f"{updated_students} updated, "
                        f"{skipped} skipped."
                    )

                    st.rerun()

        except Exception as error:

            st.error(
                f"Could not read the file: {error}"
            )


# ============================================================
# BULK MARKS UPLOAD
# ============================================================

elif page == "📊 Upload Marks":

    st.title("📊 Upload Marks")

    st.write(
        "Upload the complete marks sheet. "
        "There is no need to enter marks student-by-student."
    )

    st.success(
        "Fast Tutor automatically calculates percentage and grade."
    )

    # --------------------------------------------------------
    # TEMPLATE
    # --------------------------------------------------------

    marks_template = pd.DataFrame({
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

    st.subheader("📄 Marks File Format")

    st.dataframe(
        marks_template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Marks Template",
        marks_template.to_csv(index=False).encode(),
        "Fast_Tutor_Marks_Template.csv",
        "text/csv"
    )

    st.divider()

    uploaded_marks = st.file_uploader(
        "Choose Complete Marks Excel/CSV File",
        type=["xlsx", "xls", "csv"],
        key="marks_file"
    )

    if uploaded_marks:

        try:

            if uploaded_marks.name.lower().endswith(".csv"):

                marks = pd.read_csv(
                    uploaded_marks
                )

            else:

                marks = pd.read_excel(
                    uploaded_marks
                )

            st.success(
                f"File loaded successfully — {len(marks)} rows found."
            )

            st.subheader("Preview")

            st.dataframe(
                marks.head(30),
                use_container_width=True,
                hide_index=True
            )

            roll_col = find_column(
                marks,
                [
                    "roll_number",
                    "roll_no",
                    "roll",
                    "registration_number",
                    "registration_no",
                    "student_id"
                ]
            )

            course_col = find_column(
                marks,
                [
                    "course_code",
                    "course",
                    "subject_code",
                    "subject"
                ]
            )

            assessment_col = find_column(
                marks,
                [
                    "assessment",
                    "exam",
                    "exam_type",
                    "test",
                    "paper"
                ]
            )

            obtained_col = find_column(
                marks,
                [
                    "obtained_marks",
                    "marks_obtained",
                    "marks",
                    "score",
                    "obtained"
                ]
            )

            total_col = find_column(
                marks,
                [
                    "total_marks",
                    "maximum_marks",
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
                    "Missing columns: "
                    + ", ".join(missing)
                )

            else:

                if st.button(
                    "🚀 UPLOAD ALL MARKS",
                    type="primary",
                    use_container_width=True
                ):

                    added = 0
                    updated = 0
                    skipped = 0
                    errors = []

                    progress = st.progress(0)

                    total_rows = len(marks)

                    for number, (_, row) in enumerate(
                        marks.iterrows()
                    ):

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

                            obtained = float(
                                row[obtained_col]
                            )

                            if total_col:

                                total = float(
                                    row[total_col]
                                )

                            else:

                                total = 100.0

                            if total <= 0:

                                skipped += 1

                                errors.append(
                                    f"Row {number + 2}: "
                                    "Total marks must be greater than 0."
                                )

                                continue

                            # Check student
                            student = run_query(
                                """
                                SELECT id
                                FROM students
                                WHERE roll_no = ?
                                """,
                                (roll,),
                                fetch=True
                            )

                            if not student:

                                skipped += 1

                                errors.append(
                                    f"Row {number + 2}: "
                                    f"Student {roll} not found."
                                )

                                continue

                            percentage = (
                                obtained / total
                            ) * 100

                            grade = calculate_grade(
                                percentage
                            )

                            # Create course automatically
                            run_query(
                                """
                                INSERT OR IGNORE INTO courses
                                (
                                    course_code,
                                    course_name
                                )
                                VALUES (?, ?)
                                """,
                                (
                                    course,
                                    course
                                )
                            )

                            existing = run_query(
                                """
                                SELECT id
                                FROM results
                                WHERE roll_no = ?
                                AND course_code = ?
                                AND assessment = ?
                                """,
                                (
                                    roll,
                                    course,
                                    assessment
                                ),
                                fetch=True
                            )

                            if existing:

                                run_query(
                                    """
                                    UPDATE results
                                    SET obtained = ?,
                                        total = ?,
                                        percentage = ?,
                                        grade = ?
                                    WHERE roll_no = ?
                                    AND course_code = ?
                                    AND assessment = ?
                                    """,
                                    (
                                        obtained,
                                        total,
                                        percentage,
                                        grade,
                                        roll,
                                        course,
                                        assessment
                                    )
                                )

                                updated += 1

                            else:

                                success = run_query(
                                    """
                                    INSERT INTO results
                                    (
                                        roll_no,
                                        course_code,
                                        assessment,
                                        obtained,
                                        total,
                                        percentage,
                                        grade
                                    )
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (
                                        roll,
                                        course,
                                        assessment,
                                        obtained,
                                        total,
                                        percentage,
                                        grade
                                    )
                                )

                                if success:
                                    added += 1
                                else:
                                    skipped += 1

                        except Exception as row_error:

                            skipped += 1

                            errors.append(
                                f"Row {number + 2}: "
                                f"{row_error}"
                            )

                        progress.progress(
                            (number + 1) / total_rows
                        )

                    st.success(
                        f"Marks uploaded successfully! "
                        f"{added} new results, "
                        f"{updated} updated, "
                        f"{skipped} skipped."
                    )

                    if errors:

                        with st.expander(
                            "⚠️ Rows that need attention"
                        ):

                            for error in errors[:100]:
                                st.write(error)

                    st.rerun()

        except Exception as error:

            st.error(
                f"Could not read the marks file: {error}"
            )


# ============================================================
# RESULTS
# ============================================================

elif page == "📈 Results":

    st.title("📈 Results")

    results = get_results()

    if results.empty:

        st.info(
            "No results available yet. "
            "Upload marks first."
        )

    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            search = st.text_input(
                "🔎 Search Student"
            )

        with col2:

            course_filter = st.text_input(
                "📚 Course"
            )

        with col3:

            grade_filter = st.selectbox(
                "🎯 Grade",
                ["All"] + sorted(
                    results["Grade"].unique()
                )
            )

        filtered = results.copy()

        if search:

            filtered = filtered[
                filtered["Roll Number"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                filtered["Student Name"]
                .astype(str)
                .str.contains(
                    search,
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
            "⬇️ Download Results",
            filtered.to_csv(
                index=False
            ).encode(),
            "Fast_Tutor_Results.csv",
            "text/csv"
        )


# ============================================================
# STUDENT REPORT
# ============================================================

elif page == "🧾 Student Report":

    st.title("🧾 Student Report")

    students = get_students()

    if students.empty:

        st.info(
            "No students available."
        )

    else:

        selected = st.selectbox(
            "Select Student",
            students["Roll Number"].tolist(),
            format_func=lambda x:
                f"{x} — "
                f"{students.loc[students['Roll Number'] == x, 'Student Name'].iloc[0]}"
        )

        student = students[
            students["Roll Number"] == selected
        ].iloc[0]

        st.markdown(
            f"""
            ### 🎓 {student['Student Name']}

            **Roll Number:** {student['Roll Number']}  
            **Program:** {student['Program']}  
            **Semester:** {student['Semester']}  
            **Section:** {student['Section']}
            """
        )

        student_results = results = get_results()

        student_results = student_results[
            student_results["Roll Number"] == selected
        ]

        if student_results.empty:

            st.warning(
                "No marks have been uploaded for this student."
            )

        else:

            average = student_results[
                "Percentage"
            ].mean()

            passed = len(
                student_results[
                    student_results["Grade"] != "F"
                ]
            )

            failed = len(
                student_results[
                    student_results["Grade"] == "F"
                ]
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                st.metric(
                    "Average",
                    f"{average:.2f}%"
                )

            with c2:
                st.metric(
                    "Passed",
                    passed
                )

            with c3:
                st.metric(
                    "Failed",
                    failed
                )

            st.divider()

            st.subheader("📊 Marks")

            st.dataframe(
                student_results,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📈 Performance")

            chart = (
                student_results
                .set_index("Course Code")[
                    "Percentage"
                ]
            )

            st.bar_chart(chart)


# ============================================================
# COURSES
# ============================================================

elif page == "📚 Courses":

    st.title("📚 Courses")

    courses = get_courses()

    st.subheader("Add Course")

    with st.form("course_form"):

        col1, col2 = st.columns(2)

        with col1:

            course_code = st.text_input(
                "Course Code",
                placeholder="CS101"
            )

        with col2:

            course_name = st.text_input(
                "Course Name",
                placeholder="Programming Fundamentals"
            )

        submitted = st.form_submit_button(
            "➕ Add Course",
            use_container_width=True
        )

    if submitted:

        if not course_code or not course_name:

            st.error(
                "Please enter both course code and course name."
            )

        else:

            success = run_query(
                """
                INSERT INTO courses
                (course_code, course_name)
                VALUES (?, ?)
                """,
                (
                    course_code.strip().upper(),
                    course_name.strip()
                )
            )

            if success:

                st.success(
                    "Course added successfully."
                )

                st.rerun()

            else:

                st.warning(
                    "This course already exists."
                )

    st.divider()

    st.subheader("Course List")

    if courses.empty:

        st.info(
            "No courses available."
        )

    else:

        st.dataframe(
            courses,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# EXPORT
# ============================================================

elif page == "📤 Export":

    st.title("📤 Export Data")

    students = get_students()
    courses = get_courses()
    results = get_results()

    st.subheader("Download Excel Report")

    excel_file = BytesIO()

    with pd.ExcelWriter(
        excel_file,
        engine="openpyxl"
    ) as writer:

        students.to_excel(
            writer,
            index=False,
            sheet_name="Students"
        )

        courses.to_excel(
            writer,
            index=False,
            sheet_name="Courses"
        )

        results.to_excel(
            writer,
            index=False,
            sheet_name="Results"
        )

    st.download_button(
        "⬇️ Download Complete Excel Report",
        excel_file.getvalue(),
        "Fast_Tutor_Complete_Report.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    st.subheader("CSV Downloads")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.download_button(
            "👨‍🎓 Students CSV",
            students.to_csv(
                index=False
            ).encode(),
            "Fast_Tutor_Students.csv",
            "text/csv",
            use_container_width=True
        )

    with c2:

        st.download_button(
            "📚 Courses CSV",
            courses.to_csv(
                index=False
            ).encode(),
            "Fast_Tutor_Courses.csv",
            "text/csv",
            use_container_width=True
        )

    with c3:

        st.download_button(
            "📊 Results CSV",
            results.to_csv(
                index=False
            ).encode(),
            "Fast_Tutor_Results.csv",
            "text/csv",
            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    "<div style='text-align:center;color:#888;'>"
    "🎓 <b>Fast Tutor</b> — Student Marks & Results Management"
    "</div>",
    unsafe_allow_html=True
)
