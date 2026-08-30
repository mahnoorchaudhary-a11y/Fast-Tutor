import sqlite3
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import plotly.express as px

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer
    )
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# ============================================================
# FAST TUTOR
# CLO-PLO MAPPING MANAGEMENT SYSTEM
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

DB_FILE = "fast_tutor.db"


@st.cache_resource
def get_connection():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False,
        timeout=30
    )


conn = get_connection()


def execute(query, params=()):
    cur = conn.cursor()

    try:
        cur.execute(query, params)
        conn.commit()
        return cur

    except sqlite3.Error:
        conn.rollback()
        raise


def query_df(query, params=()):
    return pd.read_sql_query(
        query,
        conn,
        params=params
    )


def initialize_database():

    execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            department TEXT,
            created_at TEXT
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS plos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            plo_code TEXT NOT NULL,
            name TEXT,
            description TEXT,
            created_at TEXT,
            UNIQUE(program_id, plo_code)
        )
    """)

    execute("""
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
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS clos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            clo_code TEXT NOT NULL,
            description TEXT,
            bloom_level TEXT,
            assessment TEXT,
            target REAL DEFAULT 70,
            created_at TEXT,
            UNIQUE(course_id, clo_code)
        )
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clo_id INTEGER NOT NULL,
            plo_id INTEGER NOT NULL,
            strength INTEGER NOT NULL DEFAULT 0,
            UNIQUE(clo_id, plo_id)
        )
    """)

    execute("""
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
    """)

    execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            assessment_type TEXT,
            total_marks REAL DEFAULT 100,
            assessment_date TEXT,
            created_at TEXT
        )
    """)

    execute("""
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
    """)


initialize_database()


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


def normalize_column(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
    )


def read_uploaded_file(uploaded):

    if uploaded.name.lower().endswith(".csv"):
        return pd.read_csv(
            uploaded,
            dtype=str
        )

    return pd.read_excel(
        uploaded,
        dtype=str
    )


def get_programs():

    return query_df("""
        SELECT *
        FROM programs
        ORDER BY code
    """)


def get_plos():

    return query_df("""
        SELECT
            plos.*,
            programs.code AS program_code,
            programs.name AS program_name
        FROM plos
        LEFT JOIN programs
            ON plos.program_id = programs.id
        ORDER BY
            programs.code,
            plos.plo_code
    """)


def get_courses():

    return query_df("""
        SELECT
            courses.*,
            programs.code AS program_code,
            programs.name AS program_name
        FROM courses
        LEFT JOIN programs
            ON courses.program_id = programs.id
        ORDER BY
            programs.code,
            courses.code
    """)


def get_clos():

    return query_df("""
        SELECT
            clos.*,
            courses.code AS course_code,
            courses.name AS course_name
        FROM clos
        LEFT JOIN courses
            ON clos.course_id = courses.id
        ORDER BY
            courses.code,
            clos.clo_code
    """)


def get_students():

    return query_df("""
        SELECT
            students.*,
            programs.code AS program_code
        FROM students
        LEFT JOIN programs
            ON students.program_id = programs.id
        ORDER BY students.roll_number
    """)


def get_assessments():

    return query_df("""
        SELECT
            assessments.*,
            courses.code AS course_code,
            courses.name AS course_name
        FROM assessments
        LEFT JOIN courses
            ON assessments.course_id = courses.id
        ORDER BY
            assessments.assessment_date DESC,
            assessments.id DESC
    """)


def program_options():

    df = get_programs()

    return {
        f"{r['code']} — {r['name']}": int(r["id"])
        for _, r in df.iterrows()
    }


def course_options():

    df = get_courses()

    return {
        f"{r['code']} — {r['name']}": int(r["id"])
        for _, r in df.iterrows()
    }


def student_options():

    df = get_students()

    return {
        f"{r['roll_number']} — {r['name']}": int(r["id"])
        for _, r in df.iterrows()
    }


def assessment_options():

    df = get_assessments()

    return {
        f"{r['course_code']} | {r['name']} | {r['assessment_date']}":
        int(r["id"])
        for _, r in df.iterrows()
    }


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎓 Fast Tutor")

