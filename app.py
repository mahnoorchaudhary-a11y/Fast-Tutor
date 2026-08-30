import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO


# ============================================================
# FAST TUTOR
# Student Performance System
# ============================================================

st.set_page_config(
    page_title="Fast Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE
# ============================================================

# IMPORTANT:
# Streamlit Cloud may not allow writing to the project folder.
# Therefore the SQLite database is stored in /tmp.
DB_PATH = "/tmp/fast_tutor.db"


@st.cache_resource
def get_database():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    # --------------------------------------------------------
    # COURSES
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            credit_hours REAL DEFAULT 3,
            semester TEXT DEFAULT ''
        )
    """)

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            program TEXT DEFAULT '',
            semester TEXT DEFAULT '',
            section TEXT DEFAULT ''
        )
    """)

    # --------------------------------------------------------
    # ASSESSMENTS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            name TEXT NOT NULL,
            assessment_type TEXT DEFAULT '',
            total_marks REAL DEFAULT 100,
            weightage REAL DEFAULT 0
        )
    """)

    # --------------------------------------------------------
    # CLOs
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS clos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            clo TEXT NOT NULL,
            description TEXT DEFAULT '',
            bloom TEXT DEFAULT ''
        )
    """)

    # --------------------------------------------------------
    # PLOs
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS plos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plo TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT ''
        )
    """)

    # --------------------------------------------------------
    # CLO-PLO MAPPING
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            clo TEXT NOT NULL,
            plo TEXT NOT NULL,
            strength INTEGER DEFAULT 0
        )
    """)

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    connection.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            course_code TEXT NOT NULL,
            assessment TEXT NOT NULL,
            clo TEXT DEFAULT '',
            obtained REAL DEFAULT 0,
            total REAL DEFAULT 100,
            percentage REAL DEFAULT 0,
            grade TEXT DEFAULT ''
        )
    """)

    connection.commit()

    return connection


db = get_database()


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def execute(sql, values=()):

    try:

        cursor = db.cursor()

        cursor.execute(
            sql,
            values
        )

        db.commit()

        return True

    except sqlite3.Error as error:

        db.rollback()

        st.error(
            f"Database operation failed: {error}"
        )

        return False


def query(sql, values=()):

    try:

        cursor = db.cursor()

        cursor.execute(
            sql,
            values
        )

        return cursor.fetchall()

    except sqlite3.Error as error:

        st.error(
            f"Database read failed: {error}"
        )

        return []


def one(sql, values=()):

    rows = query(
        sql,
        values
    )

    if rows:

        return rows[0]

    return None


# ============================================================
# GENERAL FUNCTIONS
# ============================================================

def clean(value):

    if value is None:
        return ""

    try:

        if pd.isna(value):
            return ""

    except Exception:
        pass

    return str(value).strip()


def number(value, default=0):

    try:

        if pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


def percentage(obtained, total):

    if total <= 0:

        return 0

    return round(
        (obtained / total) * 100,
        2
    )


def grade(mark):

    if mark >= 90:
        return "A+"

    if mark >= 80:
        return "A"

    if mark >= 70:
        return "B"

    if mark >= 60:
        return "C"

    if mark >= 50:
        return "D"

    return "F"


def make_df(rows, columns):

    if not rows:

        return pd.DataFrame(
            columns=columns
        )

    return pd.DataFrame(
        rows,
        columns=columns
    )


def read_file(uploaded_file):

    if uploaded_file is None:

        return None

    try:

        filename = uploaded_file.name.lower()

        if filename.endswith(".csv"):

            return pd.read_csv(
                uploaded_file
            )

        if filename.endswith(".xlsx"):

            return pd.read_excel(
                uploaded_file
            )

        if filename.endswith(".xls"):

            return pd.read_excel(
                uploaded_file
            )

        st.error(
            "Please upload a CSV or Excel file."
        )

        return None

    except Exception as error:

        st.error(
            f"Could not read file: {error}"
        )

        return None


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main page */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* Sidebar */

    section[data-testid="stSidebar"] {
        background-color: #F8FBFD;
    }


    /* Headings */

    h1, h2, h3 {
        color: #172B4D;
    }


    /* Metric cards */

    div[data-testid="stMetric"] {

        background: white;

        border: 1px solid #E5E7EB;

        padding: 15px;

        border-radius: 15px;

        box-shadow:
            0 3px 12px
            rgba(0,0,0,0.04);
    }


    /* Buttons */

    .stButton button {

        border-radius: 10px;

        font-weight: 600;
    }


    /* Dataframes */

    div[data-testid="stDataFrame"] {

        border-radius: 12px;
        overflow: hidden;
    }


    /* Hero */

    .fast-hero {

        background:
        linear-gradient(
            135deg,
            #0795D1,
            #0877A6
        );

        padding: 32px;

        border-radius: 22px;

        color: white;

        margin-bottom: 25px;

        box-shadow:
        0 10px 30px
        rgba(7,149,209,0.20);
    }


    .fast-hero-title {

        font-size: 34px;

        font-weight: 900;

        margin-bottom: 8px;
    }


    .fast-hero-text {

        font-size: 16px;

        line-height: 1.6;

        opacity: 0.95;
    }


    .small-card {

        background: white;

        border: 1px solid #E5E7EB;

        border-radius: 16px;

        padding: 20px;

        min-height: 130px;

        box-shadow:
        0 4px 14px
        rgba(0,0,0,0.04);
    }


    .small-card-icon {

        font-size: 30px;
    }


    .small-card-title {

        color: #667085;

        font-size: 13px;

        margin-top: 7px;
    }


    .small-card-number {

        color: #0795D1;

        font-size: 30px;

        font-weight: 900;
    }


    .section-heading {

        font-size: 23px;

        font-weight: 800;

        color: #172B4D;

        margin-top: 25px;

        margin-bottom: 15px;
    }


    .tip-box {

        background: #F3FAFE;

        border-left: 5px solid #0795D1;

        padding: 18px;

        border-radius: 12px;

        color: #475467;

        margin-top: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        text-align:center;
        padding:10px 5px 22px 5px;
    ">

        <div style="
            font-size:30px;
            font-weight:900;
            color:#0795D1;
            letter-spacing:1px;
        ">
            🎓 FAST TUTOR
        </div>

        <div style="
            color:#7A869A;
            font-size:12px;
            margin-top:5px;
        ">
            Student Performance System
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# NAVIGATION
# ============================================================

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Dashboard",
        "📚 Courses",
        "👨‍🎓 Students",
        "📝 Assessments",
        "🎯 CLO Management",
        "🏆 PLO Management",
        "🔗 CLO-PLO Mapping",
        "📥 Bulk Marks",
        "👤 Student Performance",
        "📊 Attainment",
        "📑 Reports"
    ]
)


st.sidebar.divider()

st.sidebar.caption(
    "Fast Tutor"
)

st.sidebar.caption(
    "Simple • Intelligent • Student Focused"
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        """
        <div class="fast-hero">

            <div style="
                font-size:15px;
                font-weight:700;
                margin-bottom:7px;
            ">
                🎓 FAST TUTOR
            </div>

            <div class="fast-hero-title">
                Academic Performance Dashboard
            </div>

            <div class="fast-hero-text">
                Manage courses, students, assessments,
                marks and learning-outcome attainment
                from one simple platform.
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # COUNTS
    # --------------------------------------------------------

    courses_count = one(
        "SELECT COUNT(*) FROM courses"
    )[0]

    students_count = one(
        "SELECT COUNT(*) FROM students"
    )[0]

    assessments_count = one(
        "SELECT COUNT(*) FROM assessments"
    )[0]

    clos_count = one(
        "SELECT COUNT(*) FROM clos"
    )[0]

    plos_count = one(
        "SELECT COUNT(*) FROM plos"
    )[0]

    results_count = one(
        "SELECT COUNT(*) FROM results"
    )[0]

    st.markdown(
        '<div class="section-heading">📊 Overview</div>',
        unsafe_allow_html=True
    )

    # First row

    a, b, c = st.columns(3)

    with a:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="small-card-icon">
                    📚
                </div>

                <div class="small-card-title">
                    Courses
                </div>

                <div class="small-card-number">
                    {courses_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with b:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="small-card-icon">
                    👨‍🎓
                </div>

                <div class="small-card-title">
                    Students
                </div>

                <div class="small-card-number">
                    {students_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with c:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="small-card-icon">
                    📝
                </div>

                <div class="small-card-title">
                    Assessments
                </div>

                <div class="small-card-number">
                    {assessments_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # Second row

    d, e, f = st.columns(3)

    with d:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="small-card-icon">
                    🎯
                </div>

                <div class="small-card-title">
                    CLOs
                </div>

                <div class="small-card-number">
                    {clos_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with e:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="small-card-icon">
                    🏆
                </div>

                <div class="small-card-title">
                    PLOs
                </div>

                <div class="small-card-number">
                    {plos_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    with f:

        st.markdown(
            f"""
            <div class="small-card">

                <div class="small-card-icon">
                    📈
                </div>

                <div class="small-card-title">
                    Mark Records
                </div>

                <div class="small-card-number">
                    {results_count}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    # --------------------------------------------------------
    # QUICK ACTIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">⚡ Quick Actions</div>',
        unsafe_allow_html=True
    )

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        st.info(
            "📚 **Courses**\n\n"
            "Create and manage your courses."
        )

    with q2:

        st.info(
            "👨‍🎓 **Students**\n\n"
            "Import your complete class list."
        )

    with q3:

        st.info(
            "📝 **Assessments**\n\n"
            "Create quizzes, exams and assignments."
        )

    with q4:

        st.info(
            "📥 **Bulk Marks**\n\n"
            "Upload marks for the entire class."
        )

    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">📈 Performance Overview</div>',
        unsafe_allow_html=True
    )

    left, right = st.columns(
        [1.5, 1]
    )

    with left:

        st.subheader(
            "Course Average"
        )

        course_rows = query("""
            SELECT
                course_code,
                AVG(percentage)
            FROM results
            GROUP BY course_code
            ORDER BY course_code
        """)

        if course_rows:

            course_df = make_df(
                course_rows,
                [
                    "Course",
                    "Average"
                ]
            )

            course_df["Average"] = pd.to_numeric(
                course_df["Average"],
                errors="coerce"
            ).round(2)

            st.bar_chart(
                course_df.set_index("Course")
            )

        else:

            st.info(
                "Course performance will appear here after marks are uploaded."
            )

    with right:

        st.subheader(
            "CLO Attainment"
        )

        clo_rows = query("""
            SELECT
                clo,
                AVG(percentage)
            FROM results
            WHERE clo != ''
            GROUP BY clo
            ORDER BY clo
        """)

        if clo_rows:

            clo_df = make_df(
                clo_rows,
                [
                    "CLO",
                    "Attainment"
                ]
            )

            clo_df["Attainment"] = pd.to_numeric(
                clo_df["Attainment"],
                errors="coerce"
            ).round(2)

            st.bar_chart(
                clo_df.set_index("CLO")
            )

        else:

            st.info(
                "CLO attainment will appear after marks are uploaded."
            )

    # --------------------------------------------------------
    # TIP
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="tip-box">

            <b>💡 Recommended workflow</b><br><br>

            <b>1.</b> Create your courses →
            <b>2.</b> Import students →
            <b>3.</b> Create assessments →
            <b>4.</b> Define CLOs and PLOs →
            <b>5.</b> Map CLOs to PLOs →
            <b>6.</b> Upload marks in bulk →
            <b>7.</b> Analyse individual performance →
            <b>8.</b> View CLO/PLO attainment.

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# COURSES
# ============================================================

elif page == "📚 Courses":

    st.title("📚 Course Management")

    st.write(
        "Create your courses before enrolling or importing students."
    )

    with st.form("course_form"):

        col1, col2 = st.columns(2)

        with col1:

            code = st.text_input(
                "Course Code",
                placeholder="CS101"
            )

            name = st.text_input(
                "Course Name",
                placeholder="Programming Fundamentals"
            )

        with col2:

            credit_hours = st.number_input(
                "Credit Hours",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5
            )

            semester = st.text_input(
                "Semester",
                placeholder="1"
            )

        submitted = st.form_submit_button(
            "➕ Save Course",
            type="primary"
        )

    if submitted:

        code = clean(code).upper()
        name = clean(name)

        if not code or not name:

            st.warning(
                "Course code and course name are required."
            )

        else:

            existing = one(
                "SELECT id FROM courses WHERE code=?",
                (code,)
            )

            if existing:

                success = execute(
                    """
                    UPDATE courses

                    SET
                        name=?,
                        credit_hours=?,
                        semester=?

                    WHERE code=?
                    """,
                    (
                        name,
                        credit_hours,
                        semester,
                        code
                    )
                )

            else:

                success = execute(
                    """
                    INSERT INTO courses
                    (
                        code,
                        name,
                        credit_hours,
                        semester
                    )

                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        code,
                        name,
                        credit_hours,
                        semester
                    )
                )

            if success:

                st.success(
                    "Course saved successfully."
                )

    st.divider()

    rows = query(
        """
        SELECT
            code,
            name,
            credit_hours,
            semester

        FROM courses

        ORDER BY code
        """
    )

    df = make_df(
        rows,
        [
            "Course Code",
            "Course Name",
            "Credit Hours",
            "Semester"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# STUDENTS
# ============================================================

elif page == "👨‍🎓 Students":

    st.title("👨‍🎓 Student Enrollment")

    tab1, tab2 = st.tabs(
        [
            "Add Student",
            "📥 Bulk Import"
        ]
    )

    # --------------------------------------------------------
    # ADD STUDENT
    # --------------------------------------------------------

    with tab1:

        with st.form("student_form"):

            col1, col2 = st.columns(2)

            with col1:

                roll = st.text_input(
                    "Roll Number",
                    placeholder="CS001"
                )

                student_name = st.text_input(
                    "Student Name",
                    placeholder="Ali Ahmed"
                )

                program = st.text_input(
                    "Program",
                    placeholder="BS Computer Science"
                )

            with col2:

                semester = st.text_input(
                    "Semester",
                    placeholder="1"
                )

                section = st.text_input(
                    "Section",
                    placeholder="A"
                )

            save_student = st.form_submit_button(
                "➕ Save Student",
                type="primary"
            )

        if save_student:

            roll = clean(roll)
            student_name = clean(student_name)

            if not roll or not student_name:

                st.warning(
                    "Roll number and student name are required."
                )

            else:

                existing = one(
                    "SELECT id FROM students WHERE roll_no=?",
                    (roll,)
                )

                if existing:

                    success = execute(
                        """
                        UPDATE students

                        SET
                            name=?,
                            program=?,
                            semester=?,
                            section=?

                        WHERE roll_no=?
                        """,
                        (
                            student_name,
                            program,
                            semester,
                            section,
                            roll
                        )
                    )

                else:

                    success = execute(
                        """
                        INSERT INTO students
                        (
                            roll_no,
                            name,
                            program,
                            semester,
                            section
                        )

                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            roll,
                            student_name,
                            program,
                            semester,
                            section
                        )
                    )

                if success:

                    st.success(
                        "Student saved successfully."
                    )

    # --------------------------------------------------------
    # BULK IMPORT
    # --------------------------------------------------------

    with tab2:

        st.subheader(
            "📥 Import Students in Bulk"
        )

        st.write(
            "Upload the complete student list instead of entering students one by one."
        )

        template = pd.DataFrame(
            {
                "Roll Number": [
                    "CS001",
                    "CS002",
                    "CS003"
                ],

                "Student Name": [
                    "Ali Ahmed",
                    "Sara Khan",
                    "Usman Ali"
                ],

                "Program": [
                    "BSCS",
                    "BSCS",
                    "BSCS"
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
            }
        )

        st.download_button(
            "⬇️ Download Student Template",
            template.to_csv(
                index=False
            ).encode("utf-8"),
            "Fast_Tutor_Student_Template.csv",
            "text/csv"
        )

        uploaded = st.file_uploader(
            "Upload CSV or Excel file",
            type=[
                "csv",
                "xlsx",
                "xls"
            ],
            key="student_upload"
        )

        if uploaded:

            df = read_file(
                uploaded
            )

            if df is not None:

                st.write(
                    f"**{len(df)} rows found**"
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                if st.button(
                    "IMPORT ALL STUDENTS",
                    type="primary",
                    key="import_students"
                ):

                    column_map = {
                        str(column).strip().lower(): column
                        for column in df.columns
                    }

                    roll_col = (
                        column_map.get("roll number")
                        or column_map.get("roll_no")
                        or column_map.get("roll")
                    )

                    name_col = (
                        column_map.get("student name")
                        or column_map.get("name")
                    )

                    program_col = (
                        column_map.get("program")
                    )

                    semester_col = (
                        column_map.get("semester")
                    )

                    section_col = (
                        column_map.get("section")
                    )

                    if not roll_col or not name_col:

                        st.error(
                            "The file must contain "
                            "'Roll Number' and "
                            "'Student Name' columns."
                        )

                    else:

                        imported = 0
                        skipped = 0

                        for _, row in df.iterrows():

                            roll_value = clean(
                                row[roll_col]
                            )

                            name_value = clean(
                                row[name_col]
                            )

                            program_value = (
                                clean(row[program_col])
                                if program_col
                                else ""
                            )

                            semester_value = (
                                clean(row[semester_col])
                                if semester_col
                                else ""
                            )

                            section_value = (
                                clean(row[section_col])
                                if section_col
                                else ""
                            )

                            if (
                                not roll_value
                                or not name_value
                            ):

                                skipped += 1
                                continue

                            existing = one(
                                """
                                SELECT id
                                FROM students
                                WHERE roll_no=?
                                """,
                                (
                                    roll_value,
                                )
                            )

                            if existing:

                                success = execute(
                                    """
                                    UPDATE students

                                    SET
                                        name=?,
                                        program=?,
                                        semester=?,
                                        section=?

                                    WHERE roll_no=?
                                    """,
                                    (
                                        name_value,
                                        program_value,
                                        semester_value,
                                        section_value,
                                        roll_value
                                    )
                                )

                            else:

                                success = execute(
                                    """
                                    INSERT INTO students
                                    (
                                        roll_no,
                                        name,
                                        program,
                                        semester,
                                        section
                                    )

                                    VALUES (?, ?, ?, ?, ?)
                                    """,
                                    (
                                        roll_value,
                                        name_value,
                                        program_value,
                                        semester_value,
                                        section_value
                                    )
                                )

                            if success:

                                imported += 1

                            else:

                                skipped += 1

                        st.success(
                            f"{imported} students imported successfully."
                        )

                        if skipped:

                            st.warning(
                                f"{skipped} rows were skipped."
                            )

    st.divider()

    rows = query(
        """
        SELECT
            roll_no,
            name,
            program,
            semester,
            section

        FROM students

        ORDER BY roll_no
        """
    )

    st.dataframe(
        make_df(
            rows,
            [
                "Roll Number",
                "Student Name",
                "Program",
                "Semester",
                "Section"
            ]
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ASSESSMENTS
# ============================================================

elif page == "📝 Assessments":

    st.title("📝 Assessment Creation")

    courses = query(
        """
        SELECT
            code,
            name

        FROM courses

        ORDER BY code
        """
    )

    if not courses:

        st.warning(
            "Please create a course first."
        )

    else:

        course_options = [
            f"{row[0]} - {row[1]}"
            for row in courses
        ]

        selected_course = st.selectbox(
            "Course",
            course_options
        )

        course_code = selected_course.split(
            " - ",
            1
        )[0]

        with st.form("assessment_form"):

            assessment_name = st.text_input(
                "Assessment Name",
                placeholder="Midterm Examination"
            )

            assessment_type = st.selectbox(
                "Assessment Type",
                [
                    "Quiz",
                    "Assignment",
                    "Midterm Examination",
                    "Final Examination",
                    "Project",
                    "Lab",
                    "Presentation",
                    "Other"
                ]
            )

            col1, col2 = st.columns(2)

            with col1:

                total_marks = st.number_input(
                    "Total Marks",
                    min_value=1.0,
                    value=100.0
                )

            with col2:

                weightage = st.number_input(
                    "Weightage %",
                    min_value=0.0,
                    max_value=100.0,
                    value=20.0
                )

            save_assessment = st.form_submit_button(
                "➕ Create Assessment",
                type="primary"
            )

        if save_assessment:

            if not clean(assessment_name):

                st.warning(
                    "Assessment name is required."
                )

            else:

                success = execute(
                    """
                    INSERT INTO assessments
                    (
                        course_code,
                        name,
                        assessment_type,
                        total_marks,
                        weightage
                    )

                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        course_code,
                        clean(assessment_name),
                        assessment_type,
                        total_marks,
                        weightage
                    )
                )

                if success:

                    st.success(
                        "Assessment created successfully."
                    )

        st.divider()

        rows = query(
            """
            SELECT
                name,
                assessment_type,
                total_marks,
                weightage

            FROM assessments

            WHERE course_code=?

            ORDER BY id DESC
            """,
            (
                course_code,
            )
        )

        st.dataframe(
            make_df(
                rows,
                [
                    "Assessment",
                    "Type",
                    "Total Marks",
                    "Weightage %"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CLO MANAGEMENT
# ============================================================

elif page == "🎯 CLO Management":

    st.title("🎯 CLO Management")

    courses = query(
        """
        SELECT
            code,
            name

        FROM courses

        ORDER BY code
        """
    )

    if not courses:

        st.warning(
            "Please create a course first."
        )

    else:

        course_options = [
            f"{row[0]} - {row[1]}"
            for row in courses
        ]

        selected_course = st.selectbox(
            "Course",
            course_options,
            key="clo_course"
        )

        course_code = selected_course.split(
            " - ",
            1
        )[0]

        with st.form("clo_form"):

            clo_code = st.text_input(
                "CLO",
                placeholder="CLO1"
            )

            description = st.text_area(
                "CLO Description",
                placeholder="Explain fundamental programming concepts."
            )

            bloom = st.selectbox(
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

            save_clo = st.form_submit_button(
                "➕ Save CLO",
                type="primary"
            )

        if save_clo:

            clo_code = clean(
                clo_code
            ).upper()

            if not clo_code:

                st.warning(
                    "Enter a CLO code."
                )

            else:

                existing = one(
                    """
                    SELECT id
                    FROM clos
                    WHERE course_code=?
                    AND clo=?
                    """,
                    (
                        course_code,
                        clo_code
                    )
                )

                if existing:

                    success = execute(
                        """
                        UPDATE clos

                        SET
                            description=?,
                            bloom=?

                        WHERE id=?
                        """,
                        (
                            description,
                            bloom,
                            existing[0]
                        )
                    )

                else:

                    success = execute(
                        """
                        INSERT INTO clos
                        (
                            course_code,
                            clo,
                            description,
                            bloom
                        )

                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            course_code,
                            clo_code,
                            description,
                            bloom
                        )
                    )

                if success:

                    st.success(
                        "CLO saved successfully."
                    )

        rows = query(
            """
            SELECT
                clo,
                description,
                bloom

            FROM clos

            WHERE course_code=?

            ORDER BY clo
            """,
            (
                course_code,
            )
        )

        st.dataframe(
            make_df(
                rows,
                [
                    "CLO",
                    "Description",
                    "Bloom Level"
                ]
            ),
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
            "PLO",
            placeholder="PLO1"
        )

        plo_description = st.text_area(
            "PLO Description",
            placeholder="Knowledge of Computing"
        )

        save_plo = st.form_submit_button(
            "➕ Save PLO",
            type="primary"
        )

    if save_plo:

        plo_code = clean(
            plo_code
        ).upper()

        if not plo_code:

            st.warning(
                "Enter a PLO code."
            )

        else:

            existing = one(
                """
                SELECT id
                FROM plos
                WHERE plo=?
                """,
                (
                    plo_code,
                )
            )

            if existing:

                success = execute(
                    """
                    UPDATE plos

                    SET description=?

                    WHERE plo=?
                    """,
                    (
                        plo_description,
                        plo_code
                    )
                )

            else:

                success = execute(
                    """
                    INSERT INTO plos
                    (
                        plo,
                        description
                    )

                    VALUES (?, ?)
                    """,
                    (
                        plo_code,
                        plo_description
                    )
                )

            if success:

                st.success(
                    "PLO saved successfully."
                )

    st.divider()

    rows = query(
        """
        SELECT
            plo,
            description

        FROM plos

        ORDER BY plo
        """
    )

    st.dataframe(
        make_df(
            rows,
            [
                "PLO",
                "Description"
            ]
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CLO-PLO MAPPING
# ============================================================

elif page == "🔗 CLO-PLO Mapping":

    st.title("🔗 CLO-PLO Mapping")

    st.write(
        "Map each CLO to one or more PLOs."
    )

    courses = query(
        """
        SELECT
            code,
            name

        FROM courses

        ORDER BY code
        """
    )

    plos = query(
        """
        SELECT
            plo

        FROM plos

        ORDER BY plo
        """
    )

    if not courses:

        st.warning(
            "Create courses first."
        )

    elif not plos:

        st.warning(
            "Create PLOs first."
        )

    else:

        course_options = [
            f"{row[0]} - {row[1]}"
            for row in courses
        ]

        selected_course = st.selectbox(
            "Course",
            course_options,
            key="mapping_course"
        )

        course_code = selected_course.split(
            " - ",
            1
        )[0]

        clos = query(
            """
            SELECT
                clo

            FROM clos

            WHERE course_code=?

            ORDER BY clo
            """,
            (
                course_code,
            )
        )

        plo_codes = [
            row[0]
            for row in plos
        ]

        if not clos:

            st.warning(
                "Create CLOs for this course first."
            )

        else:

            st.info(
                "0 = No Mapping | "
                "1 = Low | "
                "2 = Medium | "
                "3 = High"
            )

            for clo_row in clos:

                clo = clo_row[0]

                st.markdown(
                    f"### {clo}"
                )

                columns = st.columns(
                    len(plo_codes)
                )

                for index, plo in enumerate(
                    plo_codes
                ):

                    existing = one(
                        """
                        SELECT
                            strength

                        FROM mappings

                        WHERE
                            course_code=?
                            AND clo=?
                            AND plo=?
                        """,
                        (
                            course_code,
                            clo,
                            plo
                        )
                    )

                    current = (
                        int(existing[0])
                        if existing
                        else 0
                    )

                    value = columns[index].selectbox(
                        plo,
                        [
                            0,
                            1,
                            2,
                            3
                        ],
                        index=current,
                        key=(
                            f"mapping_"
                            f"{course_code}_"
                            f"{clo}_"
                            f"{plo}"
                        )
                    )

                    mapping_id = one(
                        """
                        SELECT
                            id

                        FROM mappings

                        WHERE
                            course_code=?
                            AND clo=?
                            AND plo=?
                        """,
                        (
                            course_code,
                            clo,
                            plo
                        )
                    )

                    if mapping_id:

                        execute(
                            """
                            UPDATE mappings

                            SET strength=?

                            WHERE id=?
                            """,
                            (
                                value,
                                mapping_id[0]
                            )
                        )

                    else:

                        execute(
                            """
                            INSERT INTO mappings
                            (
                                course_code,
                                clo,
                                plo,
                                strength
                            )

                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                course_code,
                                clo,
                                plo,
                                value
                            )
                        )

            st.success(
                "CLO-PLO mapping is saved."
            )

            # Matrix

            st.subheader(
                "Mapping Matrix"
            )

            matrix_rows = []

            for clo_row in clos:

                clo = clo_row[0]

                row_data = {
                    "CLO": clo
                }

                for plo in plo_codes:

                    mapping = one(
                        """
                        SELECT
                            strength

                        FROM mappings

                        WHERE
                            course_code=?
                            AND clo=?
                            AND plo=?
                        """,
                        (
                            course_code,
                            clo,
                            plo
                        )
                    )

                    row_data[plo] = (
                        mapping[0]
                        if mapping
                        else 0
                    )

                matrix_rows.append(
                    row_data
                )

            matrix_df = pd.DataFrame(
                matrix_rows
            )

            st.dataframe(
                matrix_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# BULK MARKS
# ============================================================

elif page == "📥 Bulk Marks":

    st.title("📥 Bulk Marks Upload")

    st.success(
        "Upload the complete class marks file. "
        "You do not need to enter marks one student at a time."
    )

    st.subheader(
        "Required File Format"
    )

    template = pd.DataFrame(
        {
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

            "CLO": [
                "CLO1",
                "CLO1",
                "CLO1"
            ],

            "Obtained Marks": [
                82,
                75,
                91
            ],

            "Total Marks": [
                100,
                100,
                100
            ]
        }
    )

    st.dataframe(
        template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Marks Template",
        template.to_csv(
            index=False
        ).encode("utf-8"),
        "Fast_Tutor_Marks_Template.csv",
        "text/csv"
    )

    uploaded_marks = st.file_uploader(
        "Upload CSV or Excel marks file",
        type=[
            "csv",
            "xlsx",
            "xls"
        ],
        key="marks_upload"
    )

    if uploaded_marks:

        marks_df = read_file(
            uploaded_marks
        )

        if marks_df is not None:

            st.write(
                f"**{len(marks_df)} mark records found.**"
            )

            st.dataframe(
                marks_df,
                use_container_width=True,
                hide_index=True
            )

            if st.button(
                "🚀 IMPORT ALL MARKS",
                type="primary"
            ):

                columns = {
                    str(column).strip().lower(): column
                    for column in marks_df.columns
                }

                roll_col = (
                    columns.get("roll number")
                    or columns.get("roll_no")
                    or columns.get("roll")
                )

                course_col = (
                    columns.get("course code")
                    or columns.get("course_code")
                    or columns.get("course")
                )

                assessment_col = (
                    columns.get("assessment")
                    or columns.get("assessment name")
                )

                clo_col = (
                    columns.get("clo")
                    or columns.get("clo code")
                )

                obtained_col = (
                    columns.get("obtained marks")
                    or columns.get("obtained")
                    or columns.get("marks")
                )

                total_col = (
                    columns.get("total marks")
                    or columns.get("total")
                )

                if (
                    not roll_col
                    or not course_col
                    or not assessment_col
                    or not obtained_col
                    or not total_col
                ):

                    st.error(
                        "Required columns are: "
                        "Roll Number, Course Code, "
                        "Assessment, Obtained Marks "
                        "and Total Marks."
                    )

                else:

                    imported = 0
                    skipped = 0

                    progress = st.progress(
                        0
                    )

                    total_rows = len(
                        marks_df
                    )

                    for index, row in marks_df.iterrows():

                        roll_value = clean(
                            row[roll_col]
                        )

                        course_value = clean(
                            row[course_col]
                        ).upper()

                        assessment_value = clean(
                            row[assessment_col]
                        )

                        obtained_value = number(
                            row[obtained_col]
                        )

                        total_value = number(
                            row[total_col]
                        )

                        clo_value = ""

                        if clo_col:

                            clo_value = clean(
                                row[clo_col]
                            ).upper()

                        # Validate

                        if (
                            not roll_value
                            or not course_value
                            or not assessment_value
                            or total_value <= 0
                            or obtained_value < 0
                            or obtained_value > total_value
                        ):

                            skipped += 1

                            progress.progress(
                                int(
                                    ((index + 1) /
                                     total_rows) * 100
                                )
                            )

                            continue

                        # Check student

                        student = one(
                            """
                            SELECT
                                id

                            FROM students

                            WHERE roll_no=?
                            """,
                            (
                                roll_value,
                            )
                        )

                        if not student:

                            skipped += 1

                            progress.progress(
                                int(
                                    ((index + 1) /
                                     total_rows) * 100
                                )
                            )

                            continue

                        mark_percentage = percentage(
                            obtained_value,
                            total_value
                        )

                        mark_grade = grade(
                            mark_percentage
                        )

                        # Delete duplicate record

                        execute(
                            """
                            DELETE FROM results

                            WHERE
                                roll_no=?
                                AND course_code=?
                                AND assessment=?
                                AND clo=?
                            """,
                            (
                                roll_value,
                                course_value,
                                assessment_value,
                                clo_value
                            )
                        )

                        # Insert new result

                        success = execute(
                            """
                            INSERT INTO results
                            (
                                roll_no,
                                course_code,
                                assessment,
                                clo,
                                obtained,
                                total,
                                percentage,
                                grade
                            )

                            VALUES
                            (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                roll_value,
                                course_value,
                                assessment_value,
                                clo_value,
                                obtained_value,
                                total_value,
                                mark_percentage,
                                mark_grade
                            )
                        )

                        if success:

                            imported += 1

                        else:

                            skipped += 1

                        progress.progress(
                            int(
                                ((index + 1) /
                                 total_rows) * 100
                            )
                        )

                    st.success(
                        f"{imported} marks imported successfully."
                    )

                    if skipped:

                        st.warning(
                            f"{skipped} rows were skipped."
                        )


# ============================================================
# STUDENT PERFORMANCE
# ============================================================

elif page == "👤 Student Performance":

    st.title("👤 Individual Student Performance")

    students = query(
        """
        SELECT
            roll_no,
            name

        FROM students

        ORDER BY roll_no
        """
    )

    if not students:

        st.info(
            "Import students first."
        )

    else:

        student_options = [
            f"{row[0]} - {row[1]}"
            for row in students
        ]

        selected_student = st.selectbox(
            "Select Student",
            student_options
        )

        roll_no = selected_student.split(
            " - ",
            1
        )[0]

        student = one(
            """
            SELECT
                name,
                program,
                semester,
                section

            FROM students

            WHERE roll_no=?
            """,
            (
                roll_no,
            )
        )

        if student:

            st.subheader(
                f"🎓 {student[0]}"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Roll Number",
                roll_no
            )

            col2.metric(
                "Program",
                student[1] or "-"
            )

            col3.metric(
                "Semester",
                student[2] or "-"
            )

            col4.metric(
                "Section",
                student[3] or "-"
            )

            results = query(
                """
                SELECT
                    course_code,
                    assessment,
                    clo,
                    obtained,
                    total,
                    percentage,
                    grade

                FROM results

                WHERE roll_no=?

                ORDER BY course_code
                """,
                (
                    roll_no,
                )
            )

            if not results:

                st.info(
                    "No marks are available for this student."
                )

            else:

                performance_df = make_df(
                    results,
                    [
                        "Course",
                        "Assessment",
                        "CLO",
                        "Obtained",
                        "Total",
                        "Percentage",
                        "Grade"
                    ]
                )

                performance_df["Percentage"] = pd.to_numeric(
                    performance_df["Percentage"],
                    errors="coerce"
                )

                overall = performance_df[
                    "Percentage"
                ].mean()

                highest = performance_df[
                    "Percentage"
                ].max()

                lowest = performance_df[
                    "Percentage"
                ].min()

                a, b, c = st.columns(3)

                a.metric(
                    "Overall Performance",
                    f"{overall:.2f}%"
                )

                b.metric(
                    "Highest",
                    f"{highest:.2f}%"
                )

                c.metric(
                    "Lowest",
                    f"{lowest:.2f}%"
                )

                st.subheader(
                    "📈 Course Performance"
                )

                course_chart = (
                    performance_df
                    .groupby("Course")["Percentage"]
                    .mean()
                )

                st.bar_chart(
                    course_chart
                )

                # CLO

                clo_performance = performance_df[
                    performance_df["CLO"]
                    .astype(str)
                    .str.strip()
                    != ""
                ]

                if not clo_performance.empty:

                    st.subheader(
                        "🎯 CLO Performance"
                    )

                    clo_chart = (
                        clo_performance
                        .groupby("CLO")["Percentage"]
                        .mean()
                    )

                    st.bar_chart(
                        clo_chart
                    )

                st.subheader(
                    "📋 Detailed Performance"
                )

                st.dataframe(
                    performance_df,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# ATTAINMENT
# ============================================================

elif page == "📊 Attainment":

    st.title("📊 CLO & PLO Attainment")

    clo_tab, plo_tab = st.tabs(
        [
            "🎯 CLO Attainment",
            "🏆 PLO Attainment"
        ]
    )

    # ========================================================
    # CLO ATTAINMENT
    # ========================================================

    with clo_tab:

        st.subheader(
            "CLO Attainment"
        )

        clo_rows = query(
            """
            SELECT
                clo,
                AVG(percentage)

            FROM results

            WHERE clo != ''

            GROUP BY clo

            ORDER BY clo
            """
        )

        if clo_rows:

            clo_df = make_df(
                clo_rows,
                [
                    "CLO",
                    "Attainment"
                ]
            )

            clo_df["Attainment"] = pd.to_numeric(
                clo_df["Attainment"],
                errors="coerce"
            ).round(2)

            st.bar_chart(
                clo_df.set_index("CLO")
            )

            st.dataframe(
                clo_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No CLO attainment data is available yet."
            )

    # ========================================================
    # PLO ATTAINMENT
    # ========================================================

    with plo_tab:

        st.subheader(
            "PLO Attainment"
        )

        mapping_rows = query(
            """
            SELECT
                course_code,
                clo,
                plo,
                strength

            FROM mappings

            WHERE strength > 0
            """
        )

        result_rows = query(
            """
            SELECT
                course_code,
                clo,
                percentage

            FROM results

            WHERE clo != ''
            """
        )

        if not mapping_rows:

            st.info(
                "Create CLO-PLO mappings first."
            )

        elif not result_rows:

            st.info(
                "Upload student marks first."
            )

        else:

            mapping_df = make_df(
                mapping_rows,
                [
                    "Course",
                    "CLO",
                    "PLO",
                    "Strength"
                ]
            )

            result_df = make_df(
                result_rows,
                [
                    "Course",
                    "CLO",
                    "Percentage"
                ]
            )

            combined = result_df.merge(
                mapping_df,
                on=[
                    "Course",
                    "CLO"
                ]
            )

            if combined.empty:

                st.info(
                    "There is no matching attainment data."
                )

            else:

                combined["Percentage"] = pd.to_numeric(
                    combined["Percentage"],
                    errors="coerce"
                )

                combined["Strength"] = pd.to_numeric(
                    combined["Strength"],
                    errors="coerce"
                )

                combined["Weighted"] = (
                    combined["Percentage"]
                    *
                    combined["Strength"]
                )

                result = combined.groupby(
                    "PLO"
                ).agg(
                    Weighted=(
                        "Weighted",
                        "sum"
                    ),

                    Strength=(
                        "Strength",
                        "sum"
                    )
                )

                result["Attainment"] = (
                    result["Weighted"]
                    /
                    result["Strength"]
                )

                result["Attainment"] = (
                    result["Attainment"]
                    .round(2)
                )

                st.bar_chart(
                    result[
                        ["Attainment"]
                    ]
                )

                st.dataframe(
                    result[
                        ["Attainment"]
                    ].reset_index(),
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# REPORTS
# ============================================================

elif page == "📑 Reports":

    st.title("📑 Reports")

    st.write(
        "Export your Fast Tutor data into one Excel workbook."
    )

    courses_df = make_df(
        query(
            """
            SELECT
                code,
                name,
                credit_hours,
                semester

            FROM courses
            """
        ),
        [
            "Course Code",
            "Course Name",
            "Credit Hours",
            "Semester"
        ]
    )

    students_df = make_df(
        query(
            """
            SELECT
                roll_no,
                name,
                program,
                semester,
                section

            FROM students
            """
        ),
        [
            "Roll Number",
            "Student Name",
            "Program",
            "Semester",
            "Section"
        ]
    )

    assessments_df = make_df(
        query(
            """
            SELECT
                course_code,
                name,
                assessment_type,
                total_marks,
                weightage

            FROM assessments
            """
        ),
        [
            "Course",
            "Assessment",
            "Type",
            "Total Marks",
            "Weightage"
        ]
    )

    clos_df = make_df(
        query(
            """
            SELECT
                course_code,
                clo,
                description,
                bloom

            FROM clos
            """
        ),
        [
            "Course",
            "CLO",
            "Description",
            "Bloom Level"
        ]
    )

    plos_df = make_df(
        query(
            """
            SELECT
                plo,
                description

            FROM plos
            """
        ),
        [
            "PLO",
            "Description"
        ]
    )

    mappings_df = make_df(
        query(
            """
            SELECT
                course_code,
                clo,
                plo,
                strength

            FROM mappings
            """
        ),
        [
            "Course",
            "CLO",
            "PLO",
            "Strength"
        ]
    )

    results_df = make_df(
        query(
            """
            SELECT
                roll_no,
                course_code,
                assessment,
                clo,
                obtained,
                total,
                percentage,
                grade

            FROM results
            """
        ),
        [
            "Roll Number",
            "Course",
            "Assessment",
            "CLO",
            "Obtained",
            "Total",
            "Percentage",
            "Grade"
        ]
    )

    output = BytesIO()

    try:

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            courses_df.to_excel(
                writer,
                sheet_name="Courses",
                index=False
            )

            students_df.to_excel(
                writer,
                sheet_name="Students",
                index=False
            )

            assessments_df.to_excel(
                writer,
                sheet_name="Assessments",
                index=False
            )

            clos_df.to_excel(
                writer,
                sheet_name="CLOs",
                index=False
            )

            plos_df.to_excel(
                writer,
                sheet_name="PLOs",
                index=False
            )

            mappings_df.to_excel(
                writer,
                sheet_name="CLO-PLO Mapping",
                index=False
            )

            results_df.to_excel(
                writer,
                sheet_name="Results",
                index=False
            )

        st.success(
            "Excel report is ready."
        )

        st.download_button(
            "⬇️ DOWNLOAD EXCEL REPORT",
            output.getvalue(),
            "Fast_Tutor_Report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    except Exception as error:

        st.error(
            f"Could not create Excel report: {error}"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#98A2B3;
        font-size:12px;
        padding:10px;
    ">
        🎓 <b>Fast Tutor</b> • Student Performance System
    </div>
    """,
    unsafe_allow_html=True
)
