import streamlit as st
import pandas as pd
import sqlite3
import os
from io import BytesIO


# ============================================================
# FAST TUTOR
# Student Performance & Attainment System
# ============================================================

st.set_page_config(
    page_title="Fast Tutor",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "fast_tutor.db"

conn = sqlite3.connect(
    DB_FILE,
    check_same_thread=False
)


# ============================================================
# DATABASE EXECUTOR
# ============================================================

def execute(query, params=(), fetch=False):
    """
    Safely execute SQLite queries.

    For SELECT queries, always return a list.
    This prevents pandas from receiving False/None.
    """

    try:
        cursor = conn.cursor()

        cursor.execute(
            query,
            params
        )

        if fetch:

            rows = cursor.fetchall()

            if rows is None:
                return []

            return rows

        conn.commit()

        return True

    except sqlite3.Error as error:

        conn.rollback()

        if fetch:

            st.error(
                "Database query error: "
                + str(error)
            )

            return []

        st.error(
            "Database error: "
            + str(error)
        )

        return False


# ============================================================
# CREATE DATABASE
# ============================================================

def create_tables():

    execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            credit_hours REAL DEFAULT 3,
            semester TEXT DEFAULT ''
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            program TEXT DEFAULT '',
            semester TEXT DEFAULT '',
            section TEXT DEFAULT ''
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS clos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            clo_code TEXT NOT NULL,
            description TEXT NOT NULL,
            bloom_level TEXT DEFAULT '',
            UNIQUE(course_code, clo_code)
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS plos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plo_code TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            assessment_name TEXT NOT NULL,
            assessment_type TEXT NOT NULL,
            assessment_date TEXT DEFAULT '',
            total_marks REAL DEFAULT 100,
            weightage REAL DEFAULT 0,
            description TEXT DEFAULT '',
            UNIQUE(course_code, assessment_name)
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS assessment_clos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            clo_code TEXT NOT NULL,
            UNIQUE(assessment_id, clo_code)
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            clo_code TEXT NOT NULL,
            plo_code TEXT NOT NULL,
            strength INTEGER DEFAULT 0,
            UNIQUE(course_code, clo_code, plo_code)
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            course_code TEXT NOT NULL,
            assessment TEXT NOT NULL,
            clo_code TEXT DEFAULT '',
            obtained REAL DEFAULT 0,
            total REAL DEFAULT 100,
            percentage REAL DEFAULT 0,
            grade TEXT DEFAULT '',
            UNIQUE(
                roll_no,
                course_code,
                assessment,
                clo_code
            )
        )
    """)


create_tables()


# ============================================================
# DATABASE REPAIR
# ============================================================

def repair_results_table():

    try:

        columns = execute(
            "PRAGMA table_info(results)",
            fetch=True
        )

        existing_columns = {
            row[1]
            for row in columns
        }

        required_columns = {

            "roll_no":
                "TEXT DEFAULT ''",

            "course_code":
                "TEXT DEFAULT ''",

            "assessment":
                "TEXT DEFAULT ''",

            "clo_code":
                "TEXT DEFAULT ''",

            "obtained":
                "REAL DEFAULT 0",

            "total":
                "REAL DEFAULT 100",

            "percentage":
                "REAL DEFAULT 0",

            "grade":
                "TEXT DEFAULT ''"
        }

        for column, definition in required_columns.items():

            if column not in existing_columns:

                execute(
                    f"""
                    ALTER TABLE results
                    ADD COLUMN {column} {definition}
                    """
                )

    except Exception as error:

        st.warning(
            "Database repair warning: "
            + str(error)
        )


repair_results_table()


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
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

    .fast-logo {
        text-align: center;
        padding: 10px 5px 18px 5px;
    }

    .fast-logo-title {
        font-size: 32px;
        font-weight: 900;
        color: #0795D1;
        letter-spacing: 2px;
        line-height: 1.1;
    }

    .fast-logo-subtitle {
        font-size: 12px;
        font-weight: 600;
        color: #6B7280;
        margin-top: 6px;
    }

    .fast-title {
        font-size: 42px;
        font-weight: 900;
        color: #0795D1;
        letter-spacing: 1px;
    }

    .fast-subtitle {
        color: #667085;
        font-size: 18px;
        margin-bottom: 20px;
    }

    .hero {
        padding: 30px;
        border-radius: 22px;
        background: linear-gradient(
            135deg,
            #E8F7FF,
            #F8FCFF
        );
        border: 1px solid #D8EFFB;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 30px;
        font-weight: 800;
    }

    .hero-text {
        color: #667085;
        margin-top: 8px;
        font-size: 16px;
        line-height: 1.6;
    }

    .section-title {
        font-size: 24px;
        font-weight: 800;
        margin-top: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FAST TUTOR LOGO
# ============================================================

def show_logo():

    st.markdown(
        """
        <div class="fast-logo">

            <div class="fast-logo-title">
                ⚡ FAST TUTOR
            </div>

            <div class="fast-logo-subtitle">
                Student Performance System
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATA FUNCTIONS
# ============================================================

def get_courses():

    rows = execute(
        """
        SELECT
            course_code,
            course_name,
            credit_hours,
            semester

        FROM courses

        ORDER BY course_code
        """,
        fetch=True
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "Course Code",
                "Course Name",
                "Credit Hours",
                "Semester"
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Course Code",
            "Course Name",
            "Credit Hours",
            "Semester"
        ]
    )


def get_students():

    rows = execute(
        """
        SELECT
            roll_no,
            student_name,
            program,
            semester,
            section

        FROM students

        ORDER BY roll_no
        """,
        fetch=True
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "Roll Number",
                "Student Name",
                "Program",
                "Semester",
                "Section"
            ]
        )

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


def get_clos():

    rows = execute(
        """
        SELECT
            course_code,
            clo_code,
            description,
            bloom_level

        FROM clos

        ORDER BY course_code, clo_code
        """,
        fetch=True
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "Course Code",
                "CLO",
                "Description",
                "Bloom Level"
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Course Code",
            "CLO",
            "Description",
            "Bloom Level"
        ]
    )


def get_plos():

    rows = execute(
        """
        SELECT
            plo_code,
            description

        FROM plos

        ORDER BY plo_code
        """,
        fetch=True
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "PLO",
                "Description"
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "PLO",
            "Description"
        ]
    )


