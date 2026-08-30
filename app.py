import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from pathlib import Path


# ============================================================
# FAST TUTOR
# Student Performance System
# ============================================================

st.set_page_config(
    page_title="Fast Tutor",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

DB_PATH = Path("fast_tutor.db")


def get_connection():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


db = get_connection()


def run_sql(sql, parameters=()):
    try:
        cursor = db.cursor()
        cursor.execute(sql, parameters)
        db.commit()
        return True
    except Exception as error:
        db.rollback()
        st.error(f"Database error: {error}")
        return False


def get_rows(sql, parameters=()):
    try:
        cursor = db.cursor()
        cursor.execute(sql, parameters)
        return cursor.fetchall()
    except Exception as error:
        st.error(f"Database error: {error}")
        return []


def get_one(sql, parameters=()):
    try:
        cursor = db.cursor()
        cursor.execute(sql, parameters)
        return cursor.fetchone()
    except Exception as error:
        st.error(f"Database error: {error}")
        return None


# ============================================================
# CREATE DATABASE
# ============================================================

run_sql("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    credit_hours REAL DEFAULT 3,
    semester TEXT DEFAULT ''
)
""")


run_sql("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll_no TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    program TEXT DEFAULT '',
    semester TEXT DEFAULT '',
    section TEXT DEFAULT ''
)
""")


run_sql("""
CREATE TABLE IF NOT EXISTS clos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    clo TEXT NOT NULL,
    description TEXT DEFAULT '',
    bloom TEXT DEFAULT '',
    UNIQUE(course_code, clo)
)
""")


run_sql("""
CREATE TABLE IF NOT EXISTS plos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plo TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT ''
)
""")


run_sql("""
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    name TEXT NOT NULL,
    assessment_type TEXT DEFAULT '',
    total_marks REAL DEFAULT 100,
    weightage REAL DEFAULT 0
)
""")


run_sql("""
CREATE TABLE IF NOT EXISTS mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    clo TEXT NOT NULL,
    plo TEXT NOT NULL,
    strength INTEGER DEFAULT 0,
    UNIQUE(course_code, clo, plo)
)
""")


run_sql("""
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
    UNIQUE(
        roll_no,
        course_code,
        assessment,
        clo
    )
)
""")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def text(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).strip()


