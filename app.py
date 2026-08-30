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
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DATABASE
# ============================================================

DB_FILE = "fast_tutor.db"
LOGO_FILE = "fast_tutor_logo.png"


@st.cache_resource
def get_connection():
    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


conn = get_connection()


def execute(query, params=(), fetch=False):
    try:
        cur = conn.cursor()
        cur.execute(query, params)

        if fetch:
            return cur.fetchall()

        conn.commit()
        return True

    except sqlite3.Error as e:
        conn.rollback()
        st.error("Database error: " + str(e))
        return False


# ============================================================
# DATABASE TABLES
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
# CSS
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
}

.fast-title {
    font-size: 44px;
    font-weight: 900;
    color: #0795D1;
}

.fast-subtitle {
    color: #6B7280;
    font-size: 18px;
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
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGO
# ============================================================

def show_logo():

    if os.path.exists(LOGO_FILE):

        st.image(
            LOGO_FILE,
            width=210
        )

    else:

        st.markdown("""
        <div style="text-align:center;padding:10px">

            <div style="
                font-size:30px;
                font-weight:900;
                color:#0795D1;
                letter-spacing:2px;
            ">
                FAST TUTOR
            </div>

            <div style="
                font-size:12px;
                color:#777;
            ">
                Student Performance System
            </div>

        </div>
        """, unsafe_allow_html=True)


# ============================================================
# DATAFRAME FUNCTIONS
# ============================================================

def get_courses():

    rows = execute("""
        SELECT
            course_code,
            course_name,
            credit_hours,
            semester
        FROM courses
        ORDER BY course_code
    """, fetch=True)

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

    rows = execute("""
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


def get_clos():

    rows = execute("""
        SELECT
            course_code,
            clo_code,
            description,
            bloom_level
        FROM clos
        ORDER BY course_code, clo_code
    """, fetch=True)

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

    rows = execute("""
        SELECT
            plo_code,
            description
        FROM plos
        ORDER BY plo_code
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "PLO",
            "Description"
        ]
    )