def get_mappings():

    rows = execute(
        """
        SELECT
            course_code,
            clo_code,
            plo_code,
            strength

        FROM mappings

        ORDER BY
            course_code,
            clo_code,
            plo_code
        """,
        fetch=True
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "Course Code",
                "CLO",
                "PLO",
                "Strength"
            ]
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Course Code",
            "CLO",
            "PLO",
            "Strength"
        ]
    )


def get_results():

    columns = [
        "Roll Number",
        "Student Name",
        "Course Code",
        "Assessment",
        "CLO",
        "Obtained",
        "Total",
        "Percentage",
        "Grade"
    ]

    rows = execute(
        """
        SELECT
            r.roll_no,
            COALESCE(
                s.student_name,
                ''
            ),
            r.course_code,
            r.assessment,
            r.clo_code,
            r.obtained,
            r.total,
            r.percentage,
            r.grade

        FROM results r

        LEFT JOIN students s
            ON r.roll_no = s.roll_no

        ORDER BY
            r.roll_no,
            r.course_code,
            r.assessment
        """,
        fetch=True
    )

    if not rows:
        return pd.DataFrame(
            columns=columns
        )

    return pd.DataFrame(
        rows,
        columns=columns
    )


# ============================================================
# COLUMN DETECTION
# ============================================================

