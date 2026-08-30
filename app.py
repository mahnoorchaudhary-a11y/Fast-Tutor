import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from io import BytesIO


# ============================================================
# FAST TUTOR
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

DB_FILE = Path("fast_tutor.db")


@st.cache_resource
def get_database():
    return sqlite3.connect(
        str(DB_FILE),
        check_same_thread=False
    )


conn = get_database()


def execute(query, params=()):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Database error: {e}")
        return False


def fetch_all(query, params=()):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        if rows is None:
            return []

        return list(rows)

    except Exception as e:
        st.error(f"Database error: {e}")
        return []


def fetch_one(query, params=()):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    except Exception as e:
        st.error(f"Database error: {e}")
        return None


# ============================================================
# DATABASE TABLES
# ============================================================

execute("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    credit_hours REAL DEFAULT 3,
    semester TEXT DEFAULT ''
)
""")


execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    program TEXT DEFAULT '',
    semester TEXT DEFAULT '',
    section TEXT DEFAULT ''
)
""")


execute("""
CREATE TABLE IF NOT EXISTS clos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    clo TEXT NOT NULL,
    description TEXT DEFAULT '',
    bloom TEXT DEFAULT '',
    UNIQUE(course_code, clo)
)
""")


execute("""
CREATE TABLE IF NOT EXISTS plos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plo TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT ''
)
""")


execute("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    name TEXT NOT NULL,
    assessment_type TEXT DEFAULT '',
    total_marks REAL DEFAULT 100,
    weightage REAL DEFAULT 0
)
""")


execute("""
CREATE TABLE IF NOT EXISTS mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    clo TEXT NOT NULL,
    plo TEXT NOT NULL,
    strength INTEGER DEFAULT 0,
    UNIQUE(course_code, clo, plo)
)
""")


execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL,
    course_code TEXT NOT NULL,
    assessment TEXT NOT NULL,
    clo TEXT DEFAULT '',
    obtained REAL DEFAULT 0,
    total REAL DEFAULT 100,
    percentage REAL DEFAULT 0,
    grade TEXT DEFAULT '',
    UNIQUE(roll_no, course_code, assessment, clo)
)
""")


# ============================================================
# HELPERS
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
        return 0.0

    return round((obtained / total) * 100, 2)


def grade(percent):
    if percent >= 90:
        return "A+"
    elif percent >= 80:
        return "A"
    elif percent >= 70:
        return "B"
    elif percent >= 60:
        return "C"
    elif percent >= 50:
        return "D"
    return "F"


def dataframe(rows, columns):
    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(
        [list(row) for row in rows],
        columns=columns
    )


def read_file(uploaded):
    if uploaded is None:
        return None

    try:
        if uploaded.name.lower().endswith(".csv"):
            return pd.read_csv(uploaded)

        return pd.read_excel(uploaded)

    except Exception as e:
        st.error(f"Unable to read file: {e}")
        return None


def find_column(df, names):
    lookup = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

.fast-logo {
    text-align: center;
    padding: 12px 5px 25px 5px;
}

.fast-logo-title {
    color: #0795D1;
    font-size: 29px;
    font-weight: 900;
    letter-spacing: 2px;
}

.fast-logo-subtitle {
    color: #777;
    font-size: 12px;
    margin-top: 3px;
}

.hero {
    padding: 32px;
    border-radius: 22px;
    background: linear-gradient(
        135deg,
        #E8F7FF 0%,
        #FFFFFF 100%
    );
    border: 1px solid #D7EEF8;
    margin-bottom: 25px;
}

.hero-title {
    color: #172B4D;
    font-size: 34px;
    font-weight: 900;
}

.hero-text {
    color: #667085;
    font-size: 16px;
    line-height: 1.7;
    margin-top: 10px;
}

