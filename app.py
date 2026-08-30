import sqlite3
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import plotly.express as px


# ============================================================
# FAST TUTOR
# CLO-PLO MAPPING & STUDENT ASSESSMENT SYSTEM
# ============================================================

APP_NAME = "FAST TUTOR"
APP_SUBTITLE = "CLO-PLO Mapping & Student Assessment System"
DB_NAME = "fast_tutor.db"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FAST TUTOR",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .sub-title {
        font-size: 18px;
        color: #666;
        margin-top: 0;
        margin-bottom: 25px;
    }

    .brand-box {
        padding: 18px;
        border-radius: 12px;
        background: linear-gradient(135deg, #1f4e79, #2878b5);
        color: white;
        margin-bottom: 20px;
    }

    .brand-name {
        font-size: 28px;
        font-weight: 800;
    }

    .brand-description {
        font-size: 14px;
        opacity: 0.95;
    }

    .metric-box {
        padding: 20px;
        border-radius: 12px;
        background: #f5f7fa;
        border: 1px solid #e0e4e8;
        text-align: center;
    }

    .metric-number {
        font-size: 32px;
        font-weight: 800;
    }

    .metric-label {
        font-size: 14px;
        color: #666;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DATABASE
# ============================================================

@st.cache_resource
def get_database():

    database = sqlite3.connect(
        DB_NAME,
        check_same_thread=False,
        timeout=30
    )

    return database


db = get_database()


def execute(query, params=()):

    cursor = db.cursor()

    try:

        cursor.execute(
            query,
            params
        )

        db.commit()

        return cursor

    except sqlite3.Error:

        db.rollback()

        raise


def fetch_df(query, params=()):

    return pd.read_sql_query(
        query,
        db,
        params=params
    )


def initialize_database():

    execute(
        """
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            department TEXT,
            created_at TEXT
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS plos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            name TEXT,
            description TEXT,
            created_at TEXT,
            UNIQUE(program_id, code)
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            name TEXT NOT NULL,
            credit_hours REAL DEFAULT 3,
            semester INTEGER DEFAULT 1,
            created_at TEXT,
            UNIQUE(program_id, code)
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS clos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            description TEXT,
            bloom_level TEXT,
            assessment TEXT,
            target REAL DEFAULT 70,
            created_at TEXT,
            UNIQUE(course_id, code)
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clo_id INTEGER NOT NULL,
            plo_id INTEGER NOT NULL,
            strength INTEGER NOT NULL DEFAULT 0,
            UNIQUE(clo_id, plo_id)
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            email TEXT,
            program_id INTEGER,
            section TEXT,
            semester INTEGER,
            created_at TEXT
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            assessment_type TEXT,
            total_marks REAL DEFAULT 100,
            assessment_date TEXT,
            created_at TEXT,
            UNIQUE(course_id, name)
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            clo_id INTEGER NOT NULL,
            marks_obtained REAL NOT NULL,
            marks_total REAL NOT NULL,
            UNIQUE(
                assessment_id,
                student_id,
                clo_id
            )
        )
        """
    )


initialize_database()


# ============================================================
# HELPER FUNCTIONS
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


def normalize_column(column):

    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
    )


def read_file(uploaded_file):

    if uploaded_file.name.lower().endswith(".csv"):

        return pd.read_csv(
            uploaded_file,
            dtype=str
        )

    return pd.read_excel(
        uploaded_file,
        dtype=str
    )


def programs_df():

    return fetch_df(
        """
        SELECT *
        FROM programs
        ORDER BY code
        """
    )


def plos_df():

    return fetch_df(
        """
        SELECT
            plos.*,
            programs.code AS program_code,
            programs.name AS program_name
        FROM plos
        JOIN programs
            ON plos.program_id = programs.id
        ORDER BY
            programs.code,
            plos.code
        """
    )


def courses_df():

    return fetch_df(
        """
        SELECT
            courses.*,
            programs.code AS program_code,
            programs.name AS program_name
        FROM courses
        JOIN programs
            ON courses.program_id = programs.id
        ORDER BY
            programs.code,
            courses.code
        """
    )


def clos_df():

    return fetch_df(
        """
        SELECT
            clos.*,
            courses.code AS course_code,
            courses.name AS course_name
        FROM clos
        JOIN courses
            ON clos.course_id = courses.id
        ORDER BY
            courses.code,
            clos.code
        """
    )


def students_df():

    return fetch_df(
        """
        SELECT
            students.*,
            programs.code AS program_code
        FROM students
        LEFT JOIN programs
            ON students.program_id = programs.id
        ORDER BY
            students.roll_number
        """
    )


def assessments_df():

    return fetch_df(
        """
        SELECT
            assessments.*,
            courses.code AS course_code,
            courses.name AS course_name
        FROM assessments
        JOIN courses
            ON assessments.course_id = courses.id
        ORDER BY
            assessments.id DESC
        """
    )


def program_choices():

    data = programs_df()

    return {
        f"{row['code']} - {row['name']}":
        int(row["id"])
        for _, row in data.iterrows()
    }


def course_choices():

    data = courses_df()

    return {
        f"{row['code']} - {row['name']}":
        int(row["id"])
        for _, row in data.iterrows()
    }


def assessment_choices():

    data = assessments_df()

    return {
        f"{row['course_code']} | {row['name']}":
        int(row["id"])
        for _, row in data.iterrows()
    }


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand-box">
            <div class="brand-name">🎓 FAST TUTOR</div>
            <div class="brand-description">
                CLO-PLO Mapping & Student Assessment System
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    page = st.radio(
        "FAST TUTOR MENU",
        [
            "🏠 Dashboard",
            "🏫 Programs",
            "🎯 PLO Management",
            "📚 Course Management",
            "📝 CLO Management",
            "🔗 CLO-PLO Mapping",
            "👨‍🎓 Student Management",
            "📋 Assessment Management",
            "📤 Bulk Marks Upload",
            "📊 PLO Attainment",
            "📑 Reports",
            "📥 Import / Export",
            "⚙️ Settings"
        ]
    )

    st.divider()

    st.caption(
        "FAST TUTOR"
    )

    st.caption(
        "Academic Outcome Assessment System"
    )


# ============================================================
# HEADER FUNCTION
# ============================================================

def page_header(title, subtitle=""):

    st.markdown(
        f"""
        <div class="main-title">
            🎓 {title}
        </div>
        <div class="sub-title">
            {subtitle}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    page_header(
        "FAST TUTOR",
        "CLO-PLO Mapping & Student Assessment Dashboard"
    )

    programs = programs_df()
    plos = plos_df()
    courses = courses_df()
    clos = clos_df()
    students = students_df()
    assessments = assessments_df()

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "🏫 Programs",
            len(programs)
        )

    with c2:

        st.metric(
            "📚 Courses",
            len(courses)
        )

    with c3:

        st.metric(
            "📝 CLOs",
            len(clos)
        )

    with c4:

        st.metric(
            "🎯 PLOs",
            len(plos)
        )

    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "👨‍🎓 Students",
        len(students)
    )

    c2.metric(
        "📋 Assessments",
        len(assessments)
    )

    mappings = fetch_df(
        """
        SELECT *
        FROM mappings
        WHERE strength > 0
        """
    )

    c3.metric(
        "🔗 Active Mappings",
        len(mappings)
    )

    if len(plos) > 0:

        mapped_plo_ids = set(
            mappings["plo_id"].tolist()
        ) if not mappings.empty else set()

        weak_count = len(
            [
                x
                for x in plos["id"]
                if x not in mapped_plo_ids
            ]
        )

    else:

        weak_count = 0

    c4.metric(
        "⚠️ Unmapped PLOs",
        weak_count
    )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "📊 PLO Coverage"
        )

        if plos.empty:

            st.info(
                "Add PLOs to see coverage."
            )

        else:

            coverage_rows = []

            for _, plo in plos.iterrows():

                count = fetch_df(
                    """
                    SELECT COUNT(*) AS count
                    FROM mappings
                    WHERE
                        plo_id = ?
                        AND strength > 0
                    """,
                    (int(plo["id"]),)
                ).iloc[0]["count"]

                coverage_rows.append(
                    {
                        "PLO": plo["code"],
                        "Mapped CLOs": int(count)
                    }
                )

            coverage = pd.DataFrame(
                coverage_rows
            )

            fig = px.bar(
                coverage,
                x="PLO",
                y="Mapped CLOs",
                title="CLO Coverage by PLO"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    with right:

        st.subheader(
            "🔗 Mapping Strength"
        )

        if mappings.empty:

            st.info(
                "No mappings available."
            )

        else:

            strength = (
                mappings
                .groupby("strength")
                .size()
                .reset_index(
                    name="Count"
                )
            )

            strength["Level"] = (
                strength["strength"]
                .map(
                    {
                        1: "Low",
                        2: "Medium",
                        3: "High"
                    }
                )
            )

            fig = px.bar(
                strength,
                x="Level",
                y="Count",
                title="CLO-PLO Mapping Strength"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    st.divider()

    st.subheader(
        "🚀 FAST TUTOR Workflow"
    )

    st.markdown(
        """
        **1. Create Program** →  
        **2. Add PLOs** →  
        **3. Add Courses** →  
        **4. Add CLOs** →  
        **5. Map CLOs to PLOs** →  
        **6. Import Students in Bulk** →  
        **7. Create Assessment** →  
        **8. Upload Complete Class Marks** →  
        **9. Calculate CLO/PLO Attainment** →  
        **10. Generate Reports**
        """
    )


# ============================================================
# PROGRAMS
# ============================================================

elif page == "🏫 Programs":

    page_header(
        "Program Management",
        "Create and manage academic programs"
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Add Program",
            "📋 Programs"
        ]
    )

    with tab1:

        with st.form("program_form"):

            code = st.text_input(
                "Program Code",
                placeholder="BSCS"
            )

            name = st.text_input(
                "Program Name",
                placeholder="BS Computer Science"
            )

            department = st.text_input(
                "Department",
                placeholder="Department of Computer Science"
            )

            submit = st.form_submit_button(
                "💾 Save Program"
            )

            if submit:

                if not code.strip():

                    st.error(
                        "Program code is required."
                    )

                elif not name.strip():

                    st.error(
                        "Program name is required."
                    )

                else:

                    try:

                        execute(
                            """
                            INSERT INTO programs
                            (
                                code,
                                name,
                                department,
                                created_at
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                code.strip(),
                                name.strip(),
                                department.strip(),
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "Program added successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "A program with this code already exists."
                        )

    with tab2:

        data = programs_df()

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PLO MANAGEMENT
# ============================================================

elif page == "🎯 PLO Management":

    page_header(
        "PLO Management",
        "Define Program Learning Outcomes"
    )

    programs = program_choices()

    if not programs:

        st.warning(
            "Please create a program first."
        )

    else:

        tab1, tab2 = st.tabs(
            [
                "➕ Add PLO",
                "📋 PLO List"
            ]
        )

        with tab1:

            program = st.selectbox(
                "Program",
                list(programs.keys())
            )

            code = st.text_input(
                "PLO Code",
                placeholder="PLO1"
            )

            name = st.text_input(
                "PLO Name",
                placeholder="Knowledge of Computing"
            )

            description = st.text_area(
                "PLO Description"
            )

            if st.button(
                "💾 Save PLO",
                type="primary"
            ):

                if not code.strip():

                    st.error(
                        "PLO code is required."
                    )

                else:

                    try:

                        execute(
                            """
                            INSERT INTO plos
                            (
                                program_id,
                                code,
                                name,
                                description,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                programs[program],
                                code.strip(),
                                name.strip(),
                                description.strip(),
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "PLO added successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This PLO already exists for this program."
                        )

        with tab2:

            st.dataframe(
                plos_df(),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# COURSE MANAGEMENT
# ============================================================

elif page == "📚 Course Management":

    page_header(
        "Course Management",
        "Create and manage courses"
    )

    programs = program_choices()

    if not programs:

        st.warning(
            "Please create a program first."
        )

    else:

        tab1, tab2 = st.tabs(
            [
                "➕ Add Course",
                "📋 Courses"
            ]
        )

        with tab1:

            program = st.selectbox(
                "Program",
                list(programs.keys())
            )

            code = st.text_input(
                "Course Code",
                placeholder="CS101"
            )

            name = st.text_input(
                "Course Name",
                placeholder="Programming Fundamentals"
            )

            col1, col2 = st.columns(2)

            with col1:

                credit_hours = st.number_input(
                    "Credit Hours",
                    0.5,
                    10.0,
                    3.0,
                    0.5
                )

            with col2:

                semester = st.number_input(
                    "Semester",
                    1,
                    12,
                    1
                )

            if st.button(
                "💾 Save Course",
                type="primary"
            ):

                if not code.strip() or not name.strip():

                    st.error(
                        "Course code and name are required."
                    )

                else:

                    try:

                        execute(
                            """
                            INSERT INTO courses
                            (
                                program_id,
                                code,
                                name,
                                credit_hours,
                                semester,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                programs[program],
                                code.strip(),
                                name.strip(),
                                credit_hours,
                                semester,
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "Course added successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This course already exists."
                        )

        with tab2:

            st.dataframe(
                courses_df(),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# CLO MANAGEMENT
# ============================================================

elif page == "📝 CLO Management":

    page_header(
        "CLO Management",
        "Define Course Learning Outcomes"
    )

    courses = course_choices()

    if not courses:

        st.warning(
            "Please create a course first."
        )

    else:

        tab1, tab2 = st.tabs(
            [
                "➕ Add CLO",
                "📋 CLO List"
            ]
        )

        with tab1:

            course = st.selectbox(
                "Course",
                list(courses.keys())
            )

            code = st.text_input(
                "CLO Code",
                placeholder="CLO1"
            )

            description = st.text_area(
                "CLO Description",
                placeholder=(
                    "Explain fundamental programming concepts."
                )
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

            assessment = st.text_input(
                "Assessment",
                placeholder="Midterm Examination"
            )

            target = st.number_input(
                "Target Attainment (%)",
                0.0,
                100.0,
                70.0,
                1.0
            )

            if st.button(
                "💾 Save CLO",
                type="primary"
            ):

                if not code.strip():

                    st.error(
                        "CLO code is required."
                    )

                else:

                    try:

                        execute(
                            """
                            INSERT INTO clos
                            (
                                course_id,
                                code,
                                description,
                                bloom_level,
                                assessment,
                                target,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                courses[course],
                                code.strip(),
                                description.strip(),
                                bloom,
                                assessment.strip(),
                                target,
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "CLO added successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This CLO already exists for this course."
                        )

        with tab2:

            st.dataframe(
                clos_df(),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# CLO-PLO MAPPING
# ============================================================

elif page == "🔗 CLO-PLO Mapping":

    page_header(
        "CLO-PLO Mapping",
        "Map each CLO to the appropriate PLO"
    )

    courses = courses_df()
    plos = plos_df()
    clos = clos_df()

    if courses.empty:

        st.warning(
            "Please create courses first."
        )

    elif plos.empty:

        st.warning(
            "Please create PLOs first."
        )

    elif clos.empty:

        st.warning(
            "Please create CLOs first."
        )

    else:

        course_display = {
            f"{r['code']} - {r['name']}":
            int(r["id"])
            for _, r in courses.iterrows()
        }

        selected_course = st.selectbox(
            "Select Course",
            list(course_display.keys())
        )

        course_id = course_display[
            selected_course
        ]

        selected_course_row = courses[
            courses["id"] == course_id
        ].iloc[0]

        program_id = int(
            selected_course_row["program_id"]
        )

        course_clos = clos[
            clos["course_id"] == course_id
        ]

        program_plos = plos[
            plos["program_id"] == program_id
        ]

        if program_plos.empty:

            st.warning(
                "No PLOs have been created for this program."
            )

        else:

            st.info(
                "0 = No Mapping | 1 = Low | "
                "2 = Medium | 3 = High"
            )

            matrix_rows = []

            for _, clo in course_clos.iterrows():

                row = {
                    "CLO": clo["code"]
                }

                for _, plo in program_plos.iterrows():

                    existing = fetch_df(
                        """
                        SELECT strength
                        FROM mappings
                        WHERE
                            clo_id = ?
                            AND plo_id = ?
                        """,
                        (
                            int(clo["id"]),
                            int(plo["id"])
                        )
                    )

                    if existing.empty:

                        row[
                            plo["code"]
                        ] = 0

                    else:

                        row[
                            plo["code"]
                        ] = int(
                            existing.iloc[0][
                                "strength"
                            ]
                        )

                matrix_rows.append(row)

            matrix = pd.DataFrame(
                matrix_rows
            )

            st.subheader(
                "Current Mapping Matrix"
            )

            st.dataframe(
                matrix,
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "Edit Mapping"
            )

            for _, clo in course_clos.iterrows():

                st.markdown(
                    f"#### {clo['code']}: {clo['description']}"
                )

                cols = st.columns(
                    len(program_plos)
                )

                for i, (_, plo) in enumerate(
                    program_plos.iterrows()
                ):

                    existing = fetch_df(
                        """
                        SELECT strength
                        FROM mappings
                        WHERE
                            clo_id = ?
                            AND plo_id = ?
                        """,
                        (
                            int(clo["id"]),
                            int(plo["id"])
                        )
                    )

                    current = 0

                    if not existing.empty:

                        current = int(
                            existing.iloc[0]["strength"]
                        )

                    with cols[i]:

                        value = st.selectbox(
                            plo["code"],
                            [0, 1, 2, 3],
                            index=current,
                            key=(
                                f"mapping_"
                                f"{clo['id']}_"
                                f"{plo['id']}"
                            )
                        )

                        if st.button(
                            f"Save {clo['code']} → {plo['code']}",
                            key=(
                                f"save_"
                                f"{clo['id']}_"
                                f"{plo['id']}"
                            )
                        ):

                            execute(
                                """
                                INSERT INTO mappings
                                (
                                    clo_id,
                                    plo_id,
                                    strength
                                )
                                VALUES (?, ?, ?)
                                ON CONFLICT(
                                    clo_id,
                                    plo_id
                                )
                                DO UPDATE SET
                                    strength =
                                    excluded.strength
                                """,
                                (
                                    int(clo["id"]),
                                    int(plo["id"]),
                                    value
                                )
                            )

                            st.success(
                                "Mapping saved."
                            )

                            st.rerun()


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

elif page == "👨‍🎓 Student Management":

    page_header(
        "Student Management",
        "Manage students by roll number and name"
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Add Student",
            "📋 Student List"
        ]
    )

    with tab1:

        st.info(
            "For a complete class, use "
            "'Bulk Marks Upload → Import Students' "
            "instead of entering students individually."
        )

        programs = program_choices()

        with st.form("student_form"):

            roll_number = st.text_input(
                "Roll Number",
                placeholder="2026-CS-001"
            )

            name = st.text_input(
                "Student Name",
                placeholder="Muhammad Ali"
            )

            email = st.text_input(
                "Email"
            )

            section = st.text_input(
                "Section",
                placeholder="A"
            )

            semester = st.number_input(
                "Semester",
                1,
                12,
                1
            )

            program = None

            if programs:

                program = st.selectbox(
                    "Program",
                    list(programs.keys())
                )

            submit = st.form_submit_button(
                "💾 Save Student"
            )

            if submit:

                if not roll_number.strip():

                    st.error(
                        "Roll number is required."
                    )

                elif not name.strip():

                    st.error(
                        "Student name is required."
                    )

                else:

                    try:

                        program_id = (
                            programs[program]
                            if program
                            else None
                        )

                        execute(
                            """
                            INSERT INTO students
                            (
                                roll_number,
                                name,
                                email,
                                program_id,
                                section,
                                semester,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                roll_number.strip(),
                                name.strip(),
                                email.strip(),
                                program_id,
                                section.strip(),
                                semester,
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "Student saved successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This roll number already exists."
                        )

    with tab2:

        students = students_df()

        st.dataframe(
            students,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ASSESSMENT MANAGEMENT
# ============================================================

elif page == "📋 Assessment Management":

    page_header(
        "Assessment Management",
        "Create assessments before uploading student marks"
    )

    courses = course_choices()

    if not courses:

        st.warning(
            "Please create courses first."
        )

    else:

        with st.form("assessment_form"):

            course = st.selectbox(
                "Course",
                list(courses.keys())
            )

            name = st.text_input(
                "Assessment Name",
                placeholder="Midterm Examination"
            )

            assessment_type = st.selectbox(
                "Assessment Type",
                [
                    "Midterm",
                    "Final",
                    "Quiz",
                    "Assignment",
                    "Project",
                    "Practical",
                    "Other"
                ]
            )

            total_marks = st.number_input(
                "Total Marks",
                1.0,
                1000.0,
                100.0,
                1.0
            )

            assessment_date = st.date_input(
                "Assessment Date"
            )

            submit = st.form_submit_button(
                "💾 Save Assessment"
            )

            if submit:

                if not name.strip():

                    st.error(
                        "Assessment name is required."
                    )

                else:

                    try:

                        execute(
                            """
                            INSERT INTO assessments
                            (
                                course_id,
                                name,
                                assessment_type,
                                total_marks,
                                assessment_date,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                courses[course],
                                name.strip(),
                                assessment_type,
                                total_marks,
                                str(assessment_date),
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "Assessment created successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This assessment already exists for this course."
                        )

        st.subheader(
            "Existing Assessments"
        )

        st.dataframe(
            assessments_df(),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# BULK MARKS UPLOAD
# ============================================================

elif page == "📤 Bulk Marks Upload":

    page_header(
        "Bulk Marks Upload",
        "Upload the complete class results in one Excel or CSV file"
    )

    st.success(
        "🚀 FAST TUTOR allows you to upload the marks "
        "of the entire class at once. You do NOT need "
        "to enter marks student by student."
    )

    assessments = assessments_df()

    if assessments.empty:

        st.warning(
            "Please create an assessment first."
        )

    else:

        assessment_map = assessment_choices()

        selected = st.selectbox(
            "Select Assessment",
            list(assessment_map.keys())
        )

        assessment_id = assessment_map[
            selected
        ]

        assessment = assessments[
            assessments["id"] == assessment_id
        ].iloc[0]

        course_id = int(
            assessment["course_id"]
        )

        all_clos = clos_df()

        course_clos = all_clos[
            all_clos["course_id"] == course_id
        ]

        if course_clos.empty:

            st.warning(
                "No CLOs exist for this course."
            )

        else:

            clo_codes = [
                clean(x)
                for x in course_clos["code"]
            ]

            st.subheader(
                "Step 1 — Download the marks template"
            )

            students = students_df()

            template_columns = [
                "roll_number",
                "name"
            ] + clo_codes

            if students.empty:

                template = pd.DataFrame(
                    columns=template_columns
                )

            else:

                template = students[
                    [
                        "roll_number",
                        "name"
                    ]
                ].copy()

                for clo in clo_codes:

                    template[clo] = ""

            st.dataframe(
                template,
                use_container_width=True,
                hide_index=True
            )

            csv_template = (
                template
                .to_csv(index=False)
                .encode("utf-8-sig")
            )

            st.download_button(
                "📥 Download CSV Template",
                csv_template,
                "FAST_TUTOR_MARKS_TEMPLATE.csv",
                "text/csv"
            )

            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl"
            ) as writer:

                template.to_excel(
                    writer,
                    index=False,
                    sheet_name="Student Marks"
                )

            excel_buffer.seek(0)

            st.download_button(
                "📥 Download Excel Template",
                excel_buffer,
                "FAST_TUTOR_MARKS_TEMPLATE.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()

            st.subheader(
                "Step 2 — Upload completed marks"
            )

            uploaded = st.file_uploader(
                "Upload Excel or CSV",
                type=[
                    "xlsx",
                    "xls",
                    "csv"
                ],
                key="fast_tutor_marks"
            )

            if uploaded is not None:

                try:

                    data = read_file(
                        uploaded
                    )

                    data.columns = [
                        normalize_column(c)
                        for c in data.columns
                    ]

                    aliases = {
                        "roll_no": "roll_number",
                        "rollno": "roll_number",
                        "roll": "roll_number",
                        "student_id": "roll_number",
                        "studentid": "roll_number",
                        "registration_no": "roll_number",
                        "registration_number": "roll_number",
                        "student_name": "name",
                        "full_name": "name",
                        "student": "name"
                    }

                    data = data.rename(
                        columns=aliases
                    )

                    required = [
                        "roll_number"
                    ]

                    missing = [
                        column
                        for column in required
                        if column not in data.columns
                    ]

                    if missing:

                        st.error(
                            "Missing column: roll_number"
                        )

                    else:

                        missing_clos = [
                            clo
                            for clo in clo_codes
                            if clo not in data.columns
                        ]

                        if missing_clos:

                            st.error(
                                "The following CLO columns "
                                "are missing: "
                                + ", ".join(
                                    missing_clos
                                )
                            )

                        else:

                            registered_students = students_df()

                            registered_rolls = set(
                                registered_students[
                                    "roll_number"
                                ]
                                .astype(str)
                                .str.strip()
                            )

                            uploaded_rolls = (
                                data[
                                    "roll_number"
                                ]
                                .astype(str)
                                .str.strip()
                            )

                            unknown_rolls = [
                                roll
                                for roll in uploaded_rolls
                                if roll
                                and roll not in registered_rolls
                            ]

                            if unknown_rolls:

                                st.error(
                                    "Some roll numbers are not "
                                    "registered in FAST TUTOR."
                                )

                                st.write(
                                    ", ".join(
                                        unknown_rolls
                                    )
                                )

                                st.info(
                                    "Import the student list first "
                                    "from Student Management / Import-Export."
                                )

                            else:

                                for clo in clo_codes:

                                    data[clo] = pd.to_numeric(
                                        data[clo],
                                        errors="coerce"
                                    )

                                st.subheader(
                                    "Step 3 — Preview marks"
                                )

                                st.dataframe(
                                    data,
                                    use_container_width=True,
                                    hide_index=True
                                )

                                st.subheader(
                                    "Step 4 — CLO total marks"
                                )

                                total_marks = {}

                                columns = st.columns(
                                    min(
                                        4,
                                        len(clo_codes)
                                    )
                                )

                                for index, clo in enumerate(
                                    clo_codes
                                ):

                                    with columns[
                                        index % len(columns)
                                    ]:

                                        total_marks[
                                            clo
                                        ] = st.number_input(
                                            f"{clo} Total Marks",
                                            min_value=0.01,
                                            value=10.0,
                                            step=1.0,
                                            key=(
                                                "total_"
                                                + str(
                                                    assessment_id
                                                )
                                                + "_"
                                                + clo
                                            )
                                        )

                                errors = []

                                for clo in clo_codes:

                                    valid_marks = data[
                                        clo
                                    ].dropna()

                                    if (
                                        valid_marks < 0
                                    ).any():

                                        errors.append(
                                            f"{clo}: negative marks found."
                                        )

                                    if (
                                        valid_marks
                                        > total_marks[clo]
                                    ).any():

                                        errors.append(
                                            f"{clo}: marks exceed "
                                            f"total marks."
                                        )

                                if errors:

                                    st.error(
                                        "Please correct these errors:"
                                    )

                                    for error in errors:

                                        st.write(
                                            "• "
                                            + error
                                        )

                                else:

                                    st.divider()

                                    st.subheader(
                                        "Step 5 — Import complete class"
                                    )

                                    confirm = st.checkbox(
                                        "I confirm that the uploaded marks are correct."
                                    )

                                    if st.button(
                                        "🚀 IMPORT ALL STUDENT MARKS",
                                        type="primary",
                                        disabled=not confirm
                                    ):

                                        inserted = 0
                                        updated = 0

                                        try:

                                            db.execute(
                                                "BEGIN"
                                            )

                                            student_lookup = {
                                                str(
                                                    row[
                                                        "roll_number"
                                                    ]
                                                ).strip():
                                                int(
                                                    row["id"]
                                                )
                                                for _, row
                                                in registered_students.iterrows()
                                            }

                                            clo_lookup = {
                                                clean(
                                                    row["code"]
                                                ):
                                                int(
                                                    row["id"]
                                                )
                                                for _, row
                                                in course_clos.iterrows()
                                            }

                                            for _, row in data.iterrows():

                                                roll = clean(
                                                    row[
                                                        "roll_number"
                                                    ]
                                                )

                                                if not roll:

                                                    continue

                                                student_id = (
                                                    student_lookup[
                                                        roll
                                                    ]
                                                )

                                                for clo in clo_codes:

                                                    mark = row[
                                                        clo
                                                    ]

                                                    if pd.isna(
                                                        mark
                                                    ):

                                                        continue

                                                    obtained = float(
                                                        mark
                                                    )

                                                    total = float(
                                                        total_marks[
                                                            clo
                                                        ]
                                                    )

                                                    clo_id = (
                                                        clo_lookup[
                                                            clo
                                                        ]
                                                    )

                                                    existing = db.execute(
                                                        """
                                                        SELECT id
                                                        FROM results
                                                        WHERE
                                                            assessment_id = ?
                                                            AND student_id = ?
                                                            AND clo_id = ?
                                                        """,
                                                        (
                                                            assessment_id,
                                                            student_id,
                                                            clo_id
                                                        )
                                                    ).fetchone()

                                                    if existing:

                                                        db.execute(
                                                            """
                                                            UPDATE results
                                                            SET
                                                                marks_obtained = ?,
                                                                marks_total = ?
                                                            WHERE id = ?
                                                            """,
                                                            (
                                                                obtained,
                                                                total,
                                                                existing[0]
                                                            )
                                                        )

                                                        updated += 1

                                                    else:

                                                        db.execute(
                                                            """
                                                            INSERT INTO results
                                                            (
                                                                assessment_id,
                                                                student_id,
                                                                clo_id,
                                                                marks_obtained,
                                                                marks_total
                                                            )
                                                            VALUES (?, ?, ?, ?, ?)
                                                            """,
                                                            (
                                                                assessment_id,
                                                                student_id,
                                                                clo_id,
                                                                obtained,
                                                                total
                                                            )
                                                        )

                                                        inserted += 1

                                            db.commit()

                                            st.success(
                                                "🎉 FAST TUTOR: "
                                                "ALL STUDENT MARKS "
                                                "IMPORTED SUCCESSFULLY!"
                                            )

                                            a, b = st.columns(2)

                                            a.metric(
                                                "New Marks",
                                                inserted
                                            )

                                            b.metric(
                                                "Updated Marks",
                                                updated
                                            )

                                        except Exception as error:

                                            db.rollback()

                                            st.error(
                                                "The marks upload failed. "
                                                "No partial data was saved."
                                            )

                                            st.exception(
                                                error
                                            )

                except Exception as error:

                    st.error(
                        "Unable to read the uploaded file."
                    )

                    st.exception(
                        error
                    )


# ============================================================
# PLO ATTAINMENT
# ============================================================

elif page == "📊 PLO Attainment":

    page_header(
        "PLO Attainment",
        "Calculate CLO and PLO attainment from uploaded student marks"
    )

    results = fetch_df(
        """
        SELECT
            results.*,
            students.roll_number,
            students.name AS student_name,
            clos.code AS clo_code,
            clos.target,
            courses.code AS course_code
        FROM results
        JOIN students
            ON results.student_id = students.id
        JOIN clos
            ON results.clo_id = clos.id
        JOIN assessments
            ON results.assessment_id = assessments.id
        JOIN courses
            ON assessments.course_id = courses.id
        """
    )

    mappings = fetch_df(
        """
        SELECT
            mappings.*,
            clos.code AS clo_code,
            plos.code AS plo_code
        FROM mappings
        JOIN clos
            ON mappings.clo_id = clos.id
        JOIN plos
            ON mappings.plo_id = plos.id
        WHERE mappings.strength > 0
        """
    )

    if results.empty:

        st.info(
            "No student marks have been uploaded yet."
        )

    elif mappings.empty:

        st.warning(
            "Create CLO-PLO mappings first."
        )

    else:

        results["attainment"] = (
            results["marks_obtained"]
            /
            results["marks_total"]
            *
            100
        )

        clo_attainment = (
            results
            .groupby("clo_code")
            ["attainment"]
            .mean()
            .reset_index()
        )

        clo_attainment[
            "Attainment (%)"
        ] = clo_attainment[
            "attainment"
        ].round(2)

        st.subheader(
            "CLO Attainment"
        )

        st.dataframe(
            clo_attainment[
                [
                    "clo_code",
                    "Attainment (%)"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        plo_rows = []

        for plo_code in mappings[
            "plo_code"
        ].unique():

            mapping_rows = mappings[
                mappings["plo_code"]
                == plo_code
            ]

            values = []

            for _, mapping in mapping_rows.iterrows():

                clo = mapping["clo_code"]

                strength = float(
                    mapping["strength"]
                )

                clo_data = results[
                    results["clo_code"] == clo
                ]

                if clo_data.empty:

                    continue

                clo_average = (
                    clo_data["attainment"]
                    .mean()
                )

                contribution = (
                    clo_average
                    *
                    strength
                    /
                    3
                )

                values.append(
                    contribution
                )

            if values:

                plo_rows.append(
                    {
                        "PLO": plo_code,
                        "PLO Attainment (%)":
                        round(
                            sum(values)
                            /
                            len(values),
                            2
                        )
                    }
                )

        plo_df = pd.DataFrame(
            plo_rows
        )

        if not plo_df.empty:

            st.subheader(
                "PLO Attainment"
            )

            plo_df[
                "Status"
            ] = plo_df[
                "PLO Attainment (%)"
            ].apply(
                lambda x:
                "🟢 Meets Target"
                if x >= 70
                else
                "🔴 Below Target"
            )

            st.dataframe(
                plo_df,
                use_container_width=True,
                hide_index=True
            )

            fig = px.bar(
                plo_df,
                x="PLO",
                y="PLO Attainment (%)",
                text_auto=".1f",
                range_y=[0, 100],
                title="PLO Attainment"
            )

            fig.add_hline(
                y=70,
                line_dash="dash",
                annotation_text="70% Target"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            weak = plo_df[
                plo_df[
                    "PLO Attainment (%)"
                ] < 70
            ]

            st.subheader(
                "⚠️ Weak PLOs"
            )

            if weak.empty:

                st.success(
                    "All calculated PLOs meet the 70% target."
                )

            else:

                st.dataframe(
                    weak,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# REPORTS
# ============================================================

elif page == "📑 Reports":

    page_header(
        "FAST TUTOR Reports",
        "Generate academic outcome reports"
    )

    report = st.selectbox(
        "Select Report",
        [
            "CLO-PLO Matrix",
            "Course-wise Mapping",
            "Program-wide Mapping",
            "PLO Coverage",
            "Student Results",
            "PLO Attainment",
            "Weak PLO Report"
        ]
    )

    if report == "CLO-PLO Matrix":

        data = fetch_df(
            """
            SELECT
                courses.code AS Course,
                clos.code AS CLO,
                plos.code AS PLO,
                mappings.strength AS Strength
            FROM mappings
            JOIN clos
                ON mappings.clo_id = clos.id
            JOIN courses
                ON clos.course_id = courses.id
            JOIN plos
                ON mappings.plo_id = plos.id
            ORDER BY
                courses.code,
                clos.code,
                plos.code
            """
        )

        if data.empty:

            st.info(
                "No mappings available."
            )

        else:

            matrix = data.pivot_table(
                index=[
                    "Course",
                    "CLO"
                ],
                columns="PLO",
                values="Strength",
                fill_value=0
            ).reset_index()

            st.dataframe(
                matrix,
                use_container_width=True,
                hide_index=True
            )

    elif report == "Course-wise Mapping":

        data = fetch_df(
            """
            SELECT
                courses.code AS Course,
                courses.name AS Course_Name,
                clos.code AS CLO,
                plos.code AS PLO,
                mappings.strength AS Strength
            FROM mappings
            JOIN clos
                ON mappings.clo_id = clos.id
            JOIN courses
                ON clos.course_id = courses.id
            JOIN plos
                ON mappings.plo_id = plos.id
            ORDER BY courses.code
            """
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    elif report == "Program-wide Mapping":

        data = fetch_df(
            """
            SELECT
                programs.code AS Program,
                courses.code AS Course,
                clos.code AS CLO,
                plos.code AS PLO,
                mappings.strength AS Strength
            FROM mappings
            JOIN clos
                ON mappings.clo_id = clos.id
            JOIN courses
                ON clos.course_id = courses.id
            JOIN programs
                ON courses.program_id = programs.id
            JOIN plos
                ON mappings.plo_id = plos.id
            ORDER BY
                programs.code,
                courses.code
            """
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    elif report == "PLO Coverage":

        plos = plos_df()

        rows = []

        for _, plo in plos.iterrows():

            count = fetch_df(
                """
                SELECT COUNT(*) AS total
                FROM mappings
                WHERE
                    plo_id = ?
                    AND strength > 0
                """,
                (
                    int(plo["id"]),
                )
            ).iloc[0]["total"]

            rows.append(
                {
                    "PLO": plo["code"],
                    "Name": plo["name"],
                    "Mapped CLOs": int(count)
                }
            )

        data = pd.DataFrame(rows)

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    elif report == "Student Results":

        data = fetch_df(
            """
            SELECT
                students.roll_number AS Roll_Number,
                students.name AS Student_Name,
                courses.code AS Course,
                assessments.name AS Assessment,
                clos.code AS CLO,
                results.marks_obtained AS Marks,
                results.marks_total AS Total_Marks
            FROM results
            JOIN students
                ON results.student_id = students.id
            JOIN assessments
                ON results.assessment_id = assessments.id
            JOIN courses
                ON assessments.course_id = courses.id
            JOIN clos
                ON results.clo_id = clos.id
            ORDER BY
                students.roll_number
            """
        )

        if not data.empty:

            data["Percentage"] = (
                data["Marks"]
                /
                data["Total_Marks"]
                *
                100
            ).round(2)

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

        csv = data.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        st.download_button(
            "📥 Download Student Results",
            csv,
            "FAST_TUTOR_Student_Results.csv",
            "text/csv"
        )

    elif report == "PLO Attainment":

        results = fetch_df(
            """
            SELECT
                clos.code AS CLO,
                results.marks_obtained,
                results.marks_total
            FROM results
            JOIN clos
                ON results.clo_id = clos.id
            """
        )

        mappings = fetch_df(
            """
            SELECT
                plos.code AS PLO,
                clos.code AS CLO,
                mappings.strength
            FROM mappings
            JOIN plos
                ON mappings.plo_id = plos.id
            JOIN clos
                ON mappings.clo_id = clos.id
            WHERE mappings.strength > 0
            """
        )

        if results.empty or mappings.empty:

            st.info(
                "Not enough data for PLO attainment."
            )

        else:

            results["percentage"] = (
                results["marks_obtained"]
                /
                results["marks_total"]
                *
                100
            )

            rows = []

            for plo in mappings["PLO"].unique():

                mapping_rows = mappings[
                    mappings["PLO"] == plo
                ]

                values = []

                for _, mapping in mapping_rows.iterrows():

                    r = results[
                        results["CLO"]
                        == mapping["CLO"]
                    ]

                    if not r.empty:

                        average = r[
                            "percentage"
                        ].mean()

                        values.append(
                            average
                            *
                            mapping["strength"]
                            /
                            3
                        )

                if values:

                    rows.append(
                        {
                            "PLO": plo,
                            "Attainment (%)":
                            round(
                                sum(values)
                                /
                                len(values),
                                2
                            )
                        }
                    )

            data = pd.DataFrame(rows)

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

    else:

        plos = plos_df()

        mappings = fetch_df(
            """
            SELECT *
            FROM mappings
            WHERE strength > 0
            """
        )

        rows = []

        for _, plo in plos.iterrows():

            mapped = 0

            if not mappings.empty:

                mapped = len(
                    mappings[
                        mappings["plo_id"]
                        == plo["id"]
                    ]
                )

            if mapped == 0:

                rows.append(
                    {
                        "PLO": plo["code"],
                        "Name": plo["name"],
                        "Problem": "Unmapped"
                    }
                )

        data = pd.DataFrame(rows)

        if data.empty:

            st.success(
                "No unmapped PLOs found."
            )

        else:

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# IMPORT / EXPORT
# ============================================================

elif page == "📥 Import / Export":

    page_header(
        "Import / Export",
        "Bulk data management for FAST TUTOR"
    )

    tab1, tab2 = st.tabs(
        [
            "📥 Import",
            "📤 Export"
        ]
    )

    # --------------------------------------------------------
    # IMPORT
    # --------------------------------------------------------

    with tab1:

        import_type = st.selectbox(
            "Select Import Type",
            [
                "Students",
                "Student Marks"
            ]
        )

        # ====================================================
        # STUDENT IMPORT
        # ====================================================

        if import_type == "Students":

            st.subheader(
                "👨‍🎓 Bulk Student Import"
            )

            st.write(
                "Upload the complete student list."
            )

            template = pd.DataFrame(
                [
                    {
                        "roll_number": "2026-CS-001",
                        "name": "Ali Khan",
                        "email": "ali@example.com",
                        "section": "A",
                        "semester": "1"
                    },
                    {
                        "roll_number": "2026-CS-002",
                        "name": "Sara Ahmed",
                        "email": "sara@example.com",
                        "section": "A",
                        "semester": "1"
                    }
                ]
            )

            csv = template.to_csv(
                index=False
            ).encode(
                "utf-8-sig"
            )

            st.download_button(
                "📥 Download Student Template",
                csv,
                "FAST_TUTOR_STUDENT_TEMPLATE.csv",
                "text/csv"
            )

            programs = program_choices()

            selected_program = None

            if programs:

                selected_program = st.selectbox(
                    "Program for imported students",
                    list(programs.keys())
                )

            uploaded = st.file_uploader(
                "Upload Student Excel/CSV",
                type=[
                    "xlsx",
                    "xls",
                    "csv"
                ],
                key="students_import"
            )

            if uploaded:

                try:

                    data = read_file(
                        uploaded
                    )

                    data.columns = [
                        normalize_column(c)
                        for c in data.columns
                    ]

                    aliases = {
                        "roll_no": "roll_number",
                        "rollno": "roll_number",
                        "roll": "roll_number",
                        "student_id": "roll_number",
                        "studentid": "roll_number",
                        "student_name": "name",
                        "full_name": "name"
                    }

                    data = data.rename(
                        columns=aliases
                    )

                    if (
                        "roll_number"
                        not in data.columns
                    ) or (
                        "name"
                        not in data.columns
                    ):

                        st.error(
                            "Your file must contain "
                            "roll_number and name columns."
                        )

                    else:

                        st.dataframe(
                            data,
                            use_container_width=True,
                            hide_index=True
                        )

                        if st.button(
                            "🚀 IMPORT ALL STUDENTS",
                            type="primary"
                        ):

                            inserted = 0
                            updated = 0

                            try:

                                db.execute(
                                    "BEGIN"
                                )

                                program_id = None

                                if selected_program:

                                    program_id = programs[
                                        selected_program
                                    ]

                                for _, row in data.iterrows():

                                    roll = clean(
                                        row[
                                            "roll_number"
                                        ]
                                    )

                                    name = clean(
                                        row["name"]
                                    )

                                    if not roll or not name:

                                        continue

                                    email = clean(
                                        row.get(
                                            "email",
                                            ""
                                        )
                                    )

                                    section = clean(
                                        row.get(
                                            "section",
                                            ""
                                        )
                                    )

                                    semester = clean(
                                        row.get(
                                            "semester",
                                            ""
                                        )
                                    )

                                    existing = db.execute(
                                        """
                                        SELECT id
                                        FROM students
                                        WHERE roll_number = ?
                                        """,
                                        (
                                            roll,
                                        )
                                    ).fetchone()

                                    if existing:

                                        db.execute(
                                            """
                                            UPDATE students
                                            SET
                                                name = ?,
                                                email = ?,
                                                program_id = ?,
                                                section = ?,
                                                semester = ?
                                            WHERE id = ?
                                            """,
                                            (
                                                name,
                                                email,
                                                program_id,
                                                section,
                                                semester,
                                                existing[0]
                                            )
                                        )

                                        updated += 1

                                    else:

                                        db.execute(
                                            """
                                            INSERT INTO students
                                            (
                                                roll_number,
                                                name,
                                                email,
                                                program_id,
                                                section,
                                                semester,
                                                created_at
                                            )
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                            """,
                                            (
                                                roll,
                                                name,
                                                email,
                                                program_id,
                                                section,
                                                semester,
                                                datetime.now().isoformat()
                                            )
                                        )

                                        inserted += 1

                                db.commit()

                                st.success(
                                    "🎉 FAST TUTOR: "
                                    "STUDENTS IMPORTED!"
                                )

                                a, b = st.columns(2)

                                a.metric(
                                    "New Students",
                                    inserted
                                )

                                b.metric(
                                    "Updated Students",
                                    updated
                                )

                            except Exception as error:

                                db.rollback()

                                st.error(
                                    "Student import failed."
                                )

                                st.exception(
                                    error
                                )

                except Exception as error:

                    st.error(
                        "Unable to read the file."
                    )

                    st.exception(
                        error
                    )

        # ====================================================
        # MARKS IMPORT
        # ====================================================

        else:

            st.subheader(
                "📊 Bulk Student Marks Import"
            )

            st.success(
                "Upload marks for the ENTIRE CLASS "
                "in one file."
            )

            assessments = assessments_df()

            if assessments.empty:

                st.warning(
                    "Create an assessment first."
                )

            else:

                assessment_map = assessment_choices()

                selected_assessment = st.selectbox(
                    "Assessment",
                    list(
                        assessment_map.keys()
                    )
                )

                assessment_id = assessment_map[
                    selected_assessment
                ]

                assessment = assessments[
                    assessments["id"]
                    == assessment_id
                ].iloc[0]

                course_id = int(
                    assessment["course_id"]
                )

                all_clos = clos_df()

                course_clos = all_clos[
                    all_clos["course_id"]
                    == course_id
                ]

                if course_clos.empty:

                    st.warning(
                        "This course has no CLOs."
                    )

                else:

                    clo_codes = [
                        clean(c)
                        for c in course_clos["code"]
                    ]

                    st.markdown(
                        "### Required columns"
                    )

                    st.code(
                        "roll_number | name | "
                        + " | ".join(
                            clo_codes
                        )
                    )

                    students = students_df()

                    if students.empty:

                        template = pd.DataFrame(
                            columns=[
                                "roll_number",
                                "name"
                            ]
                            + clo_codes
                        )

                    else:

                        template = students[
                            [
                                "roll_number",
                                "name"
                            ]
                        ].copy()

                        for clo in clo_codes:

                            template[clo] = ""

                    csv = template.to_csv(
                        index=False
                    ).encode(
                        "utf-8-sig"
                    )

                    st.download_button(
                        "📥 Download Marks Template",
                        csv,
                        "FAST_TUTOR_MARKS_TEMPLATE.csv",
                        "text/csv"
                    )

                    uploaded = st.file_uploader(
                        "Upload completed marks file",
                        type=[
                            "xlsx",
                            "xls",
                            "csv"
                        ],
                        key="marks_import_2"
                    )

                    if uploaded:

                        try:

                            data = read_file(
                                uploaded
                            )

                            data.columns = [
                                normalize_column(c)
                                for c in data.columns
                            ]

                            aliases = {
                                "roll_no": "roll_number",
                                "rollno": "roll_number",
                                "roll": "roll_number",
                                "student_id": "roll_number",
                                "studentid": "roll_number",
                                "student_name": "name",
                                "full_name": "name"
                            }

                            data = data.rename(
                                columns=aliases
                            )

                            missing = [
                                c
                                for c in [
                                    "roll_number"
                                ] + clo_codes
                                if c not in data.columns
                            ]

                            if missing:

                                st.error(
                                    "Missing columns: "
                                    + ", ".join(
                                        missing
                                    )
                                )

                            else:

                                data[clo_codes] = data[
                                    clo_codes
                                ].apply(
                                    pd.to_numeric,
                                    errors="coerce"
                                )

                                st.dataframe(
                                    data,
                                    use_container_width=True,
                                    hide_index=True
                                )

                                total_marks = {}

                                st.subheader(
                                    "Total marks for each CLO"
                                )

                                cols = st.columns(
                                    min(
                                        4,
                                        len(clo_codes)
                                    )
                                )

                                for i, clo in enumerate(
                                    clo_codes
                                ):

                                    with cols[
                                        i % len(cols)
                                    ]:

                                        total_marks[
                                            clo
                                        ] = st.number_input(
                                            f"{clo} Total",
                                            min_value=0.01,
                                            value=10.0,
                                            step=1.0,
                                            key=(
                                                f"tm_"
                                                f"{assessment_id}_"
                                                f"{clo}"
                                            )
                                        )

                                valid = True

                                for clo in clo_codes:

                                    if (
                                        data[clo]
                                        .dropna()
                                        < 0
                                    ).any():

                                        st.error(
                                            f"{clo} contains "
                                            "negative marks."
                                        )

                                        valid = False

                                    if (
                                        data[clo]
                                        .dropna()
                                        >
                                        total_marks[clo]
                                    ).any():

                                        st.error(
                                            f"{clo} contains marks "
                                            "greater than total."
                                        )

                                        valid = False

                                if valid:

                                    confirm = st.checkbox(
                                        "I confirm that the uploaded marks are correct."
                                    )

                                    if st.button(
                                        "🚀 IMPORT COMPLETE CLASS MARKS",
                                        type="primary",
                                        disabled=not confirm
                                    ):

                                        try:

                                            db.execute(
                                                "BEGIN"
                                            )

                                            students = students_df()

                                            student_lookup = {
                                                str(
                                                    row[
                                                        "roll_number"
                                                    ]
                                                ).strip():
                                                int(
                                                    row[
                                                        "id"
                                                    ]
                                                )
                                                for _, row
                                                in students.iterrows()
                                            }

                                            clo_lookup = {
                                                clean(
                                                    row[
                                                        "code"
                                                    ]
                                                ):
                                                int(
                                                    row[
                                                        "id"
                                                    ]
                                                )
                                                for _, row
                                                in course_clos.iterrows()
                                            }

                                            inserted = 0
                                            updated = 0

                                            for _, row in data.iterrows():

                                                roll = clean(
                                                    row[
                                                        "roll_number"
                                                    ]
                                                )

                                                if not roll:

                                                    continue

                                                if roll not in student_lookup:

                                                    raise ValueError(
                                                        f"Roll number "
                                                        f"{roll} is not "
                                                        f"registered."
                                                    )

                                                student_id = (
                                                    student_lookup[
                                                        roll
                                                    ]
                                                )

                                                for clo in clo_codes:

                                                    mark = row[
                                                        clo
                                                    ]

                                                    if pd.isna(
                                                        mark
                                                    ):

                                                        continue

                                                    obtained = float(
                                                        mark
                                                    )

                                                    total = float(
                                                        total_marks[
                                                            clo
                                                        ]
                                                    )

                                                    clo_id = (
                                                        clo_lookup[
                                                            clo
                                                        ]
                                                    )

                                                    existing = db.execute(
                                                        """
                                                        SELECT id
                                                        FROM results
                                                        WHERE
                                                            assessment_id = ?
                                                            AND student_id = ?
                                                            AND clo_id = ?
                                                        """,
                                                        (
                                                            assessment_id,
                                                            student_id,
                                                            clo_id
                                                        )
                                                    ).fetchone()

                                                    if existing:

                                                        db.execute(
                                                            """
                                                            UPDATE results
                                                            SET
                                                                marks_obtained = ?,
                                                                marks_total = ?
                                                            WHERE id = ?
                                                            """,
                                                            (
                                                                obtained,
                                                                total,
                                                                existing[0]
                                                            )
                                                        )

                                                        updated += 1

                                                    else:

                                                        db.execute(
                                                            """
                                                            INSERT INTO results
                                                            (
                                                                assessment_id,
                                                                student_id,
                                                                clo_id,
                                                                marks_obtained,
                                                                marks_total
                                                            )
                                                            VALUES (?, ?, ?, ?, ?)
                                                            """,
                                                            (
                                                                assessment_id,
                                                                student_id,
                                                                clo_id,
                                                                obtained,
                                                                total
                                                            )
                                                        )

                                                        inserted += 1

                                            db.commit()

                                            st.success(
                                                "🎉 FAST TUTOR: "
                                                "COMPLETE CLASS MARKS "
                                                "IMPORTED SUCCESSFULLY!"
                                            )

                                            a, b = st.columns(2)

                                            a.metric(
                                                "New Marks",
                                                inserted
                                            )

                                            b.metric(
                                                "Updated Marks",
                                                updated
                                            )

                                        except Exception as error:

                                            db.rollback()

                                            st.error(
                                                "Upload failed. "
                                                "No partial marks were saved."
                                            )

                                            st.exception(
                                                error
                                            )

                        except Exception as error:

                            st.error(
                                "Could not read the marks file."
                            )

                            st.exception(
                                error
                            )


# ============================================================
# EXPORT
# ============================================================

elif page == "📥 Import / Export":

    page_header(
        "Import / Export",
        "Export FAST TUTOR data"
    )

    import_tab, export_tab = st.tabs(
        [
            "📥 Import",
            "📤 Export"
        ]
    )

    with import_tab:

        st.info(
            "Use the dedicated Bulk Marks Upload menu "
            "for complete-class marks."
        )

        st.write(
            "Supported formats:"
        )

        st.write(
            "• Excel (.xlsx / .xls)"
        )

        st.write(
            "• CSV (.csv)"
        )

    with export_tab:

        export_type = st.selectbox(
            "Export",
            [
                "Students",
                "Programs",
                "PLOs",
                "Courses",
                "CLOs",
                "Mappings",
                "Results"
            ]
        )

        if export_type == "Students":

            data = students_df()

        elif export_type == "Programs":

            data = programs_df()

        elif export_type == "PLOs":

            data = plos_df()

        elif export_type == "Courses":

            data = courses_df()

        elif export_type == "CLOs":

            data = clos_df()

        elif export_type == "Mappings":

            data = fetch_df(
                """
                SELECT
                    courses.code AS Course,
                    clos.code AS CLO,
                    plos.code AS PLO,
                    mappings.strength AS Strength
                FROM mappings
                JOIN clos
                    ON mappings.clo_id = clos.id
                JOIN courses
                    ON clos.course_id = courses.id
                JOIN plos
                    ON mappings.plo_id = plos.id
                """
            )

        else:

            data = fetch_df(
                """
                SELECT
                    students.roll_number AS Roll_Number,
                    students.name AS Student_Name,
                    courses.code AS Course,
                    assessments.name AS Assessment,
                    clos.code AS CLO,
                    results.marks_obtained AS Marks,
                    results.marks_total AS Total
                FROM results
                JOIN students
                    ON results.student_id = students.id
                JOIN assessments
                    ON results.assessment_id = assessments.id
                JOIN courses
                    ON assessments.course_id = courses.id
                JOIN clos
                    ON results.clo_id = clos.id
                """
            )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

        csv = data.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        st.download_button(
            "📥 Download CSV",
            csv,
            f"FAST_TUTOR_{export_type}.csv",
            "text/csv"
        )

        excel = BytesIO()

        with pd.ExcelWriter(
            excel,
            engine="openpyxl"
        ) as writer:

            data.to_excel(
                writer,
                index=False,
                sheet_name="FAST TUTOR"
            )

        excel.seek(0)

        st.download_button(
            "📥 Download Excel",
            excel,
            f"FAST_TUTOR_{export_type}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ============================================================
# SETTINGS
# ============================================================

elif page == "⚙️ Settings":

    page_header(
        "FAST TUTOR Settings",
        "System configuration"
    )

    st.info(
        "Application: FAST TUTOR"
    )

    st.info(
        "Database: fast_tutor.db"
    )

    st.subheader(
        "Database Statistics"
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "Programs",
        len(programs_df())
    )

    b.metric(
        "Courses",
        len(courses_df())
    )

    c.metric(
        "Students",
        len(students_df())
    )

    d.metric(
        "CLOs",
        len(clos_df())
    )

    st.divider()

    st.warning(
        "The reset option permanently deletes ALL "
        "FAST TUTOR data."
    )

    confirm = st.checkbox(
        "I understand that this will delete all data."
    )

    if st.button(
        "🗑️ DELETE ALL FAST TUTOR DATA",
        disabled=not confirm
    ):

        try:

            db.execute(
                "BEGIN"
            )

            tables = [
                "results",
                "assessments",
                "mappings",
                "clos",
                "students",
                "courses",
                "plos",
                "programs"
            ]

            for table in tables:

                db.execute(
                    f"DELETE FROM {table}"
                )

            db.commit()

            st.success(
                "All FAST TUTOR data has been deleted."
            )

            st.rerun()

        except Exception as error:

            db.rollback()

            st.error(
                "Unable to reset the database."
            )

            st.exception(
                error
            )