def find_column(dataframe, possible_names):

    for column in dataframe.columns:

        normalized = (
            str(column)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if normalized in possible_names:

            return column

    return None


# ============================================================
# GRADE
# ============================================================

def calculate_grade(percentage):

    if percentage >= 90:
        return "A+"

    if percentage >= 85:
        return "A"

    if percentage >= 80:
        return "A-"

    if percentage >= 75:
        return "B+"

    if percentage >= 70:
        return "B"

    if percentage >= 65:
        return "B-"

    if percentage >= 60:
        return "C+"

    if percentage >= 55:
        return "C"

    if percentage >= 50:
        return "C-"

    if percentage >= 45:
        return "D"

    return "F"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    show_logo()

    st.divider()

    page = st.radio(
        "FAST TUTOR",
        [
            "🏠 Dashboard",
            "📚 Courses",
            "👨‍🎓 Student Enrollment",
            "🎯 CLO Management",
            "🏆 PLO Management",
            "📝 Assessment Creation",
            "🔗 CLO–PLO Mapping",
            "📥 Bulk Marks Upload",
            "📊 Student Performance",
            "📈 Attainment Dashboard",
            "📤 Reports & Export"
        ]
    )

    st.divider()

    st.caption(
        "⚡ Fast Tutor"
    )

    st.caption(
        "Simple • Smart • Visual"
    )


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        """
        <div class="fast-title">
            ⚡ FAST TUTOR
        </div>

        <div class="fast-subtitle">
            Student Performance & Attainment System
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero">

            <div class="hero-title">
                👋 Welcome to
                <span style="color:#0795D1;">
                    Fast Tutor
                </span>
            </div>

            <div class="hero-text">
                A simple and intelligent platform for
                managing courses, students, assessments,
                marks and academic performance.
            </div>

            <div style="
                margin-top:18px;
                display:flex;
                gap:10px;
                flex-wrap:wrap;
            ">

                <span style="
                    background:#E8F7FF;
                    color:#0795D1;
                    padding:7px 14px;
                    border-radius:20px;
                    font-size:13px;
                    font-weight:600;
                ">
                    📚 Courses
                </span>

                <span style="
                    background:#E8F7FF;
                    color:#0795D1;
                    padding:7px 14px;
                    border-radius:20px;
                    font-size:13px;
                    font-weight:600;
                ">
                    👨‍🎓 Students
                </span>

                <span style="
                    background:#E8F7FF;
                    color:#0795D1;
                    padding:7px 14px;
                    border-radius:20px;
                    font-size:13px;
                    font-weight:600;
                ">
                    📝 Assessments
                </span>

                <span style="
                    background:#E8F7FF;
                    color:#0795D1;
                    padding:7px 14px;
                    border-radius:20px;
                    font-size:13px;
                    font-weight:600;
                ">
                    📊 Performance
                </span>

                <span style="
                    background:#E8F7FF;
                    color:#0795D1;
                    padding:7px 14px;
                    border-radius:20px;
                    font-size:13px;
                    font-weight:600;
                ">
                    🎯 Attainment
                </span>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    course_count = execute(
        "SELECT COUNT(*) FROM courses",
        fetch=True
    )[0][0]

    student_count = execute(
        "SELECT COUNT(*) FROM students",
        fetch=True
    )[0][0]

    clo_count = execute(
        "SELECT COUNT(*) FROM clos",
        fetch=True
    )[0][0]

    plo_count = execute(
        "SELECT COUNT(*) FROM plos",
        fetch=True
    )[0][0]

    assessment_count = execute(
        "SELECT COUNT(*) FROM assessments",
        fetch=True
    )[0][0]

    result_count = execute(
        "SELECT COUNT(*) FROM results",
        fetch=True
    )[0][0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "📚 Courses",
        course_count
    )

    c2.metric(
        "👨‍🎓 Students",
        student_count
    )

    c3.metric(
        "📝 Assessments",
        assessment_count
    )

    c4, c5, c6 = st.columns(3)

    c4.metric(
        "🎯 CLOs",
        clo_count
    )

    c5.metric(
        "🏆 PLOs",
        plo_count
    )

    c6.metric(
        "📊 Marks Records",
        result_count
    )

    st.divider()

    results = get_results()

    if not results.empty:

        st.subheader(
            "📈 Course Performance"
        )

        course_performance = (
            results
            .groupby("Course Code")[
                "Percentage"
            ]
            .mean()
            .round(2)
        )

        st.bar_chart(
            course_performance
        )

        st.subheader(
            "📊 Grade Distribution"
        )

        grade_distribution = (
            results["Grade"]
            .value_counts()
            .sort_index()
        )

        st.bar_chart(
            grade_distribution
        )

    else:

        st.info(
            "No marks have been uploaded yet. "
            "Go to Bulk Marks Upload to begin."
        )


# ============================================================
# COURSES
# ============================================================

elif page == "📚 Courses":

    st.title("📚 Courses")

    st.write(
        "Create courses before enrolling students."
    )

    with st.form("course_form"):

        c1, c2 = st.columns(2)

        with c1:

            course_code = st.text_input(
                "Course Code",
                placeholder="CS101"
            )

            credit_hours = st.number_input(
                "Credit Hours",
                min_value=0.5,
                max_value=10.0,
                value=3.0,
                step=0.5
            )

        with c2:

            course_name = st.text_input(
                "Course Name",
                placeholder="Programming Fundamentals"
            )

            semester = st.text_input(
                "Semester",
                placeholder="1"
            )

        save_course = st.form_submit_button(
            "➕ ADD COURSE",
            type="primary",
            use_container_width=True
        )

    if save_course:

        if (
            not course_code.strip()
            or not course_name.strip()
        ):

            st.error(
                "Course Code and Course Name are required."
            )

        else:

            success = execute(
                """
                INSERT INTO courses
                (
                    course_code,
                    course_name,
                    credit_hours,
                    semester
                )

                VALUES (?, ?, ?, ?)

                ON CONFLICT(course_code)
                DO UPDATE SET

                    course_name =
                        excluded.course_name,

                    credit_hours =
                        excluded.credit_hours,

                    semester =
                        excluded.semester
                """,
                (
                    course_code.strip().upper(),
                    course_name.strip(),
                    credit_hours,
                    semester.strip()
                )
            )

            if success:

                st.success(
                    "Course saved successfully."
                )

                st.rerun()

    st.divider()

    courses = get_courses()

    if courses.empty:

        st.info(
            "No courses have been created."
        )

    else:

        st.dataframe(
            courses,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# STUDENT ENROLLMENT
# ============================================================

elif page == "👨‍🎓 Student Enrollment":

    st.title("👨‍🎓 Student Enrollment")

    st.markdown(
        """
        Upload your complete student list once.
        Fast Tutor will enroll the entire class automatically.
        """
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Individual Student",
            "📥 Bulk Student Import"
        ]
    )

    # --------------------------------------------------------
    # INDIVIDUAL
    # --------------------------------------------------------

    with tab1:

        with st.form("student_form"):

            c1, c2 = st.columns(2)

            with c1:

                roll_no = st.text_input(
                    "Roll Number"
                )

                student_name = st.text_input(
                    "Student Name"
                )

                program = st.text_input(
                    "Program"
                )

            with c2:

                semester = st.text_input(
                    "Semester"
                )

                section = st.text_input(
                    "Section"
                )

            save_student = st.form_submit_button(
                "➕ SAVE STUDENT",
                type="primary",
                use_container_width=True
            )

        if save_student:

            if (
                not roll_no.strip()
                or not student_name.strip()
            ):

                st.error(
                    "Roll Number and Student Name are required."
                )

            else:

                success = execute(
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

                    ON CONFLICT(roll_no)
                    DO UPDATE SET

                        student_name =
                            excluded.student_name,

                        program =
                            excluded.program,

                        semester =
                            excluded.semester,

                        section =
                            excluded.section
                    """,
                    (
                        roll_no.strip(),
                        student_name.strip(),
                        program.strip(),
                        semester.strip(),
                        section.strip()
                    )
                )

                if success:

                    st.success(
                        "Student saved."
                    )

                    st.rerun()

    # --------------------------------------------------------
    # BULK IMPORT
    # --------------------------------------------------------

    with tab2:

        st.subheader(
            "📄 Recommended File Format"
        )

        student_template = pd.DataFrame(
            {
                "Roll Number": [
                    "CS001",
                    "CS002"
                ],

                "Student Name": [
                    "Ali Ahmed",
                    "Sara Khan"
                ],

                "Program": [
                    "BS Computer Science",
                    "BS Computer Science"
                ],

                "Semester": [
                    "3",
                    "3"
                ],

                "Section": [
                    "A",
                    "A"
                ]
            }
        )

        st.dataframe(
            student_template,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ DOWNLOAD STUDENT TEMPLATE",
            student_template.to_csv(
                index=False
            ).encode(),
            "Fast_Tutor_Student_Template.csv",
            "text/csv"
        )

        uploaded_students = st.file_uploader(
            "Upload CSV or Excel Student File",
            type=[
                "csv",
                "xlsx",
                "xls"
            ],
            key="student_file"
        )

        if uploaded_students:

            try:

                if uploaded_students.name.lower().endswith(
                    ".csv"
                ):

                    student_df = pd.read_csv(
                        uploaded_students
                    )

                else:

                    student_df = pd.read_excel(
                        uploaded_students
                    )

                st.success(
                    f"{len(student_df)} students detected."
                )

                st.dataframe(
                    student_df,
                    use_container_width=True,
                    hide_index=True
                )

                roll_column = find_column(
                    student_df,
                    [
                        "roll_number",
                        "roll_no",
                        "roll",
                        "registration_number",
                        "registration_no"
                    ]
                )

                name_column = find_column(
                    student_df,
                    [
                        "student_name",
                        "name",
                        "student"
                    ]
                )

                program_column = find_column(
                    student_df,
                    [
                        "program",
                        "programme",
                        "degree"
                    ]
                )

                semester_column = find_column(
                    student_df,
                    [
                        "semester",
                        "sem"
                    ]
                )

                section_column = find_column(
                    student_df,
                    [
                        "section",
                        "class",
                        "group"
                    ]
                )

                if (
                    not roll_column
                    or not name_column
                ):

                    st.error(
                        "The file must contain "
                        "Roll Number and Student Name."
                    )

                elif st.button(
                    "🚀 IMPORT ALL STUDENTS",
                    type="primary",
                    use_container_width=True
                ):

                    progress = st.progress(0)

                    imported = 0
                    skipped = 0

                    total_rows = max(
                        len(student_df),
                        1
                    )

                    for index, row in student_df.iterrows():

                        try:

                            roll_value = str(
                                row[roll_column]
                            ).strip()

                            name_value = str(
                                row[name_column]
                            ).strip()

                            if (
                                not roll_value
                                or roll_value.lower()
                                == "nan"
                                or not name_value
                                or name_value.lower()
                                == "nan"
                            ):

                                skipped += 1

                                continue

                            program_value = ""

                            if program_column:

                                program_value = str(
                                    row[program_column]
                                ).strip()

                            semester_value = ""

                            if semester_column:

                                semester_value = str(
                                    row[semester_column]
                                ).strip()

                            section_value = ""

                            if section_column:

                                section_value = str(
                                    row[section_column]
                                ).strip()

                            execute(
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

                                ON CONFLICT(roll_no)
                                DO UPDATE SET

                                    student_name =
                                        excluded.student_name,

                                    program =
                                        excluded.program,

                                    semester =
                                        excluded.semester,

                                    section =
                                        excluded.section
                                """,
                                (
                                    roll_value,
                                    name_value,
                                    program_value,
                                    semester_value,
                                    section_value
                                )
                            )

                            imported += 1

                        except Exception:

                            skipped += 1

                        progress.progress(
                            (index + 1) / total_rows
                        )

                    st.success(
                        f"{imported} students imported."
                    )

                    if skipped:

                        st.warning(
                            f"{skipped} rows skipped."
                        )

                    st.rerun()

            except Exception as error:

                st.error(
                    "Unable to read file: "
                    + str(error)
                )

    st.divider()

    students = get_students()

    st.subheader(
        f"👨‍🎓 Enrolled Students: {len(students)}"
    )

    if not students.empty:

        st.dataframe(
            students,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CLO MANAGEMENT
# ============================================================

elif page == "🎯 CLO Management":

    st.title("🎯 CLO Management")

    courses = get_courses()

    if courses.empty:

        st.warning(
            "Please create a course first."
        )

    else:

        selected_course = st.selectbox(
            "📚 Select Course",
            courses["Course Code"].tolist()
        )

        with st.form("clo_form"):

            c1, c2 = st.columns(2)

            with c1:

                clo_code = st.text_input(
                    "CLO Code",
                    placeholder="CLO1"
                )

                bloom_level = st.selectbox(
                    "Bloom Level",
                    [
                        "Remember",
                        "Understand",
                        "Apply",
                        "Analyze",
                        "Evaluate",
                        "Create"
                    ]
                )

            with c2:

                clo_description = st.text_area(
                    "CLO Description",
                    placeholder=(
                        "Explain fundamental programming concepts."
                    )
                )

            save_clo = st.form_submit_button(
                "➕ ADD CLO",
                type="primary",
                use_container_width=True
            )

        if save_clo:

            if (
                not clo_code.strip()
                or not clo_description.strip()
            ):

                st.error(
                    "CLO Code and Description are required."
                )

            else:

                success = execute(
                    """
                    INSERT INTO clos
                    (
                        course_code,
                        clo_code,
                        description,
                        bloom_level
                    )

                    VALUES (?, ?, ?, ?)

                    ON CONFLICT(
                        course_code,
                        clo_code
                    )
                    DO UPDATE SET

                        description =
                            excluded.description,

                        bloom_level =
                            excluded.bloom_level
                    """,
                    (
                        selected_course,
                        clo_code.strip().upper(),
                        clo_description.strip(),
                        bloom_level
                    )
                )

                if success:

                    st.success(
                        "CLO saved successfully."
                    )

                    st.rerun()

        st.divider()

        clo_data = get_clos()

        course_clos = clo_data[
            clo_data["Course Code"]
            == selected_course
        ]

        if course_clos.empty:

            st.info(
                "No CLOs created for this course."
            )

        else:

            st.dataframe(
                course_clos,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# PLO MANAGEMENT
# ============================================================

elif page == "🏆 PLO Management":

    st.title("🏆 PLO Management")

    with st.form("plo_form"):

        plo_code = st.text_input(
            "PLO Code",
            placeholder="PLO1"
        )

        plo_description = st.text_area(
            "PLO Description",
            placeholder=(
                "Knowledge of computing."
            )
        )

        save_plo = st.form_submit_button(
            "➕ ADD PLO",
            type="primary",
            use_container_width=True
        )

    if save_plo:

        if (
            not plo_code.strip()
            or not plo_description.strip()
        ):

            st.error(
                "PLO Code and Description are required."
            )

        else:

            success = execute(
                """
                INSERT INTO plos
                (
                    plo_code,
                    description
                )

                VALUES (?, ?)

                ON CONFLICT(plo_code)
                DO UPDATE SET

                    description =
                        excluded.description
                """,
                (
                    plo_code.strip().upper(),
                    plo_description.strip()
                )
            )

            if success:

                st.success(
                    "PLO saved successfully."
                )

                st.rerun()

    st.divider()

    plo_data = get_plos()

    if plo_data.empty:

        st.info(
            "No PLOs have been created."
        )

    else:

        st.dataframe(
            plo_data,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ASSESSMENT CREATION
# ============================================================

elif page == "📝 Assessment Creation":

    st.title("📝 Assessment Creation")

    st.markdown(
        """
        <div class="hero">

            <div class="hero-title">
                📝 Create Assessments
            </div>

            <div class="hero-text">
                Create quizzes, assignments, midterms,
                final examinations, projects and practicals.
                Select the CLOs assessed by each assessment.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    courses = get_courses()

    if courses.empty:

        st.warning(
            "Create a course first."
        )

    else:

        selected_course = st.selectbox(
            "📚 Select Course",
            courses["Course Code"].tolist()
        )

        clo_data = get_clos()

        course_clos = clo_data[
            clo_data["Course Code"]
            == selected_course
        ]

        with st.form("assessment_form"):

            c1, c2 = st.columns(2)

            with c1:

                assessment_name = st.text_input(
                    "Assessment Name",
                    placeholder="Midterm Examination"
                )

                assessment_type = st.selectbox(
                    "Assessment Type",
                    [
                        "Quiz",
                        "Assignment",
                        "Class Test",
                        "Midterm Examination",
                        "Final Examination",
                        "Project",
                        "Presentation",
                        "Lab",
                        "Practical",
                        "Other"
                    ]
                )

                assessment_date = st.date_input(
                    "Assessment Date"
                )

            with c2:

                total_marks = st.number_input(
                    "Total Marks",
                    min_value=1.0,
                    value=100.0,
                    step=1.0
                )

                weightage = st.number_input(
                    "Weightage (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=10.0,
                    step=1.0
                )

                assessment_description = st.text_area(
                    "Description"
                )

            st.subheader(
                "🎯 CLOs Assessed"
            )

            selected_clos = []

            if course_clos.empty:

                st.info(
                    "Create CLOs for this course first."
                )

            else:

                for _, row in course_clos.iterrows():

                    selected = st.checkbox(
                        f"{row['CLO']} — "
                        f"{row['Description']}",
                        key=(
                            "assessment_"
                            + selected_course
                            + "_"
                            + row["CLO"]
                        )
                    )

                    if selected:

                        selected_clos.append(
                            row["CLO"]
                        )

            create_assessment = st.form_submit_button(
                "🚀 CREATE ASSESSMENT",
                type="primary",
                use_container_width=True
            )

        if create_assessment:

            if not assessment_name.strip():

                st.error(
                    "Assessment Name is required."
                )

            elif not selected_clos:

                st.error(
                    "Select at least one CLO."
                )

            else:

                success = execute(
                    """
                    INSERT INTO assessments
                    (
                        course_code,
                        assessment_name,
                        assessment_type,
                        assessment_date,
                        total_marks,
                        weightage,
                        description
                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?)

                    ON CONFLICT(
                        course_code,
                        assessment_name
                    )
                    DO UPDATE SET

                        assessment_type =
                            excluded.assessment_type,

                        assessment_date =
                            excluded.assessment_date,

                        total_marks =
                            excluded.total_marks,

                        weightage =
                            excluded.weightage,

                        description =
                            excluded.description
                    """,
                    (
                        selected_course,
                        assessment_name.strip(),
                        assessment_type,
                        str(assessment_date),
                        total_marks,
                        weightage,
                        assessment_description.strip()
                    )
                )

                if success:

                    assessment_rows = execute(
                        """
                        SELECT id

                        FROM assessments

                        WHERE course_code = ?

                        AND assessment_name = ?
                        """,
                        (
                            selected_course,
                            assessment_name.strip()
                        ),
                        fetch=True
                    )

                    if assessment_rows:

                        assessment_id = (
                            assessment_rows[0][0]
                        )

                        execute(
                            """
                            DELETE FROM assessment_clos

                            WHERE assessment_id = ?
                            """,
                            (
                                assessment_id,
                            )
                        )

                        for clo in selected_clos:

                            execute(
                                """
                                INSERT INTO assessment_clos
                                (
                                    assessment_id,
                                    clo_code
                                )

                                VALUES (?, ?)
                                """,
                                (
                                    assessment_id,
                                    clo
                                )
                            )

                    st.success(
                        "Assessment created successfully."
                    )

                    st.rerun()

        st.divider()

        st.subheader(
            "📋 Existing Assessments"
        )

        assessments = execute(
            """
            SELECT
                id,
                assessment_name,
                assessment_type,
                assessment_date,
                total_marks,
                weightage,
                description

            FROM assessments

            WHERE course_code = ?

            ORDER BY
                assessment_date,
                id
            """,
            (
                selected_course,
            ),
            fetch=True
        )

        if not assessments:

            st.info(
                "No assessments created yet."
            )

        else:

            assessment_table = pd.DataFrame(
                assessments,
                columns=[
                    "ID",
                    "Assessment",
                    "Type",
                    "Date",
                    "Total Marks",
                    "Weightage %",
                    "Description"
                ]
            )

            st.dataframe(
                assessment_table,
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "🎯 CLO Assignment"
            )

            for item in assessments:

                assessment_id = item[0]
                assessment_name_existing = item[1]

                assigned = execute(
                    """
                    SELECT clo_code

                    FROM assessment_clos

                    WHERE assessment_id = ?

                    ORDER BY clo_code
                    """,
                    (
                        assessment_id,
                    ),
                    fetch=True
                )

                assigned_clos = [
                    row[0]
                    for row in assigned
                ]

                if assigned_clos:

                    st.success(
                        f"{assessment_name_existing}: "
                        + ", ".join(assigned_clos)
                    )

                else:

                    st.warning(
                        f"{assessment_name_existing}: "
                        "No CLO assigned"
                    )


# ============================================================
# CLO PLO MAPPING
# ============================================================

elif page == "🔗 CLO–PLO Mapping":

    st.title("🔗 CLO–PLO Mapping")

    courses = get_courses()
    clos = get_clos()
    plos = get_plos()

    if courses.empty:

        st.warning(
            "Create courses first."
        )

    elif clos.empty:

        st.warning(
            "Create CLOs first."
        )

    elif plos.empty:

        st.warning(
            "Create PLOs first."
        )

    else:

        selected_course = st.selectbox(
            "📚 Select Course",
            courses["Course Code"].tolist()
        )

        course_clos = clos[
            clos["Course Code"]
            == selected_course
        ]

        st.info(
            "Mapping scale: "
            "0 = None | "
            "1 = Low | "
            "2 = Medium | "
            "3 = High"
        )

        mapping_values = {}

        for _, clo_row in course_clos.iterrows():

            st.markdown(
                f"### {clo_row['CLO']}"
            )

            st.caption(
                clo_row["Description"]
            )

            columns = st.columns(
                len(plos)
            )

            for index, plo in enumerate(
                plos["PLO"]
            ):

                with columns[index]:

                    mapping_values[
                        clo_row["CLO"],
                        plo
                    ] = st.selectbox(
                        plo,
                        [0, 1, 2, 3],
                        key=(
                            "mapping_"
                            + selected_course
                            + "_"
                            + clo_row["CLO"]
                            + "_"
                            + plo
                        )
                    )

        if st.button(
            "💾 SAVE CLO–PLO MAPPING",
            type="primary",
            use_container_width=True
        ):

            for (
                clo_code,
                plo_code
            ), strength in mapping_values.items():

                execute(
                    """
                    INSERT INTO mappings
                    (
                        course_code,
                        clo_code,
                        plo_code,
                        strength
                    )

                    VALUES (?, ?, ?, ?)

                    ON CONFLICT(
                        course_code,
                        clo_code,
                        plo_code
                    )
                    DO UPDATE SET

                        strength =
                            excluded.strength
                    """,
                    (
                        selected_course,
                        clo_code,
                        plo_code,
                        strength
                    )
                )

            st.success(
                "CLO–PLO mapping saved."
            )

            st.rerun()


# ============================================================
# BULK MARKS UPLOAD
# ============================================================

elif page == "📥 Bulk Marks Upload":

    st.title("📥 Bulk Marks Upload")

    st.markdown(
        """
        <div class="hero">

            <div class="hero-title">
                🚀 Upload the Whole Class at Once
            </div>

            <div class="hero-text">
                Do not enter marks one student at a time.
                Upload one Excel or CSV file containing
                the complete class results.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    template = pd.DataFrame(
        {
            "Roll Number": [
                "CS001",
                "CS001",
                "CS002",
                "CS002"
            ],

            "Course Code": [
                "CS101",
                "CS101",
                "CS101",
                "CS101"
            ],

            "Assessment": [
                "Midterm",
                "Midterm",
                "Midterm",
                "Midterm"
            ],

            "CLO": [
                "CLO1",
                "CLO2",
                "CLO1",
                "CLO2"
            ],

            "Obtained Marks": [
                80,
                75,
                65,
                70
            ],

            "Total Marks": [
                100,
                100,
                100,
                100
            ]
        }
    )

    st.subheader(
        "📄 Required File Format"
    )

    st.dataframe(
        template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ DOWNLOAD MARKS TEMPLATE",
        template.to_csv(
            index=False
        ).encode(),
        "Fast_Tutor_Marks_Template.csv",
        "text/csv"
    )

    uploaded_marks = st.file_uploader(
        "📥 Upload Complete Marks File",
        type=[
            "csv",
            "xlsx",
            "xls"
        ],
        key="marks_file"
    )

    if uploaded_marks:

        try:

            if uploaded_marks.name.lower().endswith(
                ".csv"
            ):

                marks_df = pd.read_csv(
                    uploaded_marks
                )

            else:

                marks_df = pd.read_excel(
                    uploaded_marks
                )

            st.success(
                f"{len(marks_df)} marks records detected."
            )

            st.dataframe(
                marks_df.head(100),
                use_container_width=True,
                hide_index=True
            )

            roll_column = find_column(
                marks_df,
                [
                    "roll_number",
                    "roll_no",
                    "roll",
                    "registration_number",
                    "registration_no"
                ]
            )

            course_column = find_column(
                marks_df,
                [
                    "course_code",
                    "course",
                    "subject_code"
                ]
            )

            assessment_column = find_column(
                marks_df,
                [
                    "assessment",
                    "assessment_name",
                    "exam",
                    "test"
                ]
            )

            clo_column = find_column(
                marks_df,
                [
                    "clo",
                    "clo_code"
                ]
            )

            obtained_column = find_column(
                marks_df,
                [
                    "obtained_marks",
                    "marks_obtained",
                    "obtained",
                    "marks",
                    "score"
                ]
            )

            total_column = find_column(
                marks_df,
                [
                    "total_marks",
                    "maximum_marks",
                    "max_marks",
                    "total"
                ]
            )

            missing_columns = []

            if not roll_column:
                missing_columns.append(
                    "Roll Number"
                )

            if not course_column:
                missing_columns.append(
                    "Course Code"
                )

            if not assessment_column:
                missing_columns.append(
                    "Assessment"
                )

            if not obtained_column:
                missing_columns.append(
                    "Obtained Marks"
                )

            if missing_columns:

                st.error(
                    "Missing required columns: "
                    + ", ".join(
                        missing_columns
                    )
                )

            else:

                if st.button(
                    "🚀 IMPORT ALL MARKS",
                    type="primary",
                    use_container_width=True
                ):

                    progress = st.progress(0)

                    added = 0
                    updated = 0
                    skipped = 0

                    total_rows = max(
                        len(marks_df),
                        1
                    )

                    for index, row in marks_df.iterrows():

                        try:

                            roll_value = str(
                                row[roll_column]
                            ).strip()

                            course_value = str(
                                row[course_column]
                            ).strip().upper()

                            assessment_value = str(
                                row[assessment_column]
                            ).strip()

                            clo_value = ""

                            if clo_column:

                                clo_value = str(
                                    row[clo_column]
                                ).strip().upper()

                                if clo_value.lower() == "nan":
                                    clo_value = ""

                            obtained = float(
                                row[obtained_column]
                            )

                            if total_column:

                                total = float(
                                    row[total_column]
                                )

                            else:

                                total = 100.0

                            if (
                                not roll_value
                                or roll_value.lower()
                                == "nan"
                            ):

                                skipped += 1
                                continue

                            if (
                                not course_value
                                or course_value.lower()
                                == "nan"
                            ):

                                skipped += 1
                                continue

                            if (
                                not assessment_value
                                or assessment_value.lower()
                                == "nan"
                            ):

                                skipped += 1
                                continue

                            if total <= 0:

                                skipped += 1
                                continue

                            student_exists = execute(
                                """
                                SELECT id

                                FROM students

                                WHERE roll_no = ?
                                """,
                                (
                                    roll_value,
                                ),
                                fetch=True
                            )

                            if not student_exists:

                                skipped += 1
                                continue

                            percentage = (
                                obtained
                                /
                                total
                            ) * 100

                            grade = calculate_grade(
                                percentage
                            )

                            existing = execute(
                                """
                                SELECT id

                                FROM results

                                WHERE roll_no = ?

                                AND course_code = ?

                                AND assessment = ?

                                AND clo_code = ?
                                """,
                                (
                                    roll_value,
                                    course_value,
                                    assessment_value,
                                    clo_value
                                ),
                                fetch=True
                            )

                            if existing:

                                execute(
                                    """
                                    UPDATE results

                                    SET
                                        obtained = ?,
                                        total = ?,
                                        percentage = ?,
                                        grade = ?

                                    WHERE roll_no = ?

                                    AND course_code = ?

                                    AND assessment = ?

                                    AND clo_code = ?
                                    """,
                                    (
                                        obtained,
                                        total,
                                        percentage,
                                        grade,
                                        roll_value,
                                        course_value,
                                        assessment_value,
                                        clo_value
                                    )
                                )

                                updated += 1

                            else:

                                execute(
                                    """
                                    INSERT INTO results
                                    (
                                        roll_no,
                                        course_code,
                                        assessment,
                                        clo_code,
                                        obtained,
                                        total,
                                        percentage,
                                        grade
                                    )

                                    VALUES (
                                        ?,
                                        ?,
                                        ?,
                                        ?,
                                        ?,
                                        ?,
                                        ?,
                                        ?
                                    )
                                    """,
                                    (
                                        roll_value,
                                        course_value,
                                        assessment_value,
                                        clo_value,
                                        obtained,
                                        total,
                                        percentage,
                                        grade
                                    )
                                )

                                added += 1

                        except Exception:

                            skipped += 1

                        progress.progress(
                            (index + 1)
                            /
                            total_rows
                        )

                    st.success(
                        "Marks upload completed."
                    )

                    st.info(
                        f"Added: {added} | "
                        f"Updated: {updated} | "
                        f"Skipped: {skipped}"
                    )

                    st.rerun()

        except Exception as error:

            st.error(
                "Could not read marks file: "
                + str(error)
            )


# ============================================================
# STUDENT PERFORMANCE
# ============================================================

elif page == "📊 Student Performance":

    st.title(
        "📊 Individual Student Performance"
    )

    students = get_students()
    results = get_results()

    if students.empty:

        st.warning(
            "No students have been enrolled."
        )

    elif results.empty:

        st.warning(
            "No marks have been uploaded."
        )

    else:

        selected_roll = st.selectbox(
            "👨‍🎓 Select Student",
            students["Roll Number"].tolist()
        )

        student_rows = students[
            students["Roll Number"]
            == selected_roll
        ]

        if student_rows.empty:

            st.error(
                "Student not found."
            )

        else:

            student = student_rows.iloc[0]

            student_results = results[
                results["Roll Number"]
                == selected_roll
            ].copy()

            st.markdown(
                f"""
                <div class="hero">

                    <div class="hero-title">
                        🎓 {student["Student Name"]}
                    </div>

                    <div class="hero-text">

                        Roll Number:
                        <b>{student["Roll Number"]}</b>

                        &nbsp; | &nbsp;

                        Program:
                        <b>{student["Program"]}</b>

                        &nbsp; | &nbsp;

                        Semester:
                        <b>{student["Semester"]}</b>

                        &nbsp; | &nbsp;

                        Section:
                        <b>{student["Section"]}</b>

                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            overall = student_results[
                "Percentage"
            ].mean()

            passed = len(
                student_results[
                    student_results["Grade"]
                    != "F"
                ]
            )

            failed = len(
                student_results[
                    student_results["Grade"]
                    == "F"
                ]
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Overall",
                f"{overall:.1f}%"
            )

            c2.metric(
                "Records",
                len(student_results)
            )

            c3.metric(
                "Passed",
                passed
            )

            c4.metric(
                "Failed",
                failed
            )

            st.divider()

            # ------------------------------------------------
            # COURSE PERFORMANCE
            # ------------------------------------------------

            st.subheader(
                "📚 Course Performance"
            )

            course_performance = (
                student_results
                .groupby(
                    "Course Code"
                )["Percentage"]
                .mean()
                .round(2)
            )

            if not course_performance.empty:

                st.bar_chart(
                    course_performance
                )

            # ------------------------------------------------
            # ASSESSMENT PERFORMANCE
            # ------------------------------------------------

            st.subheader(
                "📝 Assessment Performance"
            )

            assessment_performance = (
                student_results
                .groupby(
                    "Assessment"
                )["Percentage"]
                .mean()
                .round(2)
            )

            if not assessment_performance.empty:

                st.line_chart(
                    assessment_performance
                )

            # ------------------------------------------------
            # CLO ATTAINMENT
            # ------------------------------------------------

            st.subheader(
                "🎯 CLO Attainment"
            )

            clo_results = student_results[
                student_results["CLO"]
                .astype(str)
                .str.strip()
                != ""
            ]

            if clo_results.empty:

                st.info(
                    "No CLO-level marks available."
                )

            else:

                clo_attainment = (
                    clo_results
                    .groupby(
                        "CLO"
                    )["Percentage"]
                    .mean()
                    .round(2)
                )

                st.bar_chart(
                    clo_attainment
                )

                for clo, value in (
                    clo_attainment.items()
                ):

                    if value >= 70:

                        st.success(
                            f"{clo}: "
                            f"{value:.1f}% — Achieved"
                        )

                    else:

                        st.warning(
                            f"{clo}: "
                            f"{value:.1f}% — "
                            "Needs Improvement"
                        )

            # ------------------------------------------------
            # PLO ATTAINMENT
            # ------------------------------------------------

            st.subheader(
                "🏆 PLO Attainment"
            )

            mappings = get_mappings()

            if mappings.empty:

                st.info(
                    "Create CLO–PLO mappings first."
                )

            elif clo_results.empty:

                st.info(
                    "CLO-level results are required "
                    "to calculate PLO attainment."
                )

            else:

                plo_values = {}

                for plo_code in (
                    mappings["PLO"].unique()
                ):

                    plo_mapping = mappings[
                        mappings["PLO"]
                        == plo_code
                    ]

                    weighted_values = []

                    for _, mapping in (
                        plo_mapping.iterrows()
                    ):

                        strength = float(
                            mapping["Strength"]
                        )

                        if strength <= 0:
                            continue

                        matching = clo_results[
                            (
                                clo_results[
                                    "Course Code"
                                ]
                                ==
                                mapping[
                                    "Course Code"
                                ]
                            )
                            &
                            (
                                clo_results[
                                    "CLO"
                                ]
                                ==
                                mapping[
                                    "CLO"
                                ]
                            )
                        ]

                        if not matching.empty:

                            clo_percentage = (
                                matching[
                                    "Percentage"
                                ].mean()
                            )

                            weighted_values.append(
                                (
                                    clo_percentage,
                                    strength
                                )
                            )

                    if weighted_values:

                        numerator = sum(
                            value * weight
                            for value, weight
                            in weighted_values
                        )

                        denominator = sum(
                            weight
                            for value, weight
                            in weighted_values
                        )

                        if denominator > 0:

                            plo_values[
                                plo_code
                            ] = (
                                numerator
                                /
                                denominator
                            )

                if plo_values:

                    plo_attainment = pd.Series(
                        plo_values
                    ).round(2)

                    st.bar_chart(
                        plo_attainment
                    )

                    for plo, value in (
                        plo_attainment.items()
                    ):

                        if value >= 70:

                            st.success(
                                f"{plo}: "
                                f"{value:.1f}% — Achieved"
                            )

                        else:

                            st.warning(
                                f"{plo}: "
                                f"{value:.1f}% — "
                                "Needs Improvement"
                            )

                else:

                    st.info(
                        "There is not enough mapped "
                        "CLO data to calculate PLO attainment."
                    )

            # ------------------------------------------------
            # DETAILED RESULTS
            # ------------------------------------------------

            st.subheader(
                "📋 Detailed Student Results"
            )

            st.dataframe(
                student_results,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# ATTAINMENT DASHBOARD
# ============================================================

elif page == "📈 Attainment Dashboard":

    st.title(
        "📈 Attainment Dashboard"
    )

    results = get_results()

    if results.empty:

        st.info(
            "Upload marks first."
        )

    else:

        # ----------------------------------------------------
        # CLO
        # ----------------------------------------------------

        clo_results = results[
            results["CLO"]
            .astype(str)
            .str.strip()
            != ""
        ]

        if not clo_results.empty:

            st.subheader(
                "🎯 Overall CLO Attainment"
            )

            clo_attainment = (
                clo_results
                .groupby(
                    "CLO"
                )["Percentage"]
                .mean()
                .round(2)
            )

            st.bar_chart(
                clo_attainment
            )

        else:

            st.info(
                "No CLO-level results found."
            )

        # ----------------------------------------------------
        # PLO
        # ----------------------------------------------------

        mappings = get_mappings()

        if (
            not mappings.empty
            and not clo_results.empty
        ):

            st.subheader(
                "🏆 Overall PLO Attainment"
            )

            plo_values = {}

            for plo_code in (
                mappings["PLO"].unique()
            ):

                plo_mapping = mappings[
                    mappings["PLO"]
                    == plo_code
                ]

                weighted_values = []

                for _, mapping in (
                    plo_mapping.iterrows()
                ):

                    strength = float(
                        mapping["Strength"]
                    )

                    if strength <= 0:
                        continue

                    matching = clo_results[
                        (
                            clo_results[
                                "Course Code"
                            ]
                            ==
                            mapping[
                                "Course Code"
                            ]
                        )
                        &
                        (
                            clo_results[
                                "CLO"
                            ]
                            ==
                            mapping[
                                "CLO"
                            ]
                        )
                    ]

                    if not matching.empty:

                        weighted_values.append(
                            (
                                matching[
                                    "Percentage"
                                ].mean(),
                                strength
                            )
                        )

                if weighted_values:

                    denominator = sum(
                        weight
                        for value, weight
                        in weighted_values
                    )

                    if denominator > 0:

                        numerator = sum(
                            value * weight
                            for value, weight
                            in weighted_values
                        )

                        plo_values[
                            plo_code
                        ] = (
                            numerator
                            /
                            denominator
                        )

            if plo_values:

                plo_attainment = pd.Series(
                    plo_values
                ).round(2)

                st.bar_chart(
                    plo_attainment
                )

                weak_plos = (
                    plo_attainment[
                        plo_attainment < 70
                    ]
                )

                if not weak_plos.empty:

                    st.subheader(
                        "⚠️ PLOs Requiring Attention"
                    )

                    st.dataframe(
                        weak_plos.rename(
                            "Attainment"
                        ).to_frame(),
                        use_container_width=True
                    )


# ============================================================
# REPORTS
# ============================================================

elif page == "📤 Reports & Export":

    st.title(
        "📤 Reports & Export"
    )

    courses = get_courses()
    students = get_students()
    clos = get_clos()
    plos = get_plos()
    mappings = get_mappings()
    results = get_results()

    assessment_rows = execute(
        """
        SELECT
            course_code,
            assessment_name,
            assessment_type,
            assessment_date,
            total_marks,
            weightage,
            description

        FROM assessments

        ORDER BY
            course_code,
            assessment_date
        """,
        fetch=True
    )

    if assessment_rows:

        assessments = pd.DataFrame(
            assessment_rows,
            columns=[
                "Course Code",
                "Assessment",
                "Type",
                "Date",
                "Total Marks",
                "Weightage",
                "Description"
            ]
        )

    else:

        assessments = pd.DataFrame(
            columns=[
                "Course Code",
                "Assessment",
                "Type",
                "Date",
                "Total Marks",
                "Weightage",
                "Description"
            ]
        )

    st.subheader(
        "📊 Complete Excel Report"
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        courses.to_excel(
            writer,
            index=False,
            sheet_name="Courses"
        )

        students.to_excel(
            writer,
            index=False,
            sheet_name="Students"
        )

        clos.to_excel(
            writer,
            index=False,
            sheet_name="CLOs"
        )

        plos.to_excel(
            writer,
            index=False,
            sheet_name="PLOs"
        )

        assessments.to_excel(
            writer,
            index=False,
            sheet_name="Assessments"
        )

        mappings.to_excel(
            writer,
            index=False,
            sheet_name="CLO-PLO Mapping"
        )

        results.to_excel(
            writer,
            index=False,
            sheet_name="Marks"
        )

    st.download_button(
        "⬇️ DOWNLOAD COMPLETE FAST TUTOR REPORT",
        output.getvalue(),
        "Fast_Tutor_Complete_Report.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "👨‍🎓 Individual Student Report"
    )

    if students.empty:

        st.info(
            "No students available."
        )

    else:

        selected_roll = st.selectbox(
            "Select Student",
            students["Roll Number"].tolist()
        )

        individual_results = results[
            results["Roll Number"]
            == selected_roll
        ]

        if individual_results.empty:

            st.info(
                "No results found for this student."
            )

        else:

            st.dataframe(
                individual_results,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ DOWNLOAD STUDENT RESULTS",
                individual_results.to_csv(
                    index=False
                ).encode(),
                f"Fast_Tutor_{selected_roll}.csv",
                "text/csv",
                use_container_width=True
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        padding:18px;
        color:#777;
    ">

        <div style="
            font-size:18px;
            font-weight:800;
            color:#0795D1;
        ">
            ⚡ FAST TUTOR
        </div>

        <div style="
            font-size:12px;
            margin-top:5px;
        ">
            Student Performance & Attainment System
        </div>

    </div>
    """,
    unsafe_allow_html=True
)