.section-title {
    color: #172B4D;
    font-weight: 800;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("""
<div class="fast-logo">

    <div class="fast-logo-title">
        FAST TUTOR
    </div>

    <div class="fast-logo-subtitle">
        Student Performance System
    </div>

</div>
""", unsafe_allow_html=True)


page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📚 Courses",
        "👨‍🎓 Students",
        "📝 Assessments",
        "🎯 CLO Management",
        "🏆 PLO Management",
        "🔗 CLO-PLO Mapping",
        "📥 Bulk Marks Upload",
        "📊 Student Performance",
        "🎯 Attainment Tracker",
        "📤 Reports"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown("""
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
            margin-top:20px;
            display:flex;
            gap:10px;
            flex-wrap:wrap;
        ">

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">📚 Courses</span>

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">👨‍🎓 Students</span>

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">📝 Assessments</span>

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">📥 Bulk Marks</span>

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">📊 Performance</span>

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">🎯 CLO Attainment</span>

            <span style="
                background:#E8F7FF;
                color:#0795D1;
                padding:8px 15px;
                border-radius:20px;
                font-weight:700;
            ">🏆 PLO Attainment</span>

        </div>

    </div>
    """, unsafe_allow_html=True)

    courses = fetch_one(
        "SELECT COUNT(*) FROM courses"
    )[0]

    students = fetch_one(
        "SELECT COUNT(*) FROM students"
    )[0]

    clos = fetch_one(
        "SELECT COUNT(*) FROM clos"
    )[0]

    plos = fetch_one(
        "SELECT COUNT(*) FROM plos"
    )[0]

    assessments = fetch_one(
        "SELECT COUNT(*) FROM assessments"
    )[0]

    marks = fetch_one(
        "SELECT COUNT(*) FROM results"
    )[0]

    c1, c2, c3 = st.columns(3)

    c1.metric("📚 Courses", courses)
    c2.metric("👨‍🎓 Students", students)
    c3.metric("🎯 CLOs", clos)

    c4, c5, c6 = st.columns(3)

    c4.metric("🏆 PLOs", plos)
    c5.metric("📝 Assessments", assessments)
    c6.metric("📊 Mark Records", marks)

    st.divider()

    rows = fetch_all("""
        SELECT
            course_code,
            AVG(percentage)
        FROM results
        GROUP BY course_code
        ORDER BY course_code
    """)

    if rows:

        chart_df = dataframe(
            rows,
            [
                "Course",
                "Average Performance"
            ]
        )

        chart_df = chart_df.set_index("Course")

        st.subheader("📈 Course Performance")

        st.bar_chart(chart_df)

    else:

        st.info(
            "Upload student marks to see performance charts."
        )


# ============================================================
# COURSES
# ============================================================

elif page == "📚 Courses":

    st.title("📚 Course Management")

    st.write(
        "Create your courses before enrolling students."
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
                min_value=0.5,
                max_value=10.0,
                value=3.0,
                step=0.5
            )

            semester = st.text_input(
                "Semester",
                placeholder="1"
            )

        save = st.form_submit_button(
            "Save Course",
            type="primary"
        )

    if save:

        code = clean(code).upper()
        name = clean(name)

        if not code or not name:

            st.error(
                "Course Code and Course Name are required."
            )

        else:

            ok = execute("""
                INSERT INTO courses
                (
                    code,
                    name,
                    credit_hours,
                    semester
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(code)
                DO UPDATE SET
                    name = excluded.name,
                    credit_hours = excluded.credit_hours,
                    semester = excluded.semester
            """, (
                code,
                name,
                credit_hours,
                clean(semester)
            ))

            if ok:
                st.success("Course saved successfully.")

    st.divider()

    rows = fetch_all("""
        SELECT
            code,
            name,
            credit_hours,
            semester
        FROM courses
        ORDER BY code
    """)

    df = dataframe(
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
            "➕ Add Student",
            "📥 Bulk Student Import"
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
                    placeholder="CS-001"
                )

                student_name = st.text_input(
                    "Student Name",
                    placeholder="Muhammad Ali"
                )

                program = st.text_input(
                    "Program",
                    placeholder="BS Computer Science"
                )

            with col2:

                semester = st.text_input(
                    "Semester",
                    placeholder="3"
                )

                section = st.text_input(
                    "Section",
                    placeholder="A"
                )

            save = st.form_submit_button(
                "Save Student",
                type="primary"
            )

        if save:

            roll = clean(roll)
            student_name = clean(student_name)

            if not roll or not student_name:

                st.error(
                    "Roll Number and Student Name are required."
                )

            else:

                ok = execute("""
                    INSERT INTO students
                    (
                        roll_no,
                        name,
                        program,
                        semester,
                        section
                    )
                    VALUES (?, ?, ?, ?, ?)

                    ON CONFLICT(roll_no)
                    DO UPDATE SET
                        name = excluded.name,
                        program = excluded.program,
                        semester = excluded.semester,
                        section = excluded.section
                """, (
                    roll,
                    student_name,
                    clean(program),
                    clean(semester),
                    clean(section)
                ))

                if ok:
                    st.success(
                        "Student saved successfully."
                    )

    # --------------------------------------------------------
    # BULK STUDENT IMPORT
    # --------------------------------------------------------

    with tab2:

        st.subheader(
            "📥 Import Complete Student List"
        )

        st.write(
            "Upload CSV or Excel containing the complete class."
        )

        template = pd.DataFrame({
            "Roll Number": [
                "CS-001",
                "CS-002",
                "CS-003"
            ],
            "Student Name": [
                "Ali Ahmed",
                "Sara Khan",
                "Ahmed Raza"
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

        st.dataframe(
            template,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Student Template",
            template.to_csv(index=False).encode("utf-8"),
            "Fast_Tutor_Student_Template.csv",
            "text/csv"
        )

        uploaded = st.file_uploader(
            "Upload Student File",
            type=[
                "csv",
                "xlsx",
                "xls"
            ],
            key="student_upload"
        )

        if uploaded:

            df = read_file(uploaded)

            if df is not None:

                df.columns = [
                    str(c).strip()
                    for c in df.columns
                ]

                st.write(
                    f"**{len(df)} students found**"
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                roll_col = find_column(
                    df,
                    [
                        "roll number",
                        "roll_no",
                        "rollno",
                        "roll",
                        "registration number",
                        "registration no"
                    ]
                )

                name_col = find_column(
                    df,
                    [
                        "student name",
                        "name",
                        "student"
                    ]
                )

                program_col = find_column(
                    df,
                    [
                        "program",
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
                        "sec"
                    ]
                )

                if roll_col is None or name_col is None:

                    st.error(
                        "The file must contain Roll Number "
                        "and Student Name columns."
                    )

                else:

                    if st.button(
                        "🚀 IMPORT ALL STUDENTS",
                        type="primary"
                    ):

                        imported = 0
                        skipped = 0

                        for _, row in df.iterrows():

                            roll_value = clean(
                                row[roll_col]
                            )

                            name_value = clean(
                                row[name_col]
                            )

                            if (
                                not roll_value
                                or not name_value
                            ):
                                skipped += 1
                                continue

                            program_value = ""

                            if program_col:
                                program_value = clean(
                                    row[program_col]
                                )

                            semester_value = ""

                            if semester_col:
                                semester_value = clean(
                                    row[semester_col]
                                )

                            section_value = ""

                            if section_col:
                                section_value = clean(
                                    row[section_col]
                                )

                            ok = execute("""
                                INSERT INTO students
                                (
                                    roll_no,
                                    name,
                                    program,
                                    semester,
                                    section
                                )
                                VALUES (?, ?, ?, ?, ?)

                                ON CONFLICT(roll_no)
                                DO UPDATE SET
                                    name = excluded.name,
                                    program = excluded.program,
                                    semester = excluded.semester,
                                    section = excluded.section
                            """, (
                                roll_value,
                                name_value,
                                program_value,
                                semester_value,
                                section_value
                            ))

                            if ok:
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

    rows = fetch_all("""
        SELECT
            roll_no,
            name,
            program,
            semester,
            section
        FROM students
        ORDER BY roll_no
    """)

    df = dataframe(
        rows,
        [
            "Roll Number",
            "Student Name",
            "Program",
            "Semester",
            "Section"
        ]
    )

    st.subheader("Current Students")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ASSESSMENTS
# ============================================================

elif page == "📝 Assessments":

    st.title("📝 Assessment Creation")

    courses = fetch_all("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    if not courses:

        st.warning(
            "Please create a course first."
        )

    else:

        course_options = {
            f"{code} — {name}": code
            for code, name in courses
        }

        selected_course = st.selectbox(
            "Course",
            list(course_options.keys())
        )

        course_code = course_options[
            selected_course
        ]

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
                    "Class Test",
                    "Midterm",
                    "Final",
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
                    "Weightage (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=20.0
                )

            save = st.form_submit_button(
                "Create Assessment",
                type="primary"
            )

        if save:

            if not clean(assessment_name):

                st.error(
                    "Assessment name is required."
                )

            else:

                ok = execute("""
                    INSERT INTO assessments
                    (
                        course_code,
                        name,
                        assessment_type,
                        total_marks,
                        weightage
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    course_code,
                    clean(assessment_name),
                    assessment_type,
                    total_marks,
                    weightage
                ))

                if ok:
                    st.success(
                        "Assessment created successfully."
                    )

        st.divider()

        rows = fetch_all("""
            SELECT
                name,
                assessment_type,
                total_marks,
                weightage
            FROM assessments
            WHERE course_code = ?
            ORDER BY id DESC
        """, (
            course_code,
        ))

        df = dataframe(
            rows,
            [
                "Assessment",
                "Type",
                "Total Marks",
                "Weightage %"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CLO MANAGEMENT
# ============================================================

elif page == "🎯 CLO Management":

    st.title("🎯 CLO Management")

    courses = fetch_all("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    if not courses:

        st.warning(
            "Create courses first."
        )

    else:

        course_options = {
            f"{code} — {name}": code
            for code, name in courses
        }

        selected = st.selectbox(
            "Course",
            list(course_options.keys())
        )

        course_code = course_options[selected]

        with st.form("clo_form"):

            clo = st.text_input(
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

            save = st.form_submit_button(
                "Save CLO",
                type="primary"
            )

        if save:

            clo = clean(clo).upper()

            if not clo:

                st.error(
                    "CLO is required."
                )

            else:

                ok = execute("""
                    INSERT INTO clos
                    (
                        course_code,
                        clo,
                        description,
                        bloom
                    )
                    VALUES (?, ?, ?, ?)

                    ON CONFLICT(course_code, clo)
                    DO UPDATE SET
                        description = excluded.description,
                        bloom = excluded.bloom
                """, (
                    course_code,
                    clo,
                    clean(description),
                    bloom
                ))

                if ok:
                    st.success(
                        "CLO saved successfully."
                    )

        st.divider()

        rows = fetch_all("""
            SELECT
                clo,
                description,
                bloom
            FROM clos
            WHERE course_code = ?
            ORDER BY clo
        """, (
            course_code,
        ))

        df = dataframe(
            rows,
            [
                "CLO",
                "Description",
                "Bloom Level"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PLO MANAGEMENT
# ============================================================

elif page == "🏆 PLO Management":

    st.title("🏆 PLO Management")

    with st.form("plo_form"):

        plo = st.text_input(
            "PLO",
            placeholder="PLO1"
        )

        description = st.text_area(
            "PLO Description",
            placeholder="Knowledge of Computing"
        )

        save = st.form_submit_button(
            "Save PLO",
            type="primary"
        )

    if save:

        plo = clean(plo).upper()

        if not plo:

            st.error(
                "PLO is required."
            )

        else:

            ok = execute("""
                INSERT INTO plos
                (
                    plo,
                    description
                )
                VALUES (?, ?)

                ON CONFLICT(plo)
                DO UPDATE SET
                    description = excluded.description
            """, (
                plo,
                clean(description)
            ))

            if ok:
                st.success(
                    "PLO saved successfully."
                )

    st.divider()

    rows = fetch_all("""
        SELECT
            plo,
            description
        FROM plos
        ORDER BY plo
    """)

    df = dataframe(
        rows,
        [
            "PLO",
            "Description"
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# CLO-PLO MAPPING
# ============================================================

elif page == "🔗 CLO-PLO Mapping":

    st.title("🔗 CLO-PLO Mapping")

    courses = fetch_all("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    plos = fetch_all("""
        SELECT plo
        FROM plos
        ORDER BY plo
    """)

    if not courses:

        st.warning(
            "Create courses first."
        )

    elif not plos:

        st.warning(
            "Create PLOs first."
        )

    else:

        course_options = {
            f"{code} — {name}": code
            for code, name in courses
        }

        selected = st.selectbox(
            "Course",
            list(course_options.keys())
        )

        course_code = course_options[selected]

        clo_rows = fetch_all("""
            SELECT clo
            FROM clos
            WHERE course_code = ?
            ORDER BY clo
        """, (
            course_code,
        ))

        if not clo_rows:

            st.warning(
                "Create CLOs for this course first."
            )

        else:

            plo_list = [
                row[0]
                for row in plos
            ]

            st.write(
                "**Mapping strength:** "
                "0 = None | 1 = Low | "
                "2 = Medium | 3 = High"
            )

            header = st.columns(
                len(plo_list) + 1
            )

            header[0].markdown(
                "**CLO**"
            )

            for i, plo in enumerate(plo_list):
                header[i + 1].markdown(
                    f"**{plo}**"
                )

            for clo_row in clo_rows:

                clo = clo_row[0]

                current = fetch_all("""
                    SELECT plo, strength
                    FROM mappings
                    WHERE course_code = ?
                    AND clo = ?
                """, (
                    course_code,
                    clo
                ))

                current_dict = {
                    row[0]: row[1]
                    for row in current
                }

                columns = st.columns(
                    len(plo_list) + 1
                )

                columns[0].markdown(
                    f"**{clo}**"
                )

                for i, plo in enumerate(
                    plo_list
                ):

                    default_value = int(
                        current_dict.get(
                            plo,
                            0
                        )
                    )

                    value = columns[
                        i + 1
                    ].selectbox(
                        plo,
                        [0, 1, 2, 3],
                        index=default_value,
                        key=f"map_{course_code}_{clo}_{plo}"
                    )

                    execute("""
                        INSERT INTO mappings
                        (
                            course_code,
                            clo,
                            plo,
                            strength
                        )
                        VALUES (?, ?, ?, ?)

                        ON CONFLICT(
                            course_code,
                            clo,
                            plo
                        )
                        DO UPDATE SET
                            strength = excluded.strength
                    """, (
                        course_code,
                        clo,
                        plo,
                        value
                    ))

            st.success(
                "Mappings are saved automatically."
            )


# ============================================================
# BULK MARKS UPLOAD
# ============================================================

elif page == "📥 Bulk Marks Upload":

    st.title("📥 Bulk Marks Upload")

    st.markdown("""
    <div class="hero">

        <div class="hero-title">
            🚀 Upload Complete Class Results
        </div>

        <div class="hero-text">
            Upload one CSV or Excel file containing
            marks for the entire class. You do not need
            to enter student marks one by one.
        </div>

    </div>
    """, unsafe_allow_html=True)

    st.subheader("Required File Format")

    template = pd.DataFrame({
        "Roll Number": [
            "CS-001",
            "CS-002",
            "CS-003"
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
            68
        ],
        "Total Marks": [
            100,
            100,
            100
        ]
    })

    st.dataframe(
        template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Marks Template",
        template.to_csv(index=False).encode("utf-8"),
        "Fast_Tutor_Marks_Template.csv",
        "text/csv"
    )

    uploaded = st.file_uploader(
        "Upload Complete Marks File",
        type=[
            "csv",
            "xlsx",
            "xls"
        ],
        key="marks_upload"
    )

    if uploaded:

        df = read_file(uploaded)

        if df is not None:

            df.columns = [
                str(c).strip()
                for c in df.columns
            ]

            st.success(
                f"{len(df)} result rows detected."
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            roll_col = find_column(
                df,
                [
                    "roll number",
                    "roll_no",
                    "rollno",
                    "roll",
                    "registration number",
                    "registration no"
                ]
            )

            course_col = find_column(
                df,
                [
                    "course code",
                    "course_code",
                    "course"
                ]
            )

            assessment_col = find_column(
                df,
                [
                    "assessment",
                    "assessment name",
                    "assessment_name"
                ]
            )

            obtained_col = find_column(
                df,
                [
                    "obtained marks",
                    "obtained",
                    "marks obtained",
                    "marks"
                ]
            )

            total_col = find_column(
                df,
                [
                    "total marks",
                    "total",
                    "maximum marks",
                    "max marks"
                ]
            )

            clo_col = find_column(
                df,
                [
                    "clo",
                    "clo code"
                ]
            )

            missing = []

            if roll_col is None:
                missing.append("Roll Number")

            if course_col is None:
                missing.append("Course Code")

            if assessment_col is None:
                missing.append("Assessment")

            if obtained_col is None:
                missing.append("Obtained Marks")

            if total_col is None:
                missing.append("Total Marks")

            if missing:

                st.error(
                    "Missing required columns: "
                    + ", ".join(missing)
                )

            else:

                st.info(
                    "Rows without a matching enrolled student "
                    "will be skipped."
                )

                if st.button(
                    "🚀 IMPORT ALL MARKS",
                    type="primary"
                ):

                    imported = 0
                    skipped = 0
                    errors = []

                    for index, row in df.iterrows():

                        try:

                            roll = clean(
                                row[roll_col]
                            )

                            course = clean(
                                row[course_col]
                            ).upper()

                            assessment = clean(
                                row[assessment_col]
                            )

                            obtained = number(
                                row[obtained_col]
                            )

                            total = number(
                                row[total_col]
                            )

                            clo = ""

                            if clo_col is not None:
                                clo = clean(
                                    row[clo_col]
                                ).upper()

                            if (
                                not roll
                                or not course
                                or not assessment
                                or total <= 0
                            ):

                                skipped += 1

                                errors.append(
                                    f"Row {index + 2}: invalid data"
                                )

                                continue

                            student = fetch_one("""
                                SELECT id
                                FROM students
                                WHERE roll_no = ?
                            """, (
                                roll,
                            ))

                            if student is None:

                                skipped += 1

                                errors.append(
                                    f"Row {index + 2}: "
                                    f"student {roll} not found"
                                )

                                continue

                            percent = percentage(
                                obtained,
                                total
                            )

                            letter = grade(
                                percent
                            )

                            ok = execute("""
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
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                                ON CONFLICT(
                                    roll_no,
                                    course_code,
                                    assessment,
                                    clo
                                )
                                DO UPDATE SET
                                    obtained =
                                        excluded.obtained,
                                    total =
                                        excluded.total,
                                    percentage =
                                        excluded.percentage,
                                    grade =
                                        excluded.grade
                            """, (
                                roll,
                                course,
                                assessment,
                                clo,
                                obtained,
                                total,
                                percent,
                                letter
                            ))

                            if ok:
                                imported += 1
                            else:
                                skipped += 1

                        except Exception as e:

                            skipped += 1

                            errors.append(
                                f"Row {index + 2}: {e}"
                            )

                    st.success(
                        f"{imported} marks records imported/updated."
                    )

                    if skipped > 0:

                        st.warning(
                            f"{skipped} rows were skipped."
                        )

                        with st.expander(
                            "View skipped rows"
                        ):

                            for error in errors[:50]:
                                st.write(error)


# ============================================================
# INDIVIDUAL STUDENT PERFORMANCE
# ============================================================

elif page == "📊 Student Performance":

    st.title(
        "📊 Individual Student Performance"
    )

    students = fetch_all("""
        SELECT
            roll_no,
            name
        FROM students
        ORDER BY roll_no
    """)

    if not students:

        st.info(
            "No students have been enrolled yet."
        )

    else:

        student_options = {
            f"{roll} — {name}": roll
            for roll, name in students
        }

        selected = st.selectbox(
            "Select Student",
            list(student_options.keys())
        )

        roll = student_options[selected]

        student = fetch_one("""
            SELECT
                name,
                program,
                semester,
                section
            FROM students
            WHERE roll_no = ?
        """, (
            roll,
        ))

        if student:

            name = student[0]
            program = student[1]
            semester = student[2]
            section = student[3]

            st.markdown(f"""
            <div class="hero">

                <div class="hero-title">
                    🎓 {name}
                </div>

                <div class="hero-text">
                    Roll Number: <b>{roll}</b>
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    Program: <b>{program}</b>
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    Semester: <b>{semester}</b>
                    &nbsp;&nbsp; | &nbsp;&nbsp;
                    Section: <b>{section}</b>
                </div>

            </div>
            """, unsafe_allow_html=True)

            rows = fetch_all("""
                SELECT
                    course_code,
                    assessment,
                    clo,
                    obtained,
                    total,
                    percentage,
                    grade
                FROM results
                WHERE roll_no = ?
                ORDER BY course_code, assessment
            """, (
                roll,
            ))

            if not rows:

                st.info(
                    "No marks are available for this student."
                )

            else:

                result_df = dataframe(
                    rows,
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

                overall = result_df[
                    "Percentage"
                ].mean()

                passed = int(
                    (
                        result_df["Grade"] != "F"
                    ).sum()
                )

                failed = int(
                    (
                        result_df["Grade"] == "F"
                    ).sum()
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Overall Performance",
                    f"{overall:.1f}%"
                )

                c2.metric(
                    "Passed",
                    passed
                )

                c3.metric(
                    "Failed",
                    failed
                )

                st.subheader(
                    "📈 Performance by Course"
                )

                course_chart = (
                    result_df
                    .groupby("Course")[
                        "Percentage"
                    ]
                    .mean()
                    .round(2)
                )

                st.bar_chart(
                    course_chart
                )

                clo_data = result_df[
                    result_df["CLO"].astype(str).str.strip() != ""
                ]

                if not clo_data.empty:

                    st.subheader(
                        "🎯 Individual CLO Performance"
                    )

                    clo_chart = (
                        clo_data
                        .groupby("CLO")[
                            "Percentage"
                        ]
                        .mean()
                        .round(2)
                    )

                    st.bar_chart(
                        clo_chart
                    )

                st.subheader(
                    "📋 Detailed Results"
                )

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# ATTAINMENT TRACKER
# ============================================================

elif page == "🎯 Attainment Tracker":

    st.title(
        "🎯 CLO & PLO Attainment Tracker"
    )

    tab1, tab2 = st.tabs(
        [
            "CLO Attainment",
            "PLO Attainment"
        ]
    )

    # --------------------------------------------------------
    # CLO ATTAINMENT
    # --------------------------------------------------------

    with tab1:

        rows = fetch_all("""
            SELECT
                clo,
                AVG(percentage)
            FROM results
            WHERE clo != ''
            GROUP BY clo
            ORDER BY clo
        """)

        if rows:

            clo_df = dataframe(
                rows,
                [
                    "CLO",
                    "Attainment"
                ]
            )

            clo_df["Attainment"] = pd.to_numeric(
                clo_df["Attainment"],
                errors="coerce"
            ).round(2)

            st.subheader(
                "CLO Attainment (%)"
            )

            st.bar_chart(
                clo_df.set_index("CLO")
            )

            st.dataframe(
                clo_df,
                use_container_width=True,
                hide_index=True
            )

            weak = clo_df[
                clo_df["Attainment"] < 70
            ]

            if not weak.empty:

                st.warning(
                    "CLOs below 70% attainment"
                )

                st.dataframe(
                    weak,
                    use_container_width=True,
                    hide_index=True
                )

        else:

            st.info(
                "No CLO-linked marks are available."
            )

    # --------------------------------------------------------
    # PLO ATTAINMENT
    # --------------------------------------------------------

    with tab2:

        mapping_rows = fetch_all("""
            SELECT
                course_code,
                clo,
                plo,
                strength
            FROM mappings
            WHERE strength > 0
        """)

        result_rows = fetch_all("""
            SELECT
                course_code,
                clo,
                percentage
            FROM results
            WHERE clo != ''
        """)

        if not mapping_rows:

            st.info(
                "Create CLO-PLO mappings first."
            )

        elif not result_rows:

            st.info(
                "Upload CLO-linked student marks first."
            )

        else:

            mapping_df = dataframe(
                mapping_rows,
                [
                    "Course",
                    "CLO",
                    "PLO",
                    "Strength"
                ]
            )

            result_df = dataframe(
                result_rows,
                [
                    "Course",
                    "CLO",
                    "Percentage"
                ]
            )

            merged = result_df.merge(
                mapping_df,
                on=[
                    "Course",
                    "CLO"
                ],
                how="inner"
            )

            if merged.empty:

                st.info(
                    "No matching CLO-PLO data is available."
                )

            else:

                merged["Weighted"] = (
                    merged["Percentage"]
                    * merged["Strength"]
                )

                plo_values = (
                    merged
                    .groupby("PLO")
                    .apply(
                        lambda x:
                        x["Weighted"].sum()
                        /
                        x["Strength"].sum()
                        if x["Strength"].sum() > 0
                        else 0
                    )
                    .round(2)
                )

                st.subheader(
                    "🏆 PLO Attainment (%)"
                )

                st.bar_chart(
                    plo_values
                )

                plo_table = pd.DataFrame({
                    "PLO": plo_values.index,
                    "Attainment": plo_values.values
                })

                st.dataframe(
                    plo_table,
                    use_container_width=True,
                    hide_index=True
                )

                weak = plo_table[
                    plo_table["Attainment"] < 70
                ]

                if not weak.empty:

                    st.warning(
                        "PLOs below 70% attainment"
                    )

                    st.dataframe(
                        weak,
                        use_container_width=True,
                        hide_index=True
                    )


# ============================================================
# REPORTS
# ============================================================

elif page == "📤 Reports":

    st.title(
        "📤 Reports & Export"
    )

    st.write(
        "Download the Fast Tutor academic data as Excel."
    )

    courses = dataframe(
        fetch_all("""
            SELECT
                code,
                name,
                credit_hours,
                semester
            FROM courses
        """),
        [
            "Course Code",
            "Course Name",
            "Credit Hours",
            "Semester"
        ]
    )

    students = dataframe(
        fetch_all("""
            SELECT
                roll_no,
                name,
                program,
                semester,
                section
            FROM students
        """),
        [
            "Roll Number",
            "Student Name",
            "Program",
            "Semester",
            "Section"
        ]
    )

    assessments = dataframe(
        fetch_all("""
            SELECT
                course_code,
                name,
                assessment_type,
                total_marks,
                weightage
            FROM assessments
        """),
        [
            "Course",
            "Assessment",
            "Type",
            "Total Marks",
            "Weightage"
        ]
    )

    clos = dataframe(
        fetch_all("""
            SELECT
                course_code,
                clo,
                description,
                bloom
            FROM clos
        """),
        [
            "Course",
            "CLO",
            "Description",
            "Bloom"
        ]
    )

    plos = dataframe(
        fetch_all("""
            SELECT
                plo,
                description
            FROM plos
        """),
        [
            "PLO",
            "Description"
        ]
    )

    mappings = dataframe(
        fetch_all("""
            SELECT
                course_code,
                clo,
                plo,
                strength
            FROM mappings
        """),
        [
            "Course",
            "CLO",
            "PLO",
            "Strength"
        ]
    )

    results = dataframe(
        fetch_all("""
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
        """),
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

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        courses.to_excel(
            writer,
            sheet_name="Courses",
            index=False
        )

        students.to_excel(
            writer,
            sheet_name="Students",
            index=False
        )

        assessments.to_excel(
            writer,
            sheet_name="Assessments",
            index=False
        )

        clos.to_excel(
            writer,
            sheet_name="CLOs",
            index=False
        )

        plos.to_excel(
            writer,
            sheet_name="PLOs",
            index=False
        )

        mappings.to_excel(
            writer,
            sheet_name="CLO-PLO Mapping",
            index=False
        )

        results.to_excel(
            writer,
            sheet_name="Results",
            index=False
        )

    st.download_button(
        "⬇️ DOWNLOAD COMPLETE EXCEL REPORT",
        output.getvalue(),
        "Fast_Tutor_Complete_Report.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.success(
        "Complete Fast Tutor Excel report is ready."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown("""
<div style="
    text-align:center;
    padding:18px;
">

    <div style="
        color:#0795D1;
        font-size:18px;
        font-weight:900;
        letter-spacing:2px;
    ">
        FAST TUTOR
    </div>

    <div style="
        color:#777;
        font-size:12px;
        margin-top:5px;
    ">
        Student Performance System
    </div>

</div>
""", unsafe_allow_html=True)