def get_mappings():

    rows = execute("""
        SELECT
            course_code,
            clo_code,
            plo_code,
            strength
        FROM mappings
        ORDER BY course_code, clo_code, plo_code
    """, fetch=True)

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

    rows = execute("""
        SELECT
            r.roll_no,
            s.student_name,
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
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
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
    )


# ============================================================
# GRADE
# ============================================================

def grade_from_percentage(value):

    if value >= 90:
        return "A+"
    elif value >= 85:
        return "A"
    elif value >= 80:
        return "A-"
    elif value >= 75:
        return "B+"
    elif value >= 70:
        return "B"
    elif value >= 65:
        return "B-"
    elif value >= 60:
        return "C+"
    elif value >= 55:
        return "C"
    elif value >= 50:
        return "C-"
    elif value >= 45:
        return "D"
    else:
        return "F"


# ============================================================
# COLUMN DETECTOR
# ============================================================

def find_column(df, possible):

    for col in df.columns:

        normalized = (
            str(col)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        if normalized in possible:
            return col

    return None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    show_logo()

    st.markdown("""
    <div style="
        text-align:center;
        color:#777;
        font-size:13px;
        padding-bottom:10px;
    ">
        Student Performance<br>
        & Attainment System
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    page = st.radio(
        "FAST TUTOR MENU",
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

    st.caption("FAST TUTOR")
    st.caption("Simple • Smart • Visual")


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        "<div class='fast-title'>FAST TUTOR</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div class='fast-subtitle'>"
        "Student Performance & Attainment System"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("""
    <div class="hero">

        <div class="hero-title">
            Welcome to Fast Tutor 🎓
        </div>

        <div class="hero-text">
            Manage courses, students, assessments,
            marks and learning-outcome attainment
            from one simple system.
        </div>

    </div>
    """, unsafe_allow_html=True)

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

    a, b, c = st.columns(3)

    a.metric("📚 Courses", course_count)
    b.metric("👨‍🎓 Students", student_count)
    c.metric("📝 Assessments", assessment_count)

    d, e, f = st.columns(3)

    d.metric("🎯 CLOs", clo_count)
    e.metric("🏆 PLOs", plo_count)
    f.metric("📊 Marks Records", result_count)

    st.divider()

    results = get_results()

    if not results.empty:

        st.subheader("📈 Overall Course Performance")

        course_chart = (
            results
            .groupby("Course Code")["Percentage"]
            .mean()
            .round(2)
        )

        st.bar_chart(course_chart)

    else:

        st.info(
            "No marks uploaded yet. "
            "Use Bulk Marks Upload to start."
        )


# ============================================================
# COURSES
# ============================================================

elif page == "📚 Courses":

    st.title("📚 Courses")

    st.write(
        "Create your courses before enrolling students."
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

        save = st.form_submit_button(
            "➕ ADD COURSE",
            type="primary",
            use_container_width=True
        )

    if save:

        if not course_code.strip() or not course_name.strip():

            st.error(
                "Course Code and Course Name are required."
            )

        else:

            if execute("""
                INSERT INTO courses
                (
                    course_code,
                    course_name,
                    credit_hours,
                    semester
                )
                VALUES (?, ?, ?, ?)
            """, (
                course_code.strip().upper(),
                course_name.strip(),
                credit_hours,
                semester.strip()
            )):

                st.success("Course added successfully.")
                st.rerun()

    st.divider()

    courses = get_courses()

    if courses.empty:
        st.info("No courses created yet.")
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

    st.write(
        "Upload the complete student list in one file."
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Individual Student",
            "📥 Bulk Import"
        ]
    )

    with tab1:

        with st.form("student_form"):

            c1, c2 = st.columns(2)

            with c1:

                roll = st.text_input(
                    "Roll Number"
                )

                name = st.text_input(
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

            save = st.form_submit_button(
                "➕ ENROLL STUDENT",
                type="primary",
                use_container_width=True
            )

        if save:

            if not roll.strip() or not name.strip():

                st.error(
                    "Roll Number and Student Name are required."
                )

            else:

                execute("""
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
                        student_name = excluded.student_name,
                        program = excluded.program,
                        semester = excluded.semester,
                        section = excluded.section
                """, (
                    roll.strip(),
                    name.strip(),
                    program.strip(),
                    semester.strip(),
                    section.strip()
                ))

                st.success("Student saved.")
                st.rerun()

    with tab2:

        st.markdown("""
        Your file should contain columns such as:

        **Roll Number | Student Name | Program | Semester | Section**
        """)

        template = pd.DataFrame({
            "Roll Number": ["CS001", "CS002"],
            "Student Name": ["Ali Ahmed", "Sara Khan"],
            "Program": ["BS Computer Science", "BS Computer Science"],
            "Semester": ["3", "3"],
            "Section": ["A", "A"]
        })

        st.download_button(
            "⬇️ Download Student Template",
            template.to_csv(index=False).encode(),
            "Fast_Tutor_Student_Template.csv",
            "text/csv"
        )

        uploaded = st.file_uploader(
            "Upload Student Excel/CSV",
            type=["csv", "xlsx", "xls"],
            key="student_upload"
        )

        if uploaded:

            try:

                if uploaded.name.lower().endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)

                st.success(
                    f"{len(df)} student records found."
                )

                st.dataframe(
                    df,
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
                        "registration_no"
                    ]
                )

                name_col = find_column(
                    df,
                    [
                        "student_name",
                        "name",
                        "student"
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

                if not roll_col or not name_col:

                    st.error(
                        "Roll Number and Student Name "
                        "columns are required."
                    )

                elif st.button(
                    "🚀 IMPORT ALL STUDENTS",
                    type="primary",
                    use_container_width=True
                ):

                    count = 0

                    for _, row in df.iterrows():

                        roll_value = str(
                            row[roll_col]
                        ).strip()

                        name_value = str(
                            row[name_col]
                        ).strip()

                        if (
                            not roll_value
                            or roll_value.lower() == "nan"
                            or not name_value
                            or name_value.lower() == "nan"
                        ):
                            continue

                        program_value = ""

                        if program_col:
                            program_value = str(
                                row[program_col]
                            ).strip()

                        semester_value = ""

                        if semester_col:
                            semester_value = str(
                                row[semester_col]
                            ).strip()

                        section_value = ""

                        if section_col:
                            section_value = str(
                                row[section_col]
                            ).strip()

                        execute("""
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
                                student_name = excluded.student_name,
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

                        count += 1

                    st.success(
                        f"{count} student records imported."
                    )

                    st.rerun()

            except Exception as e:

                st.error(
                    "Could not read the file: " + str(e)
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
            "Create a course first."
        )

    else:

        course = st.selectbox(
            "Select Course",
            courses["Course Code"].tolist()
        )

        with st.form("clo_form"):

            c1, c2 = st.columns(2)

            with c1:

                clo = st.text_input(
                    "CLO Code",
                    placeholder="CLO1"
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

            with c2:

                description = st.text_area(
                    "CLO Description"
                )

            save = st.form_submit_button(
                "➕ ADD CLO",
                type="primary",
                use_container_width=True
            )

        if save:

            if not clo.strip() or not description.strip():

                st.error(
                    "CLO and description are required."
                )

            else:

                if execute("""
                    INSERT INTO clos
                    (
                        course_code,
                        clo_code,
                        description,
                        bloom_level
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    course,
                    clo.strip().upper(),
                    description.strip(),
                    bloom
                )):

                    st.success("CLO added.")
                    st.rerun()

        st.divider()

        data = get_clos()

        st.dataframe(
            data[
                data["Course Code"] == course
            ],
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
            "PLO Code",
            placeholder="PLO1"
        )

        description = st.text_area(
            "PLO Description"
        )

        save = st.form_submit_button(
            "➕ ADD PLO",
            type="primary",
            use_container_width=True
        )

    if save:

        if not plo.strip() or not description.strip():

            st.error(
                "PLO and description are required."
            )

        else:

            if execute("""
                INSERT INTO plos
                (
                    plo_code,
                    description
                )
                VALUES (?, ?)
            """, (
                plo.strip().upper(),
                description.strip()
            )):

                st.success("PLO added.")
                st.rerun()

    st.divider()

    st.dataframe(
        get_plos(),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ASSESSMENT CREATION
# ============================================================

elif page == "📝 Assessment Creation":

    st.title("📝 Assessment Creation")

    st.markdown("""
    <div class="hero">

        <div class="hero-title">
            Create Assessments 📝
        </div>

        <div class="hero-text">
            Create quizzes, assignments, midterms,
            final examinations, projects and practicals.
            Then assign the CLOs assessed by each assessment.
        </div>

    </div>
    """, unsafe_allow_html=True)

    courses = get_courses()

    if courses.empty:

        st.warning(
            "Create a course first."
        )

    else:

        course = st.selectbox(
            "📚 Select Course",
            courses["Course Code"].tolist()
        )

        course_clos = get_clos()

        course_clos = course_clos[
            course_clos["Course Code"] == course
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

                description = st.text_area(
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

                    checked = st.checkbox(
                        f"{row['CLO']} — {row['Description']}",
                        key=f"new_assessment_{course}_{row['CLO']}"
                    )

                    if checked:
                        selected_clos.append(
                            row["CLO"]
                        )

            create = st.form_submit_button(
                "🚀 CREATE ASSESSMENT",
                type="primary",
                use_container_width=True
            )

        if create:

            if not assessment_name.strip():

                st.error(
                    "Assessment Name is required."
                )

            elif not selected_clos:

                st.error(
                    "Select at least one CLO."
                )

            else:

                success = execute("""
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
                """, (
                    course,
                    assessment_name.strip(),
                    assessment_type,
                    str(assessment_date),
                    total_marks,
                    weightage,
                    description.strip()
                ))

                if success:

                    assessment = execute("""
                        SELECT id
                        FROM assessments
                        WHERE course_code = ?
                        AND assessment_name = ?
                    """, (
                        course,
                        assessment_name.strip()
                    ), fetch=True)

                    if assessment:

                        assessment_id = assessment[0][0]

                        for clo_code in selected_clos:

                            execute("""
                                INSERT INTO assessment_clos
                                (
                                    assessment_id,
                                    clo_code
                                )
                                VALUES (?, ?)
                            """, (
                                assessment_id,
                                clo_code
                            ))

                    st.success(
                        "Assessment created successfully."
                    )

                    st.rerun()

        st.divider()

        st.subheader(
            "📋 Existing Assessments"
        )

        assessments = execute("""
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
            ORDER BY assessment_date, id
        """, (
            course,
        ), fetch=True)

        if not assessments:

            st.info(
                "No assessments created for this course."
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
                "🎯 CLOs Assigned to Assessments"
            )

            for item in assessments:

                assessment_id = item[0]
                assessment_name_existing = item[1]

                assigned = execute("""
                    SELECT clo_code
                    FROM assessment_clos
                    WHERE assessment_id = ?
                    ORDER BY clo_code
                """, (
                    assessment_id,
                ), fetch=True)

                clo_names = [
                    x[0] for x in assigned
                ]

                if clo_names:

                    st.success(
                        f"{assessment_name_existing}: "
                        + ", ".join(clo_names)
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

        st.warning("Create courses first.")

    elif clos.empty:

        st.warning("Create CLOs first.")

    elif plos.empty:

        st.warning("Create PLOs first.")

    else:

        course = st.selectbox(
            "Select Course",
            courses["Course Code"].tolist()
        )

        course_clos = clos[
            clos["Course Code"] == course
        ]

        st.info(
            "0 = No Mapping | "
            "1 = Low | "
            "2 = Medium | "
            "3 = High"
        )

        values = {}

        for _, clo_row in course_clos.iterrows():

            st.markdown(
                f"### {clo_row['CLO']}"
            )

            st.caption(
                clo_row["Description"]
            )

            cols = st.columns(
                len(plos)
            )

            for i, plo in enumerate(
                plos["PLO"]
            ):

                with cols[i]:

                    values[
                        clo_row["CLO"],
                        plo
                    ] = st.selectbox(
                        plo,
                        [0, 1, 2, 3],
                        key=f"map_{course}_{clo_row['CLO']}_{plo}"
                    )

        if st.button(
            "💾 SAVE CLO–PLO MAPPING",
            type="primary",
            use_container_width=True
        ):

            for (clo_code, plo_code), strength in values.items():

                execute("""
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
                        strength = excluded.strength
                """, (
                    course,
                    clo_code,
                    plo_code,
                    strength
                ))

            st.success(
                "Mapping saved successfully."
            )

            st.rerun()


# ============================================================
# BULK MARKS UPLOAD
# ============================================================

elif page == "📥 Bulk Marks Upload":

    st.title("📥 Bulk Marks Upload")

    st.markdown("""
    <div class="hero">

        <div class="hero-title">
            Upload the whole class at once 🚀
        </div>

        <div class="hero-text">
            No need to enter student marks one-by-one.
            Upload a complete Excel or CSV file.
        </div>

    </div>
    """, unsafe_allow_html=True)

    template = pd.DataFrame({
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
    })

    st.subheader(
        "📄 Marks File Format"
    )

    st.dataframe(
        template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Marks Template",
        template.to_csv(index=False).encode(),
        "Fast_Tutor_Marks_Template.csv",
        "text/csv"
    )

    uploaded = st.file_uploader(
        "📥 Upload Complete Marks File",
        type=["csv", "xlsx", "xls"],
        key="marks_upload"
    )

    if uploaded:

        try:

            if uploaded.name.lower().endswith(".csv"):
                df = pd.read_csv(uploaded)
            else:
                df = pd.read_excel(uploaded)

            st.success(
                f"{len(df)} records found."
            )

            st.dataframe(
                df.head(100),
                use_container_width=True,
                hide_index=True
            )

            roll_col = find_column(
                df,
                [
                    "roll_number",
                    "roll_no",
                    "roll",
                    "registration_number"
                ]
            )

            course_col = find_column(
                df,
                [
                    "course_code",
                    "course",
                    "subject_code"
                ]
            )

            assessment_col = find_column(
                df,
                [
                    "assessment",
                    "assessment_name",
                    "exam",
                    "test"
                ]
            )

            clo_col = find_column(
                df,
                [
                    "clo",
                    "clo_code"
                ]
            )

            obtained_col = find_column(
                df,
                [
                    "obtained_marks",
                    "marks_obtained",
                    "obtained",
                    "marks",
                    "score"
                ]
            )

            total_col = find_column(
                df,
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
                    "🚀 IMPORT ALL MARKS",
                    type="primary",
                    use_container_width=True
                ):

                    added = 0
                    updated = 0
                    skipped = 0

                    progress = st.progress(0)

                    total_rows = max(
                        len(df),
                        1
                    )

                    for i, row in df.iterrows():

                        try:

                            roll_value = str(
                                row[roll_col]
                            ).strip()

                            course_value = str(
                                row[course_col]
                            ).strip().upper()

                            assessment_value = str(
                                row[assessment_col]
                            ).strip()

                            clo_value = ""

                            if clo_col:

                                clo_value = str(
                                    row[clo_col]
                                ).strip().upper()

                            obtained = float(
                                row[obtained_col]
                            )

                            if total_col:

                                total = float(
                                    row[total_col]
                                )

                            else:

                                total = 100

                            if total <= 0:

                                skipped += 1
                                continue

                            student_exists = execute("""
                                SELECT id
                                FROM students
                                WHERE roll_no = ?
                            """, (
                                roll_value,
                            ), fetch=True)

                            if not student_exists:

                                skipped += 1
                                continue

                            percentage = (
                                obtained /
                                total
                            ) * 100

                            grade = grade_from_percentage(
                                percentage
                            )

                            existing = execute("""
                                SELECT id
                                FROM results
                                WHERE roll_no = ?
                                AND course_code = ?
                                AND assessment = ?
                                AND clo_code = ?
                            """, (
                                roll_value,
                                course_value,
                                assessment_value,
                                clo_value
                            ), fetch=True)

                            if existing:

                                execute("""
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
                                """, (
                                    obtained,
                                    total,
                                    percentage,
                                    grade,
                                    roll_value,
                                    course_value,
                                    assessment_value,
                                    clo_value
                                ))

                                updated += 1

                            else:

                                execute("""
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
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    roll_value,
                                    course_value,
                                    assessment_value,
                                    clo_value,
                                    obtained,
                                    total,
                                    percentage,
                                    grade
                                ))

                                added += 1

                        except Exception:

                            skipped += 1

                        progress.progress(
                            (i + 1) / total_rows
                        )

                    st.success(
                        f"Upload complete: "
                        f"{added} added, "
                        f"{updated} updated, "
                        f"{skipped} skipped."
                    )

                    st.rerun()

        except Exception as e:

            st.error(
                "Could not read the file: " + str(e)
            )


# ============================================================
# INDIVIDUAL STUDENT PERFORMANCE
# ============================================================

elif page == "📊 Student Performance":

    st.title("📊 Individual Student Performance")

    students = get_students()
    results = get_results()

    if students.empty:

        st.warning(
            "No students enrolled."
        )

    elif results.empty:

        st.warning(
            "No marks have been uploaded."
        )

    else:

        roll = st.selectbox(
            "👨‍🎓 Select Student",
            students["Roll Number"].tolist()
        )

        student = students[
            students["Roll Number"] == roll
        ].iloc[0]

        student_results = results[
            results["Roll Number"] == roll
        ].copy()

        st.markdown(f"""
        <div class="hero">

            <div class="hero-title">
                🎓 {student['Student Name']}
            </div>

            <div class="hero-text">
                Roll Number: <b>{student['Roll Number']}</b>
                &nbsp; | &nbsp;
                Program: <b>{student['Program']}</b>
                &nbsp; | &nbsp;
                Semester: <b>{student['Semester']}</b>
                &nbsp; | &nbsp;
                Section: <b>{student['Section']}</b>
            </div>

        </div>
        """, unsafe_allow_html=True)

        overall = student_results[
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

        a, b, c, d = st.columns(4)

        a.metric(
            "Overall",
            f"{overall:.1f}%"
        )

        b.metric(
            "Records",
            len(student_results)
        )

        c.metric(
            "Passed",
            passed
        )

        d.metric(
            "Failed",
            failed
        )

        st.divider()

        st.subheader(
            "📚 Course Performance"
        )

        course_chart = (
            student_results
            .groupby("Course Code")["Percentage"]
            .mean()
            .round(2)
        )

        st.bar_chart(course_chart)

        st.subheader(
            "📝 Assessment Performance"
        )

        assessment_chart = (
            student_results
            .groupby("Assessment")["Percentage"]
            .mean()
            .round(2)
        )

        st.line_chart(assessment_chart)

        st.subheader(
            "🎯 CLO Attainment"
        )

        clo_data = student_results[
            student_results["CLO"].astype(str).str.strip() != ""
        ]

        if clo_data.empty:

            st.info(
                "No CLO-level marks available."
            )

        else:

            clo_chart = (
                clo_data
                .groupby("CLO")["Percentage"]
                .mean()
                .round(2)
            )

            st.bar_chart(clo_chart)

            for clo, value in clo_chart.items():

                if value >= 70:

                    st.success(
                        f"{clo}: {value:.1f}% — Achieved"
                    )

                else:

                    st.warning(
                        f"{clo}: {value:.1f}% — Needs Improvement"
                    )

        st.subheader(
            "🏆 PLO Attainment"
        )

        mappings = get_mappings()

        if mappings.empty:

            st.info(
                "Create CLO–PLO mappings first."
            )

        elif clo_data.empty:

            st.info(
                "CLO marks are required for PLO attainment."
            )

        else:

            plo_values = {}

            for plo in mappings["PLO"].unique():

                selected = mappings[
                    mappings["PLO"] == plo
                ]

                values = []

                for _, mapping in selected.iterrows():

                    strength = float(
                        mapping["Strength"]
                    )

                    if strength <= 0:
                        continue

                    matching = clo_data[
                        (
                            clo_data["Course Code"]
                            == mapping["Course Code"]
                        )
                        &
                        (
                            clo_data["CLO"]
                            == mapping["CLO"]
                        )
                    ]

                    if not matching.empty:

                        values.append(
                            (
                                matching[
                                    "Percentage"
                                ].mean(),
                                strength
                            )
                        )

                if values:

                    plo_values[plo] = (
                        sum(
                            v * w
                            for v, w in values
                        )
                        /
                        sum(
                            w
                            for v, w in values
                        )
                    )

            if plo_values:

                plo_chart = pd.Series(
                    plo_values
                ).round(2)

                st.bar_chart(plo_chart)

                for plo, value in plo_chart.items():

                    if value >= 70:

                        st.success(
                            f"{plo}: {value:.1f}% — Achieved"
                        )

                    else:

                        st.warning(
                            f"{plo}: {value:.1f}% — Needs Improvement"
                        )

        st.subheader(
            "📋 Detailed Results"
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

    st.title("📈 Attainment Dashboard")

    results = get_results()

    if results.empty:

        st.info(
            "Upload marks to view attainment."
        )

    else:

        clo_data = results[
            results["CLO"].astype(str).str.strip() != ""
        ]

        if not clo_data.empty:

            st.subheader(
                "🎯 CLO Attainment"
            )

            clo_chart = (
                clo_data
                .groupby("CLO")["Percentage"]
                .mean()
                .round(2)
            )

            st.bar_chart(clo_chart)

        else:

            st.info(
                "No CLO marks available."
            )

        mappings = get_mappings()

        if not mappings.empty and not clo_data.empty:

            st.subheader(
                "🏆 PLO Attainment"
            )

            plo_values = {}

            for plo in mappings["PLO"].unique():

                selected = mappings[
                    mappings["PLO"] == plo
                ]

                values = []

                for _, mapping in selected.iterrows():

                    if mapping["Strength"] <= 0:
                        continue

                    matching = clo_data[
                        (
                            clo_data["Course Code"]
                            == mapping["Course Code"]
                        )
                        &
                        (
                            clo_data["CLO"]
                            == mapping["CLO"]
                        )
                    ]

                    if not matching.empty:

                        values.append(
                            (
                                matching["Percentage"].mean(),
                                mapping["Strength"]
                            )
                        )

                if values:

                    plo_values[plo] = (
                        sum(
                            v * w
                            for v, w in values
                        )
                        /
                        sum(
                            w
                            for v, w in values
                        )
                    )

            if plo_values:

                st.bar_chart(
                    pd.Series(
                        plo_values
                    ).round(2)
                )


# ============================================================
# REPORTS
# ============================================================

elif page == "📤 Reports & Export":

    st.title("📤 Reports & Export")

    courses = get_courses()
    students = get_students()
    clos = get_clos()
    plos = get_plos()
    mappings = get_mappings()
    results = get_results()

    assessments_rows = execute("""
        SELECT
            course_code,
            assessment_name,
            assessment_type,
            assessment_date,
            total_marks,
            weightage,
            description
        FROM assessments
        ORDER BY course_code, assessment_date
    """, fetch=True)

    assessments = pd.DataFrame(
        assessments_rows,
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
        "📊 Complete Fast Tutor Excel Report"
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
        "⬇️ DOWNLOAD COMPLETE EXCEL REPORT",
        output.getvalue(),
        "Fast_Tutor_Complete_Report.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "👨‍🎓 Individual Student Report"
    )

    if not students.empty:

        roll = st.selectbox(
            "Select Student",
            students["Roll Number"].tolist()
        )

        individual = results[
            results["Roll Number"] == roll
        ]

        if individual.empty:

            st.info(
                "No marks found for this student."
            )

        else:

            st.dataframe(
                individual,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "⬇️ DOWNLOAD STUDENT REPORT",
                individual.to_csv(
                    index=False
                ).encode(),
                f"Fast_Tutor_{roll}.csv",
                "text/csv",
                use_container_width=True
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown("""
<div style="
    text-align:center;
    padding:15px;
    color:#777;
">

    <strong style="color:#0795D1;">
        FAST TUTOR
    </strong>

    <br>

    Student Performance & Attainment System

</div>
""", unsafe_allow_html=True)