def numeric(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def percentage(obtained, total):
    if total <= 0:
        return 0.0

    return round(
        (obtained / total) * 100,
        2
    )


def grade(mark):
    if mark >= 90:
        return "A+"
    elif mark >= 80:
        return "A"
    elif mark >= 70:
        return "B"
    elif mark >= 60:
        return "C"
    elif mark >= 50:
        return "D"
    else:
        return "F"


def dataframe(rows, columns):
    if not rows:
        return pd.DataFrame(columns=columns)

    safe_rows = []

    for row in rows:
        if isinstance(row, (tuple, list)):
            safe_rows.append(list(row))
        else:
            safe_rows.append([row])

    return pd.DataFrame(
        safe_rows,
        columns=columns
    )


def read_file(uploaded):
    if uploaded is None:
        return None

    try:
        filename = uploaded.name.lower()

        if filename.endswith(".csv"):
            return pd.read_csv(uploaded)

        if filename.endswith(".xlsx"):
            return pd.read_excel(uploaded)

        if filename.endswith(".xls"):
            return pd.read_excel(uploaded)

        st.error(
            "Please upload a CSV or Excel file."
        )
        return None

    except Exception as error:
        st.error(
            f"Unable to read the file: {error}"
        )
        return None


def column(df, names):
    available = {
        str(c).strip().lower(): c
        for c in df.columns
    }

    for name in names:
        key = name.strip().lower()

        if key in available:
            return available[key]

    return None


def save_result(
    roll_no,
    course_code,
    assessment,
    clo,
    obtained,
    total
):
    pct = percentage(
        obtained,
        total
    )

    grd = grade(pct)

    existing = get_one("""
        SELECT id
        FROM results
        WHERE roll_no = ?
        AND course_code = ?
        AND assessment = ?
        AND clo = ?
    """, (
        roll_no,
        course_code,
        assessment,
        clo
    ))

    if existing:

        return run_sql("""
            UPDATE results
            SET obtained = ?,
                total = ?,
                percentage = ?,
                grade = ?
            WHERE id = ?
        """, (
            obtained,
            total,
            pct,
            grd,
            existing[0]
        ))

    return run_sql("""
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
    """, (
        roll_no,
        course_code,
        assessment,
        clo,
        obtained,
        total,
        pct,
        grd
    ))


# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>

[data-testid="stSidebar"] {
    background-color: #F7FAFC;
}

.fast-title {
    font-size: 30px;
    font-weight: 900;
    color: #0795D1;
    margin-bottom: 4px;
}

.fast-subtitle {
    color: #667085;
    font-size: 13px;
    margin-bottom: 25px;
}

.page-title {
    font-size: 30px;
    font-weight: 800;
    color: #172B4D;
    margin-bottom: 5px;
}

.page-description {
    color: #667085;
    margin-bottom: 25px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    '<div class="fast-title">Fast Tutor</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    '<div class="fast-subtitle">Student Performance System</div>',
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "MENU",
    [
        "Dashboard",
        "Courses",
        "Students",
        "Assessments",
        "CLOs",
        "PLOs",
        "CLO-PLO Mapping",
        "Bulk Marks",
        "Student Performance",
        "Attainment",
        "Reports"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.markdown(
        '<div class="page-title">Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-description">'
        'Manage courses, students, assessments and academic performance.'
        '</div>',
        unsafe_allow_html=True
    )

    course_count = get_one(
        "SELECT COUNT(*) FROM courses"
    )

    student_count = get_one(
        "SELECT COUNT(*) FROM students"
    )

    clo_count = get_one(
        "SELECT COUNT(*) FROM clos"
    )

    plo_count = get_one(
        "SELECT COUNT(*) FROM plos"
    )

    assessment_count = get_one(
        "SELECT COUNT(*) FROM assessments"
    )

    result_count = get_one(
        "SELECT COUNT(*) FROM results"
    )

    a = course_count[0] if course_count else 0
    b = student_count[0] if student_count else 0
    c = clo_count[0] if clo_count else 0
    d = plo_count[0] if plo_count else 0
    e = assessment_count[0] if assessment_count else 0
    f = result_count[0] if result_count else 0

    c1, c2, c3 = st.columns(3)

    c1.metric("Courses", a)
    c2.metric("Students", b)
    c3.metric("CLOs", c)

    c4, c5, c6 = st.columns(3)

    c4.metric("PLOs", d)
    c5.metric("Assessments", e)
    c6.metric("Mark Records", f)

    st.divider()

    st.subheader("Overall Student Performance")

    rows = get_rows("""
        SELECT
            course_code,
            AVG(percentage)
        FROM results
        GROUP BY course_code
        ORDER BY course_code
    """)

    if rows:

        chart = dataframe(
            rows,
            ["Course", "Average"]
        )

        chart["Average"] = pd.to_numeric(
            chart["Average"],
            errors="coerce"
        )

        st.bar_chart(
            chart.set_index("Course")
        )

    else:

        st.info(
            "Upload student marks to see performance charts."
        )

    st.subheader("CLO Attainment")

    rows = get_rows("""
        SELECT
            clo,
            AVG(percentage)
        FROM results
        WHERE clo != ''
        GROUP BY clo
        ORDER BY clo
    """)

    if rows:

        chart = dataframe(
            rows,
            ["CLO", "Attainment"]
        )

        chart["Attainment"] = pd.to_numeric(
            chart["Attainment"],
            errors="coerce"
        )

        st.bar_chart(
            chart.set_index("CLO")
        )

    else:

        st.info(
            "No CLO-linked marks are available yet."
        )


# ============================================================
# COURSES
# ============================================================

elif page == "Courses":

    st.markdown(
        '<div class="page-title">Courses</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-description">'
        'Create courses before adding assessments and students.'
        '</div>',
        unsafe_allow_html=True
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

            credits = st.number_input(
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

        submitted = st.form_submit_button(
            "Save Course",
            type="primary"
        )

    if submitted:

        code = text(code).upper()
        name = text(name)

        if not code:
            st.error("Course code is required.")

        elif not name:
            st.error("Course name is required.")

        else:

            existing = get_one(
                "SELECT id FROM courses WHERE code = ?",
                (code,)
            )

            if existing:

                ok = run_sql("""
                    UPDATE courses
                    SET name = ?,
                        credit_hours = ?,
                        semester = ?
                    WHERE code = ?
                """, (
                    name,
                    credits,
                    text(semester),
                    code
                ))

            else:

                ok = run_sql("""
                    INSERT INTO courses
                    (
                        code,
                        name,
                        credit_hours,
                        semester
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    code,
                    name,
                    credits,
                    text(semester)
                ))

            if ok:
                st.success(
                    "Course saved successfully."
                )

    st.divider()

    rows = get_rows("""
        SELECT
            code,
            name,
            credit_hours,
            semester
        FROM courses
        ORDER BY code
    """)

    st.dataframe(
        dataframe(
            rows,
            [
                "Course Code",
                "Course Name",
                "Credit Hours",
                "Semester"
            ]
        ),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# STUDENTS
# ============================================================

elif page == "Students":

    st.markdown(
        '<div class="page-title">Students</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-description">'
        'Add students individually or import the complete class in one file.'
        '</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(
        [
            "Add Student",
            "Bulk Import"
        ]
    )

    # --------------------------------------------------------
    # SINGLE STUDENT
    # --------------------------------------------------------

    with tab1:

        with st.form("single_student"):

            col1, col2 = st.columns(2)

            with col1:

                roll = st.text_input(
                    "Roll Number"
                )

                student_name = st.text_input(
                    "Student Name"
                )

                program = st.text_input(
                    "Program"
                )

            with col2:

                semester = st.text_input(
                    "Semester"
                )

                section = st.text_input(
                    "Section"
                )

            submitted = st.form_submit_button(
                "Save Student",
                type="primary"
            )

        if submitted:

            roll = text(roll)
            student_name = text(student_name)

            if not roll:
                st.error(
                    "Roll number is required."
                )

            elif not student_name:
                st.error(
                    "Student name is required."
                )

            else:

                existing = get_one(
                    "SELECT id FROM students WHERE roll_no = ?",
                    (roll,)
                )

                if existing:

                    ok = run_sql("""
                        UPDATE students
                        SET name = ?,
                            program = ?,
                            semester = ?,
                            section = ?
                        WHERE roll_no = ?
                    """, (
                        student_name,
                        text(program),
                        text(semester),
                        text(section),
                        roll
                    ))

                else:

                    ok = run_sql("""
                        INSERT INTO students
                        (
                            roll_no,
                            name,
                            program,
                            semester,
                            section
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        roll,
                        student_name,
                        text(program),
                        text(semester),
                        text(section)
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
            "Upload Complete Student List"
        )

        template = pd.DataFrame({
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
        })

        st.dataframe(
            template,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Student Template",
            template.to_csv(
                index=False
            ).encode("utf-8"),
            "Fast_Tutor_Student_Template.csv",
            "text/csv"
        )

        uploaded = st.file_uploader(
            "Upload CSV or Excel",
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

                roll_column = column(
                    df,
                    [
                        "roll number",
                        "roll_no",
                        "rollno",
                        "roll",
                        "registration number"
                    ]
                )

                name_column = column(
                    df,
                    [
                        "student name",
                        "name",
                        "student"
                    ]
                )

                program_column = column(
                    df,
                    [
                        "program",
                        "degree"
                    ]
                )

                semester_column = column(
                    df,
                    [
                        "semester",
                        "sem"
                    ]
                )

                section_column = column(
                    df,
                    [
                        "section",
                        "sec"
                    ]
                )

                if not roll_column or not name_column:

                    st.error(
                        "Your file must contain "
                        "'Roll Number' and 'Student Name'."
                    )

                else:

                    st.write(
                        f"**{len(df)} students detected.**"
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

                        successful = 0
                        failed = 0

                        for _, row in df.iterrows():

                            roll_value = text(
                                row[roll_column]
                            )

                            name_value = text(
                                row[name_column]
                            )

                            if (
                                not roll_value
                                or not name_value
                            ):
                                failed += 1
                                continue

                            program_value = ""

                            if program_column:
                                program_value = text(
                                    row[program_column]
                                )

                            semester_value = ""

                            if semester_column:
                                semester_value = text(
                                    row[semester_column]
                                )

                            section_value = ""

                            if section_column:
                                section_value = text(
                                    row[section_column]
                                )

                            existing = get_one(
                                "SELECT id FROM students WHERE roll_no = ?",
                                (roll_value,)
                            )

                            if existing:

                                ok = run_sql("""
                                    UPDATE students
                                    SET name = ?,
                                        program = ?,
                                        semester = ?,
                                        section = ?
                                    WHERE roll_no = ?
                                """, (
                                    name_value,
                                    program_value,
                                    semester_value,
                                    section_value,
                                    roll_value
                                ))

                            else:

                                ok = run_sql("""
                                    INSERT INTO students
                                    (
                                        roll_no,
                                        name,
                                        program,
                                        semester,
                                        section
                                    )
                                    VALUES (?, ?, ?, ?, ?)
                                """, (
                                    roll_value,
                                    name_value,
                                    program_value,
                                    semester_value,
                                    section_value
                                ))

                            if ok:
                                successful += 1
                            else:
                                failed += 1

                        st.success(
                            f"{successful} students imported."
                        )

                        if failed:
                            st.warning(
                                f"{failed} rows could not be imported."
                            )

    st.divider()

    rows = get_rows("""
        SELECT
            roll_no,
            name,
            program,
            semester,
            section
        FROM students
        ORDER BY roll_no
    """)

    st.subheader(
        "Enrolled Students"
    )

    st.dataframe(
        dataframe(
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

elif page == "Assessments":

    st.markdown(
        '<div class="page-title">Assessments</div>',
        unsafe_allow_html=True
    )

    courses = get_rows("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    if not courses:

        st.warning(
            "Please create a course first."
        )

    else:

        course_names = [
            f"{row[0]} — {row[1]}"
            for row in courses
        ]

        selected_course = st.selectbox(
            "Course",
            course_names
        )

        course_code = selected_course.split(
            " — "
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

                total = st.number_input(
                    "Total Marks",
                    min_value=1.0,
                    value=100.0
                )

            with col2:

                weight = st.number_input(
                    "Weightage %",
                    min_value=0.0,
                    max_value=100.0,
                    value=20.0
                )

            submitted = st.form_submit_button(
                "Create Assessment",
                type="primary"
            )

        if submitted:

            if not text(assessment_name):

                st.error(
                    "Assessment name is required."
                )

            else:

                ok = run_sql("""
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
                    text(assessment_name),
                    assessment_type,
                    total,
                    weight
                ))

                if ok:
                    st.success(
                        "Assessment created."
                    )

        st.divider()

        rows = get_rows("""
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

        st.dataframe(
            dataframe(
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
# CLOs
# ============================================================

elif page == "CLOs":

    st.markdown(
        '<div class="page-title">CLO Management</div>',
        unsafe_allow_html=True
    )

    courses = get_rows("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    if not courses:

        st.warning(
            "Please create a course first."
        )

    else:

        course_names = [
            f"{row[0]} — {row[1]}"
            for row in courses
        ]

        selected = st.selectbox(
            "Course",
            course_names
        )

        course_code = selected.split(
            " — "
        )[0]

        with st.form("clo_form"):

            clo_code = st.text_input(
                "CLO",
                placeholder="CLO1"
            )

            description = st.text_area(
                "Description"
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

            submitted = st.form_submit_button(
                "Save CLO",
                type="primary"
            )

        if submitted:

            clo_code = text(
                clo_code
            ).upper()

            if not clo_code:

                st.error(
                    "CLO is required."
                )

            else:

                existing = get_one("""
                    SELECT id
                    FROM clos
                    WHERE course_code = ?
                    AND clo = ?
                """, (
                    course_code,
                    clo_code
                ))

                if existing:

                    ok = run_sql("""
                        UPDATE clos
                        SET description = ?,
                            bloom = ?
                        WHERE course_code = ?
                        AND clo = ?
                    """, (
                        text(description),
                        bloom,
                        course_code,
                        clo_code
                    ))

                else:

                    ok = run_sql("""
                        INSERT INTO clos
                        (
                            course_code,
                            clo,
                            description,
                            bloom
                        )
                        VALUES (?, ?, ?, ?)
                    """, (
                        course_code,
                        clo_code,
                        text(description),
                        bloom
                    ))

                if ok:
                    st.success(
                        "CLO saved."
                    )

        rows = get_rows("""
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

        st.dataframe(
            dataframe(
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
# PLOs
# ============================================================

elif page == "PLOs":

    st.markdown(
        '<div class="page-title">PLO Management</div>',
        unsafe_allow_html=True
    )

    with st.form("plo_form"):

        plo_code = st.text_input(
            "PLO",
            placeholder="PLO1"
        )

        description = st.text_area(
            "Description",
            placeholder="Knowledge of Computing"
        )

        submitted = st.form_submit_button(
            "Save PLO",
            type="primary"
        )

    if submitted:

        plo_code = text(
            plo_code
        ).upper()

        if not plo_code:

            st.error(
                "PLO is required."
            )

        else:

            existing = get_one(
                "SELECT id FROM plos WHERE plo = ?",
                (plo_code,)
            )

            if existing:

                ok = run_sql("""
                    UPDATE plos
                    SET description = ?
                    WHERE plo = ?
                """, (
                    text(description),
                    plo_code
                ))

            else:

                ok = run_sql("""
                    INSERT INTO plos
                    (
                        plo,
                        description
                    )
                    VALUES (?, ?)
                """, (
                    plo_code,
                    text(description)
                ))

            if ok:
                st.success(
                    "PLO saved."
                )

    st.divider()

    rows = get_rows("""
        SELECT
            plo,
            description
        FROM plos
        ORDER BY plo
    """)

    st.dataframe(
        dataframe(
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

elif page == "CLO-PLO Mapping":

    st.markdown(
        '<div class="page-title">CLO-PLO Mapping</div>',
        unsafe_allow_html=True
    )

    courses = get_rows("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    plos = get_rows("""
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

        course_names = [
            f"{row[0]} — {row[1]}"
            for row in courses
        ]

        selected = st.selectbox(
            "Course",
            course_names
        )

        course_code = selected.split(
            " — "
        )[0]

        clos = get_rows("""
            SELECT clo
            FROM clos
            WHERE course_code = ?
            ORDER BY clo
        """, (
            course_code,
        ))

        if not clos:

            st.warning(
                "Create CLOs for this course first."
            )

        else:

            plo_codes = [
                row[0]
                for row in plos
            ]

            st.write(
                "**Mapping strength:** "
                "0 = None, 1 = Low, 2 = Medium, 3 = High"
            )

            for clo_row in clos:

                clo = clo_row[0]

                st.markdown(
                    f"### {clo}"
                )

                cols = st.columns(
                    len(plo_codes)
                )

                for i, plo in enumerate(
                    plo_codes
                ):

                    existing = get_one("""
                        SELECT strength
                        FROM mappings
                        WHERE course_code = ?
                        AND clo = ?
                        AND plo = ?
                    """, (
                        course_code,
                        clo,
                        plo
                    ))

                    current = (
                        existing[0]
                        if existing
                        else 0
                    )

                    value = cols[i].selectbox(
                        plo,
                        [0, 1, 2, 3],
                        index=int(current),
                        key=(
                            "mapping_"
                            + course_code
                            + "_"
                            + clo
                            + "_"
                            + plo
                        )
                    )

                    existing = get_one("""
                        SELECT id
                        FROM mappings
                        WHERE course_code = ?
                        AND clo = ?
                        AND plo = ?
                    """, (
                        course_code,
                        clo,
                        plo
                    ))

                    if existing:

                        run_sql("""
                            UPDATE mappings
                            SET strength = ?
                            WHERE id = ?
                        """, (
                            value,
                            existing[0]
                        ))

                    else:

                        run_sql("""
                            INSERT INTO mappings
                            (
                                course_code,
                                clo,
                                plo,
                                strength
                            )
                            VALUES (?, ?, ?, ?)
                        """, (
                            course_code,
                            clo,
                            plo,
                            value
                        ))

            st.success(
                "Mapping is saved automatically."
            )

            st.divider()

            mapping_rows = get_rows("""
                SELECT
                    clo,
                    plo,
                    strength
                FROM mappings
                WHERE course_code = ?
                ORDER BY clo, plo
            """, (
                course_code,
            ))

            st.dataframe(
                dataframe(
                    mapping_rows,
                    [
                        "CLO",
                        "PLO",
                        "Strength"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# BULK MARKS
# ============================================================

elif page == "Bulk Marks":

    st.markdown(
        '<div class="page-title">Bulk Marks Upload</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="page-description">'
        'Upload the complete class marks file. '
        'Marks do not need to be entered student by student.'
        '</div>',
        unsafe_allow_html=True
    )

    st.subheader(
        "Recommended File Format"
    )

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
        "CLO": [
            "CLO1",
            "CLO1",
            "CLO1"
        ],
        "Obtained Marks": [
            82,
            76,
            91
        ],
        "Total Marks": [
            100,
            100,
            100
        ]
    })

    st.dataframe(
        marks_template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Marks Template",
        marks_template.to_csv(
            index=False
        ).encode("utf-8"),
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

            roll_column = column(
                df,
                [
                    "roll number",
                    "roll_no",
                    "rollno",
                    "roll",
                    "registration number"
                ]
            )

            course_column = column(
                df,
                [
                    "course code",
                    "course_code",
                    "course"
                ]
            )

            assessment_column = column(
                df,
                [
                    "assessment",
                    "assessment name",
                    "assessment_name"
                ]
            )

            clo_column = column(
                df,
                [
                    "clo",
                    "clo code"
                ]
            )

            obtained_column = column(
                df,
                [
                    "obtained marks",
                    "obtained",
                    "marks obtained",
                    "marks"
                ]
            )

            total_column = column(
                df,
                [
                    "total marks",
                    "total",
                    "maximum marks",
                    "max marks"
                ]
            )

            required_missing = []

            if roll_column is None:
                required_missing.append(
                    "Roll Number"
                )

            if course_column is None:
                required_missing.append(
                    "Course Code"
                )

            if assessment_column is None:
                required_missing.append(
                    "Assessment"
                )

            if obtained_column is None:
                required_missing.append(
                    "Obtained Marks"
                )

            if total_column is None:
                required_missing.append(
                    "Total Marks"
                )

            if required_missing:

                st.error(
                    "Missing columns: "
                    + ", ".join(
                        required_missing
                    )
                )

            else:

                st.success(
                    f"{len(df)} mark rows detected."
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                if st.button(
                    "IMPORT ALL MARKS",
                    type="primary",
                    key="import_marks"
                ):

                    imported = 0
                    skipped = 0

                    progress = st.progress(
                        0
                    )

                    total_rows = max(
                        len(df),
                        1
                    )

                    for number_row, (_, row) in enumerate(
                        df.iterrows()
                    ):

                        roll = text(
                            row[roll_column]
                        )

                        course = text(
                            row[course_column]
                        ).upper()

                        assessment = text(
                            row[assessment_column]
                        )

                        obtained = numeric(
                            row[obtained_column]
                        )

                        total_marks = numeric(
                            row[total_column]
                        )

                        clo = ""

                        if clo_column is not None:
                            clo = text(
                                row[clo_column]
                            ).upper()

                        if (
                            not roll
                            or not course
                            or not assessment
                            or total_marks <= 0
                        ):

                            skipped += 1

                        else:

                            student = get_one("""
                                SELECT id
                                FROM students
                                WHERE roll_no = ?
                            """, (
                                roll,
                            ))

                            if student is None:

                                skipped += 1

                            elif obtained < 0:

                                skipped += 1

                            elif obtained > total_marks:

                                skipped += 1

                            else:

                                ok = save_result(
                                    roll,
                                    course,
                                    assessment,
                                    clo,
                                    obtained,
                                    total_marks
                                )

                                if ok:
                                    imported += 1
                                else:
                                    skipped += 1

                        progress.progress(
                            min(
                                (number_row + 1)
                                / total_rows,
                                1.0
                            )
                        )

                    st.success(
                        f"{imported} marks imported or updated."
                    )

                    if skipped:
                        st.warning(
                            f"{skipped} rows were skipped. "
                            "Check roll numbers and marks."
                        )


# ============================================================
# STUDENT PERFORMANCE
# ============================================================

elif page == "Student Performance":

    st.markdown(
        '<div class="page-title">Student Performance</div>',
        unsafe_allow_html=True
    )

    students = get_rows("""
        SELECT
            roll_no,
            name
        FROM students
        ORDER BY roll_no
    """)

    if not students:

        st.info(
            "No students are enrolled yet."
        )

    else:

        options = [
            f"{row[0]} — {row[1]}"
            for row in students
        ]

        selected = st.selectbox(
            "Select Student",
            options
        )

        roll = selected.split(
            " — "
        )[0]

        student = get_one("""
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

            st.subheader(
                f"🎓 {student[0]}"
            )

            x1, x2, x3, x4 = st.columns(4)

            x1.metric(
                "Roll Number",
                roll
            )

            x2.metric(
                "Program",
                student[1] or "-"
            )

            x3.metric(
                "Semester",
                student[2] or "-"
            )

            x4.metric(
                "Section",
                student[3] or "-"
            )

            rows = get_rows("""
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
                    "No marks have been uploaded for this student."
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

                result_df["Percentage"] = pd.to_numeric(
                    result_df["Percentage"],
                    errors="coerce"
                )

                average = result_df[
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

                a, b, c = st.columns(3)

                a.metric(
                    "Overall",
                    f"{average:.1f}%"
                )

                b.metric(
                    "Passed",
                    passed
                )

                c.metric(
                    "Failed",
                    failed
                )

                st.subheader(
                    "Course Performance"
                )

                course_chart = (
                    result_df
                    .groupby("Course")[
                        "Percentage"
                    ]
                    .mean()
                )

                st.bar_chart(
                    course_chart
                )

                clo_df = result_df[
                    result_df["CLO"]
                    .astype(str)
                    .str.strip()
                    != ""
                ]

                if not clo_df.empty:

                    st.subheader(
                        "CLO Performance"
                    )

                    clo_chart = (
                        clo_df
                        .groupby("CLO")[
                            "Percentage"
                        ]
                        .mean()
                    )

                    st.bar_chart(
                        clo_chart
                    )

                st.subheader(
                    "Detailed Marks"
                )

                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# ATTAINMENT
# ============================================================

elif page == "Attainment":

    st.markdown(
        '<div class="page-title">Attainment Tracker</div>',
        unsafe_allow_html=True
    )

    clo_tab, plo_tab = st.tabs(
        [
            "CLO Attainment",
            "PLO Attainment"
        ]
    )

    # --------------------------------------------------------
    # CLO
    # --------------------------------------------------------

    with clo_tab:

        rows = get_rows("""
            SELECT
                clo,
                AVG(percentage)
            FROM results
            WHERE clo != ''
            GROUP BY clo
            ORDER BY clo
        """)

        if rows:

            df = dataframe(
                rows,
                [
                    "CLO",
                    "Attainment"
                ]
            )

            df["Attainment"] = pd.to_numeric(
                df["Attainment"],
                errors="coerce"
            ).round(2)

            st.bar_chart(
                df.set_index("CLO")
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            weak = df[
                df["Attainment"] < 70
            ]

            if not weak.empty:

                st.warning(
                    "CLOs below 70%."
                )

                st.dataframe(
                    weak,
                    use_container_width=True,
                    hide_index=True
                )

        else:

            st.info(
                "No CLO marks are available."
            )

    # --------------------------------------------------------
    # PLO
    # --------------------------------------------------------

    with plo_tab:

        mappings = get_rows("""
            SELECT
                course_code,
                clo,
                plo,
                strength
            FROM mappings
            WHERE strength > 0
        """)

        results = get_rows("""
            SELECT
                course_code,
                clo,
                percentage
            FROM results
            WHERE clo != ''
        """)

        if not mappings:

            st.info(
                "Create CLO-PLO mappings first."
            )

        elif not results:

            st.info(
                "Upload CLO-linked marks first."
            )

        else:

            map_df = dataframe(
                mappings,
                [
                    "Course",
                    "CLO",
                    "PLO",
                    "Strength"
                ]
            )

            result_df = dataframe(
                results,
                [
                    "Course",
                    "CLO",
                    "Percentage"
                ]
            )

            combined = result_df.merge(
                map_df,
                on=[
                    "Course",
                    "CLO"
                ],
                how="inner"
            )

            if combined.empty:

                st.info(
                    "No matching PLO attainment data."
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

                grouped = combined.groupby(
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

                grouped["Attainment"] = (
                    grouped["Weighted"]
                    /
                    grouped["Strength"]
                )

                grouped["Attainment"] = (
                    grouped["Attainment"]
                    .fillna(0)
                    .round(2)
                )

                plo_chart = grouped[
                    ["Attainment"]
                ]

                st.subheader(
                    "PLO Attainment"
                )

                st.bar_chart(
                    plo_chart
                )

                plo_table = (
                    grouped[
                        ["Attainment"]
                    ]
                    .reset_index()
                )

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
                        "Weak PLOs below 70%."
                    )

                    st.dataframe(
                        weak,
                        use_container_width=True,
                        hide_index=True
                    )


# ============================================================
# REPORTS
# ============================================================

elif page == "Reports":

    st.markdown(
        '<div class="page-title">Reports</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Export the complete Fast Tutor database to Excel."
    )

    courses_df = dataframe(
        get_rows("""
            SELECT
                code,
                name,
                credit_hours,
                semester
            FROM courses
            ORDER BY code
        """),
        [
            "Course Code",
            "Course Name",
            "Credit Hours",
            "Semester"
        ]
    )

    students_df = dataframe(
        get_rows("""
            SELECT
                roll_no,
                name,
                program,
                semester,
                section
            FROM students
            ORDER BY roll_no
        """),
        [
            "Roll Number",
            "Student Name",
            "Program",
            "Semester",
            "Section"
        ]
    )

    assessments_df = dataframe(
        get_rows("""
            SELECT
                course_code,
                name,
                assessment_type,
                total_marks,
                weightage
            FROM assessments
            ORDER BY course_code
        """),
        [
            "Course",
            "Assessment",
            "Type",
            "Total Marks",
            "Weightage"
        ]
    )

    clos_df = dataframe(
        get_rows("""
            SELECT
                course_code,
                clo,
                description,
                bloom
            FROM clos
            ORDER BY course_code, clo
        """),
        [
            "Course",
            "CLO",
            "Description",
            "Bloom"
        ]
    )

    plos_df = dataframe(
        get_rows("""
            SELECT
                plo,
                description
            FROM plos
            ORDER BY plo
        """),
        [
            "PLO",
            "Description"
        ]
    )

    mapping_df = dataframe(
        get_rows("""
            SELECT
                course_code,
                clo,
                plo,
                strength
            FROM mappings
            ORDER BY course_code, clo, plo
        """),
        [
            "Course",
            "CLO",
            "PLO",
            "Strength"
        ]
    )

    results_df = dataframe(
        get_rows("""
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
            ORDER BY roll_no, course_code
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

            mapping_df.to_excel(
                writer,
                sheet_name="CLO-PLO Mapping",
                index=False
            )

            results_df.to_excel(
                writer,
                sheet_name="Results",
                index=False
            )

        st.download_button(
            "DOWNLOAD EXCEL REPORT",
            output.getvalue(),
            "Fast_Tutor_Report.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    except Exception as error:

        st.error(
            f"Excel report could not be created: {error}"
        )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "Fast Tutor"
)

st.sidebar.caption(
    "Student Performance System"
)