st.sidebar.caption(
    "CLO–PLO Mapping & Outcome Assessment System"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🏫 Programs",
        "🎯 PLO Management",
        "📚 Course Management",
        "🎯 CLO Management",
        "🔗 CLO–PLO Mapping",
        "📊 PLO Attainment",
        "📑 Reports",
        "📤 Import / Export",
        "⚙️ Settings"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.title("🎓 Fast Tutor")
    st.subheader(
        "CLO–PLO Mapping Management System"
    )

    programs = get_programs()
    plos = get_plos()
    courses = get_courses()
    clos = get_clos()
    students = get_students()
    assessments = get_assessments()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Programs",
        len(programs)
    )

    c2.metric(
        "Courses",
        len(courses)
    )

    c3.metric(
        "CLOs",
        len(clos)
    )

    c4.metric(
        "PLOs",
        len(plos)
    )

    st.divider()

    if plos.empty:

        st.info(
            "Add Programs, PLOs, Courses and CLOs "
            "to start building your mapping."
        )

    else:

        mappings = query_df("""
            SELECT
                mappings.*,
                plos.plo_code,
                clos.clo_code
            FROM mappings
            JOIN plos
                ON mappings.plo_id = plos.id
            JOIN clos
                ON mappings.clo_id = clos.id
        """)

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "📊 PLO Coverage"
            )

            coverage = []

            for _, plo in plos.iterrows():

                count = 0

                if not mappings.empty:

                    count = len(
                        mappings[
                            (
                                mappings["plo_id"]
                                ==
                                plo["id"]
                            )
                            &
                            (
                                mappings["strength"]
                                > 0
                            )
                        ]
                    )

                coverage.append(
                    {
                        "PLO": plo["plo_code"],
                        "Mapped CLOs": count
                    }
                )

            coverage_df = pd.DataFrame(
                coverage
            )

            if not coverage_df.empty:

                fig = px.bar(
                    coverage_df,
                    x="PLO",
                    y="Mapped CLOs",
                    title="CLO Coverage per PLO"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

        with col2:

            st.subheader(
                "🔗 Mapping Strength"
            )

            if mappings.empty:

                st.info(
                    "No mappings created yet."
                )

            else:

                strength_df = (
                    mappings
                    .groupby("strength")
                    .size()
                    .reset_index(
                        name="Mappings"
                    )
                )

                strength_df["Level"] = (
                    strength_df["strength"]
                    .map(
                        {
                            0: "None",
                            1: "Low",
                            2: "Medium",
                            3: "High"
                        }
                    )
                )

                fig = px.bar(
                    strength_df,
                    x="Level",
                    y="Mappings",
                    title="CLO–PLO Mapping Strength"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

    st.subheader(
        "📌 System Summary"
    )

    a, b, c = st.columns(3)

    a.metric(
        "Students",
        len(students)
    )

    b.metric(
        "Assessments",
        len(assessments)
    )

    if not plos.empty:

        unmapped = 0

        mappings = query_df("""
            SELECT *
            FROM mappings
            WHERE strength > 0
        """)

        for _, plo in plos.iterrows():

            if mappings.empty:

                unmapped += 1

            elif not (
                mappings["plo_id"]
                == plo["id"]
            ).any():

                unmapped += 1

        c.metric(
            "Unmapped PLOs",
            unmapped
        )

    else:

        c.metric(
            "Unmapped PLOs",
            0
        )


# ============================================================
# PROGRAMS
# ============================================================

elif page == "🏫 Programs":

    st.title("🏫 Programs")

    tab1, tab2 = st.tabs(
        [
            "➕ Add Program",
            "📋 Program List"
        ]
    )

    with tab1:

        with st.form("add_program"):

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
                placeholder="Computer Science"
            )

            submitted = st.form_submit_button(
                "Save Program"
            )

            if submitted:

                if not code.strip() or not name.strip():

                    st.error(
                        "Program code and name are required."
                    )

                else:

                    try:

                        execute(
                            """
                            INSERT INTO programs
                            (code, name, department, created_at)
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
                            "This program code already exists."
                        )

    with tab2:

        st.dataframe(
            get_programs(),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# PLO MANAGEMENT
# ============================================================

elif page == "🎯 PLO Management":

    st.title("🎯 PLO Management")

    programs = program_options()

    if not programs:

        st.warning(
            "Create a program first."
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

            plo_code = st.text_input(
                "PLO Code",
                placeholder="PLO1"
            )

            plo_name = st.text_input(
                "PLO Name",
                placeholder="Knowledge of Computing"
            )

            description = st.text_area(
                "Description"
            )

            if st.button(
                "Save PLO",
                type="primary"
            ):

                if not plo_code.strip():

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
                                plo_code,
                                name,
                                description,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                programs[program],
                                plo_code.strip(),
                                plo_name.strip(),
                                description.strip(),
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "PLO saved successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This PLO already exists for this program."
                        )

        with tab2:

            st.dataframe(
                get_plos(),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# COURSE MANAGEMENT
# ============================================================

elif page == "📚 Course Management":

    st.title("📚 Course Management")

    programs = program_options()

    if not programs:

        st.warning(
            "Create a program first."
        )

    else:

        tab1, tab2 = st.tabs(
            [
                "➕ Add Course",
                "📋 Course List"
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
                    min_value=0.5,
                    max_value=10.0,
                    value=3.0,
                    step=0.5
                )

            with col2:

                semester = st.number_input(
                    "Semester",
                    min_value=1,
                    max_value=12,
                    value=1,
                    step=1
                )

            if st.button(
                "Save Course",
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
                            "Course saved successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This course already exists."
                        )

        with tab2:

            st.dataframe(
                get_courses(),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# CLO MANAGEMENT
# ============================================================

elif page == "🎯 CLO Management":

    st.title("🎯 CLO Management")

    courses = course_options()

    if not courses:

        st.warning(
            "Create a course first."
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

            clo_code = st.text_input(
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
                min_value=0.0,
                max_value=100.0,
                value=70.0,
                step=1.0
            )

            if st.button(
                "Save CLO",
                type="primary"
            ):

                if not clo_code.strip():

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
                                clo_code,
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
                                clo_code.strip(),
                                description.strip(),
                                bloom,
                                assessment.strip(),
                                target,
                                datetime.now().isoformat()
                            )
                        )

                        st.success(
                            "CLO saved successfully."
                        )

                        st.rerun()

                    except sqlite3.IntegrityError:

                        st.error(
                            "This CLO already exists for this course."
                        )

        with tab2:

            st.dataframe(
                get_clos(),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# CLO-PLO MAPPING
# ============================================================

elif page == "🔗 CLO–PLO Mapping":

    st.title("🔗 CLO–PLO Mapping")

    programs = get_programs()
    courses = get_courses()
    clos = get_clos()
    plos = get_plos()

    if clos.empty or plos.empty:

        st.warning(
            "You need both CLOs and PLOs before creating mappings."
        )

    else:

        st.info(
            "Mapping scale: 0 = No Mapping, "
            "1 = Low, 2 = Medium, 3 = High"
        )

        selected_course = st.selectbox(
            "Select Course",
            [
                f"{r['code']} — {r['name']}"
                for _, r in courses.iterrows()
            ]
        )

        course_code = selected_course.split(
            " — "
        )[0]

        course_id = int(
            courses[
                courses["code"] == course_code
            ].iloc[0]["id"]
        )

        course_clos = clos[
            clos["course_id"] == course_id
        ]

        if course_clos.empty:

            st.warning(
                "This course has no CLOs."
            )

        else:

            program_ids = courses[
                courses["id"] == course_id
            ]["program_id"].tolist()

            if program_ids:

                program_id = program_ids[0]

                program_plos = plos[
                    plos["program_id"] == program_id
                ]

            else:

                program_plos = plos

            if program_plos.empty:

                st.warning(
                    "No PLOs exist for this program."
                )

            else:

                st.subheader(
                    "CLO–PLO Matrix"
                )

                matrix_data = []

                for _, clo in course_clos.iterrows():

                    row = {
                        "CLO": clo["clo_code"]
                    }

                    for _, plo in program_plos.iterrows():

                        existing = query_df(
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

                            strength = 0

                        else:

                            strength = int(
                                existing.iloc[0][
                                    "strength"
                                ]
                            )

                        row[
                            plo["plo_code"]
                        ] = strength

                    matrix_data.append(row)

                matrix_df = pd.DataFrame(
                    matrix_data
                )

                st.dataframe(
                    matrix_df,
                    use_container_width=True,
                    hide_index=True
                )

                st.subheader(
                    "✏️ Edit Mapping"
                )

                for _, clo in course_clos.iterrows():

                    st.markdown(
                        f"### {clo['clo_code']}"
                    )

                    cols = st.columns(
                        len(program_plos)
                    )

                    for i, (_, plo) in enumerate(
                        program_plos.iterrows()
                    ):

                        existing = query_df(
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
                                existing.iloc[0][
                                    "strength"
                                ]
                            )

                        with cols[i]:

                            value = st.selectbox(
                                plo["plo_code"],
                                [0, 1, 2, 3],
                                index=current,
                                key=(
                                    f"map_"
                                    f"{clo['id']}_"
                                    f"{plo['id']}"
                                )
                            )

                            if st.button(
                                f"Save {clo['clo_code']} → {plo['plo_code']}",
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
                                        strength = excluded.strength
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
# PLO ATTAINMENT
# ============================================================

elif page == "📊 PLO Attainment":

    st.title("📊 PLO Attainment")

    results = query_df(
        """
        SELECT
            results.id,
            results.assessment_id,
            results.student_id,
            results.clo_id,
            results.marks_obtained,
            results.marks_total,
            students.roll_number,
            students.name AS student_name,
            clos.clo_code,
            clos.target,
            courses.code AS course_code,
            assessments.name AS assessment_name
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

    mappings = query_df(
        """
        SELECT
            mappings.*,
            plos.id AS plo_id,
            plos.plo_code,
            clos.clo_code
        FROM mappings
        JOIN plos
            ON mappings.plo_id = plos.id
        JOIN clos
            ON mappings.clo_id = clos.id
        WHERE mappings.strength > 0
        """
    )

    if results.empty:

        st.info(
            "No student results have been uploaded yet."
        )

    elif mappings.empty:

        st.warning(
            "Create CLO–PLO mappings first."
        )

    else:

        results["clo_percentage"] = (
            results["marks_obtained"]
            /
            results["marks_total"]
            *
            100
        )

        plo_rows = []

        for _, mapping in mappings.iterrows():

            clo_code = mapping["clo_code"]
            plo_code = mapping["plo_code"]
            strength = float(
                mapping["strength"]
            )

            clo_results = results[
                results["clo_code"]
                == clo_code
            ]

            if clo_results.empty:

                continue

            average = (
                clo_results[
                    "clo_percentage"
                ].mean()
            )

            weighted = average * (
                strength / 3.0
            )

            plo_rows.append(
                {
                    "PLO": plo_code,
                    "CLO": clo_code,
                    "Mapping Strength": strength,
                    "CLO Attainment (%)": round(
                        average,
                        2
                    ),
                    "Weighted Contribution (%)": round(
                        weighted,
                        2
                    )
                }
            )

        contribution_df = pd.DataFrame(
            plo_rows
        )

        if contribution_df.empty:

            st.warning(
                "No attainment could be calculated."
            )

        else:

            summary = (
                contribution_df
                .groupby("PLO")
                .agg(
                    Contributions=(
                        "Weighted Contribution (%)",
                        "mean"
                    ),
                    CLOs=(
                        "CLO",
                        "count"
                    )
                )
                .reset_index()
            )

            summary[
                "PLO Attainment (%)"
            ] = summary[
                "Contributions"
            ].round(2)

            summary[
                "Status"
            ] = summary[
                "PLO Attainment (%)"
            ].apply(
                lambda x:
                "🟢 Strong"
                if x >= 70
                else
                "🟠 Needs Improvement"
                if x >= 50
                else
                "🔴 Weak"
            )

            st.subheader(
                "PLO Attainment"
            )

            st.dataframe(
                summary[
                    [
                        "PLO",
                        "CLOs",
                        "PLO Attainment (%)",
                        "Status"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            fig = px.bar(
                summary,
                x="PLO",
                y="PLO Attainment (%)",
                text_auto=".1f",
                range_y=[0, 100],
                title="PLO Attainment (%)"
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

            weak = summary[
                summary[
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

    st.title("📑 Reports")

    report_type = st.selectbox(
        "Select Report",
        [
            "CLO–PLO Matrix",
            "Course-wise Mapping",
            "Program-wide Mapping",
            "PLO Coverage",
            "PLO Attainment",
            "Weak PLO Report",
            "Student Results"
        ]
    )

    if report_type == "CLO–PLO Matrix":

        data = query_df(
            """
            SELECT
                courses.code AS course,
                clos.clo_code AS clo,
                plos.plo_code AS plo,
                mappings.strength
            FROM mappings
            JOIN clos
                ON mappings.clo_id = clos.id
            JOIN courses
                ON clos.course_id = courses.id
            JOIN plos
                ON mappings.plo_id = plos.id
            ORDER BY
                courses.code,
                clos.clo_code,
                plos.plo_code
            """
        )

        if data.empty:

            st.info(
                "No mappings available."
            )

        else:

            matrix = data.pivot_table(
                index=["course", "clo"],
                columns="plo",
                values="strength",
                fill_value=0
            ).reset_index()

            st.dataframe(
                matrix,
                use_container_width=True,
                hide_index=True
            )

    elif report_type == "Course-wise Mapping":

        data = query_df(
            """
            SELECT
                courses.code AS course_code,
                courses.name AS course_name,
                clos.clo_code,
                plos.plo_code,
                mappings.strength
            FROM mappings
            JOIN clos
                ON mappings.clo_id = clos.id
            JOIN courses
                ON clos.course_id = courses.id
            JOIN plos
                ON mappings.plo_id = plos.id
            ORDER BY
                courses.code,
                clos.clo_code
            """
        )

        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )

    elif report_type == "Program-wide Mapping":

        data = query_df(
            """
            SELECT
                programs.code AS program,
                courses.code AS course,
                clos.clo_code,
                plos.plo_code,
                mappings.strength
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

    elif report_type == "PLO Coverage":

        plos = get_plos()

        rows = []

        for _, plo in plos.iterrows():

            count = query_df(
                """
                SELECT COUNT(*) AS total
                FROM mappings
                WHERE
                    plo_id = ?
                    AND strength > 0
                """,
                (int(plo["id"]),)
            ).iloc[0]["total"]

            rows.append(
                {
                    "PLO": plo["plo_code"],
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

    elif report_type == "PLO Attainment":

        results = query_df(
            """
            SELECT
                clos.clo_code,
                results.marks_obtained,
                results.marks_total
            FROM results
            JOIN clos
                ON results.clo_id = clos.id
            """
        )

        mappings = query_df(
            """
            SELECT
                plos.plo_code,
                clos.clo_code,
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
                "Not enough data for attainment."
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

            for plo in mappings[
                "plo_code"
            ].unique():

                mappings_for_plo = mappings[
                    mappings["plo_code"] == plo
                ]

                values = []

                for _, mapping in (
                    mappings_for_plo.iterrows()
                ):

                    clo = mapping["clo_code"]
                    strength = mapping["strength"]

                    r = results[
                        results["clo_code"] == clo
                    ]

                    if not r.empty:

                        avg = r[
                            "percentage"
                        ].mean()

                        values.append(
                            avg *
                            (
                                strength / 3
                            )
                        )

                if values:

                    rows.append(
                        {
                            "PLO": plo,
                            "Attainment (%)":
                            round(
                                sum(values) /
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

    elif report_type == "Weak PLO Report":

        plos = get_plos()

        mappings = query_df(
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
                        "PLO": plo["plo_code"],
                        "Name": plo["name"],
                        "Issue": "Unmapped"
                    }
                )

        data = pd.DataFrame(rows)

        if data.empty:

            st.success(
                "No unmapped PLOs."
            )

        else:

            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True
            )

    elif report_type == "Student Results":

        data = query_df(
            """
            SELECT
                students.roll_number,
                students.name,
                courses.code AS course,
                assessments.name AS assessment,
                clos.clo_code,
                results.marks_obtained,
                results.marks_total
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

        if data.empty:

            st.info(
                "No student results available."
            )

        else:

            data["percentage"] = (
                data["marks_obtained"]
                /
                data["marks_total"]
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
                "📥 Download Excel-compatible CSV",
                csv,
                "Fast_Tutor_Student_Results.csv",
                "text/csv"
            )


# ============================================================
# IMPORT / EXPORT
# ============================================================

elif page == "📤 Import / Export":

    st.title("📤 Import / Export")

    import_tab, export_tab = st.tabs(
        [
            "📥 Import",
            "📤 Export"
        ]
    )

    # ========================================================
    # IMPORT
    # ========================================================

    with import_tab:

        import_type = st.selectbox(
            "What do you want to import?",
            [
                "Students",
                "Student Results / Marks"
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
                "Upload a complete class list instead of "
                "entering students one by one."
            )

            student_template = pd.DataFrame(
                columns=[
                    "roll_number",
                    "name",
                    "email",
                    "section",
                    "semester"
                ]
            )

            student_template.loc[0] = [
                "2026-CS-001",
                "Ali Khan",
                "ali@example.com",
                "A",
                "1"
            ]

            student_csv = (
                student_template
                .to_csv(index=False)
                .encode("utf-8-sig")
            )

            st.download_button(
                "📥 Download Student Template",
                student_csv,
                "Fast_Tutor_Student_Template.csv",
                "text/csv"
            )

            programs = program_options()

            selected_program = None

            if programs:

                selected_program = st.selectbox(
                    "Assign all imported students to program",
                    list(programs.keys())
                )

            uploaded = st.file_uploader(
                "Upload Student Excel / CSV",
                type=[
                    "xlsx",
                    "xls",
                    "csv"
                ],
                key="student_import"
            )

            if uploaded is not None:

                try:

                    df = read_uploaded_file(
                        uploaded
                    )

                    df.columns = [
                        normalize_column(c)
                        for c in df.columns
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

                    df = df.rename(
                        columns=aliases
                    )

                    required = [
                        "roll_number",
                        "name"
                    ]

                    missing = [
                        c
                        for c in required
                        if c not in df.columns
                    ]

                    if missing:

                        st.error(
                            "Missing required columns: "
                            + ", ".join(missing)
                        )

                    else:

                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True
                        )

                        if st.button(
                            "🚀 Import Students",
                            type="primary"
                        ):

                            inserted = 0
                            updated = 0

                            try:

                                conn.execute(
                                    "BEGIN"
                                )

                                program_id = None

                                if selected_program:

                                    program_id = programs[
                                        selected_program
                                    ]

                                for _, row in df.iterrows():

                                    roll = clean(
                                        row[
                                            "roll_number"
                                        ]
                                    )

                                    name = clean(
                                        row[
                                            "name"
                                        ]
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

                                    existing = conn.execute(
                                        """
                                        SELECT id
                                        FROM students
                                        WHERE roll_number = ?
                                        """,
                                        (roll,)
                                    ).fetchone()

                                    if existing:

                                        conn.execute(
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

                                        conn.execute(
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

                                conn.commit()

                                st.success(
                                    "🎉 Students imported successfully!"
                                )

                                c1, c2 = st.columns(2)

                                c1.metric(
                                    "New Students",
                                    inserted
                                )

                                c2.metric(
                                    "Updated Students",
                                    updated
                                )

                            except Exception as error:

                                conn.rollback()

                                st.error(
                                    "Student import failed."
                                )

                                st.exception(
                                    error
                                )

                except Exception as error:

                    st.error(
                        "Could not read the student file."
                    )

                    st.exception(
                        error
                    )

        # ====================================================
        # RESULT IMPORT
        # ====================================================

        else:

            st.subheader(
                "📊 Bulk Student Marks Import"
            )

            st.success(
                "This is the main marks-entry method. "
                "You can upload the complete class results "
                "in one Excel/CSV file."
            )

            assessments = get_assessments()

            if assessments.empty:

                st.warning(
                    "Create an assessment first."
                )

            else:

                assessment_map = assessment_options()

                selected_assessment = st.selectbox(
                    "Select Assessment",
                    list(
                        assessment_map.keys()
                    ),
                    key="bulk_result_assessment"
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

                course_clos = get_clos()

                course_clos = course_clos[
                    course_clos["course_id"]
                    == course_id
                ]

                if course_clos.empty:

                    st.warning(
                        "Create CLOs for this course first."
                    )

                else:

                    clo_codes = [
                        clean(x)
                        for x in course_clos[
                            "clo_code"
                        ]
                    ]

                    st.write(
                        "### Required file structure"
                    )

                    st.code(
                        "roll_number | name | "
                        + " | ".join(
                            clo_codes
                        )
                    )

                    template = pd.DataFrame(
                        columns=[
                            "roll_number",
                            "name"
                        ]
                        + clo_codes
                    )

                    students = get_students()

                    if not students.empty:

                        template = students[
                            [
                                "roll_number",
                                "name"
                            ]
                        ].copy()

                        for clo in clo_codes:

                            template[clo] = ""

                    template_csv = (
                        template
                        .to_csv(
                            index=False
                        )
                        .encode(
                            "utf-8-sig"
                        )
                    )

                    st.download_button(
                        "📥 Download Marks Template",
                        template_csv,
                        "Fast_Tutor_Marks_Template.csv",
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
                            sheet_name="Marks"
                        )

                    excel_buffer.seek(0)

                    st.download_button(
                        "📥 Download Excel Marks Template",
                        excel_buffer,
                        "Fast_Tutor_Marks_Template.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    uploaded = st.file_uploader(
                        "Upload completed marks file",
                        type=[
                            "xlsx",
                            "xls",
                            "csv"
                        ],
                        key="result_import"
                    )

                    if uploaded is not None:

                        try:

                            df = read_uploaded_file(
                                uploaded
                            )

                            df.columns = [
                                normalize_column(c)
                                for c in df.columns
                            ]

                            aliases = {
                                "roll_no": "roll_number",
                                "rollno": "roll_number",
                                "roll": "roll_number",
                                "student_id": "roll_number",
                                "studentid": "roll_number",
                                "student_name": "name",
                                "full_name": "name",
                                "student": "name"
                            }

                            df = df.rename(
                                columns=aliases
                            )

                            if (
                                "roll_number"
                                not in df.columns
                            ):

                                st.error(
                                    "The marks file must contain "
                                    "a roll_number column."
                                )

                            else:

                                missing_clos = [
                                    clo
                                    for clo in clo_codes
                                    if clo not in df.columns
                                ]

                                if missing_clos:

                                    st.error(
                                        "Missing CLO columns: "
                                        + ", ".join(
                                            missing_clos
                                        )
                                    )

                                else:

                                    students = get_students()

                                    registered = set(
                                        students[
                                            "roll_number"
                                        ]
                                        .astype(str)
                                        .str.strip()
                                    )

                                    unknown = []

                                    for roll in df[
                                        "roll_number"
                                    ]:

                                        roll = str(
                                            roll
                                        ).strip()

                                        if (
                                            roll
                                            and
                                            roll not in registered
                                        ):

                                            unknown.append(
                                                roll
                                            )

                                    if unknown:

                                        st.error(
                                            "These roll numbers "
                                            "are not registered:"
                                        )

                                        st.write(
                                            ", ".join(
                                                unknown
                                            )
                                        )

                                    else:

                                        for clo in clo_codes:

                                            df[clo] = (
                                                pd.to_numeric(
                                                    df[clo],
                                                    errors="coerce"
                                                )
                                            )

                                        st.subheader(
                                            "👀 Marks Preview"
                                        )

                                        st.dataframe(
                                            df,
                                            use_container_width=True,
                                            hide_index=True
                                        )

                                        total_cols = st.columns(
                                            min(
                                                4,
                                                len(clo_codes)
                                            )
                                        )

                                        totals = {}

                                        for i, clo in enumerate(
                                            clo_codes
                                        ):

                                            with total_cols[
                                                i % len(
                                                    total_cols
                                                )
                                            ]:

                                                totals[
                                                    clo
                                                ] = st.number_input(
                                                    f"{clo} Total Marks",
                                                    min_value=0.01,
                                                    value=10.0,
                                                    step=1.0,
                                                    key=(
                                                        f"bulk_total_"
                                                        f"{assessment_id}_"
                                                        f"{clo}"
                                                    )
                                                )

                                        errors = []

                                        for clo in clo_codes:

                                            if (
                                                df[clo]
                                                .dropna()
                                                < 0
                                            ).any():

                                                errors.append(
                                                    f"{clo}: negative marks found."
                                                )

                                            if (
                                                df[clo]
                                                .dropna()
                                                > totals[clo]
                                            ).any():

                                                errors.append(
                                                    f"{clo}: marks exceed "
                                                    f"total marks."
                                                )

                                        if errors:

                                            st.error(
                                                "Please correct:"
                                            )

                                            for error in errors:

                                                st.write(
                                                    "• "
                                                    + error
                                                )

                                        else:

                                            confirm = st.checkbox(
                                                "I confirm that these "
                                                "are the final student marks."
                                            )

                                            if st.button(
                                                "🚀 IMPORT ALL MARKS",
                                                type="primary",
                                                disabled=not confirm
                                            ):

                                                inserted = 0
                                                updated = 0

                                                try:

                                                    conn.execute(
                                                        "BEGIN"
                                                    )

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
                                                                "clo_code"
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

                                                    for _, row in df.iterrows():

                                                        roll = clean(
                                                            row[
                                                                "roll_number"
                                                            ]
                                                        )

                                                        student_db_id = (
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
                                                                totals[
                                                                    clo
                                                                ]
                                                            )

                                                            clo_id = (
                                                                clo_lookup[
                                                                    clo
                                                                ]
                                                            )

                                                            existing = conn.execute(
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
                                                                    student_db_id,
                                                                    clo_id
                                                                )
                                                            ).fetchone()

                                                            if existing:

                                                                conn.execute(
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

                                                                conn.execute(
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
                                                                        student_db_id,
                                                                        clo_id,
                                                                        obtained,
                                                                        total
                                                                    )
                                                                )

                                                                inserted += 1

                                                    conn.commit()

                                                    st.success(
                                                        "🎉 ALL MARKS "
                                                        "IMPORTED SUCCESSFULLY!"
                                                    )

                                                    c1, c2 = st.columns(2)

                                                    c1.metric(
                                                        "New Marks",
                                                        inserted
                                                    )

                                                    c2.metric(
                                                        "Updated Marks",
                                                        updated
                                                    )

                                                except Exception as error:

                                                    conn.rollback()

                                                    st.error(
                                                        "Marks import failed. "
                                                        "No partial data was saved."
                                                    )

                                                    st.exception(
                                                        error
                                                    )

                        except Exception as error:

                            st.error(
                                "Could not read the uploaded file."
                            )

                            st.exception(
                                error
                            )

    # ========================================================
    # EXPORT
    # ========================================================

    with export_tab:

        st.subheader(
            "📤 Export Data"
        )

        export_type = st.selectbox(
            "Select data",
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

            data = get_students()

        elif export_type == "Programs":

            data = get_programs()

        elif export_type == "PLOs":

            data = get_plos()

        elif export_type == "Courses":

            data = get_courses()

        elif export_type == "CLOs":

            data = get_clos()

        elif export_type == "Mappings":

            data = query_df(
                """
                SELECT
                    courses.code AS course,
                    clos.clo_code,
                    plos.plo_code,
                    mappings.strength
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

            data = query_df(
                """
                SELECT
                    students.roll_number,
                    students.name,
                    courses.code AS course,
                    assessments.name AS assessment,
                    clos.clo_code,
                    results.marks_obtained,
                    results.marks_total
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

        csv_data = (
            data
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            "📥 Download CSV",
            csv_data,
            f"Fast_Tutor_{export_type.replace(' ', '_')}.csv",
            "text/csv"
        )

        excel_buffer = BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl"
        ) as writer:

            data.to_excel(
                writer,
                index=False,
                sheet_name="Data"
            )

        excel_buffer.seek(0)

        st.download_button(
            "📥 Download Excel",
            excel_buffer,
            f"Fast_Tutor_{export_type.replace(' ', '_')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ============================================================
# SETTINGS
# ============================================================

elif page == "⚙️ Settings":

    st.title("⚙️ Settings")

    st.subheader(
        "Fast Tutor"
    )

    st.write(
        "CLO–PLO Mapping Management System"
    )

    st.info(
        "Database file: fast_tutor.db"
    )

    st.warning(
        "The reset option permanently deletes all "
        "programs, PLOs, courses, CLOs, mappings, "
        "students, assessments and results."
    )

    if st.button(
        "🗑️ Delete All Data",
        type="secondary"
    ):

        confirm = st.checkbox(
            "I understand that this permanently deletes all data."
        )

        if confirm:

            if st.button(
                "⚠️ CONFIRM DELETE EVERYTHING",
                type="primary"
            ):

                tables = [
                    "results",
                    "assessments",
                    "students",
                    "mappings",
                    "clos",
                    "courses",
                    "plos",
                    "programs"
                ]

                try:

                    conn.execute(
                        "BEGIN"
                    )

                    for table in tables:

                        conn.execute(
                            f"DELETE FROM {table}"
                        )

                    conn.commit()

                    st.success(
                        "All data has been deleted."
                    )

                    st.rerun()

                except Exception as error:

                    conn.rollback()

                    st.error(
                        "Could not delete data."
                    )

                    st.exception(
                        error
                    )
