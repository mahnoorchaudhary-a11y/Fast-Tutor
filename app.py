import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
import os


# ============================================================
# FAST TUTOR
# ============================================================

st.set_page_config(
    page_title="Fast Tutor",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# DATABASE
# IMPORTANT:
# Streamlit Cloud project folders can be read-only.
# Therefore the database is stored in /tmp.
# ============================================================

DB_PATH = "/tmp/fast_tutor.db"


@st.cache_resource
def get_database():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            credit_hours REAL DEFAULT 3,
            semester TEXT DEFAULT ''
        )
    """)

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

    connection.execute("""
        CREATE TABLE IF NOT EXISTS clos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            clo TEXT NOT NULL,
            description TEXT DEFAULT '',
            bloom TEXT DEFAULT ''
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS plos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plo TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT ''
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_code TEXT NOT NULL,
            clo TEXT NOT NULL,
            plo TEXT NOT NULL,
            strength INTEGER DEFAULT 0
        )
    """)

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
# DATABASE HELPERS
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


def get_percentage(obtained, total):

    if total <= 0:
        return 0

    return round(
        (obtained / total) * 100,
        2
    )


def get_grade(mark):

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


def read_uploaded_file(uploaded):

    if uploaded is None:
        return None

    try:

        if uploaded.name.lower().endswith(".csv"):

            return pd.read_csv(uploaded)

        return pd.read_excel(uploaded)

    except Exception as error:

        st.error(
            f"Could not read file: {error}"
        )

        return None


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: 900;
    color: #0795D1;
}

.sub-title {
    color: #667085;
    font-size: 14px;
    margin-bottom: 25px;
}

.section-title {
    font-size: 28px;
    font-weight: 800;
    color: #172B4D;
}

.card {
    padding: 20px;
    border-radius: 15px;
    background: #F7FAFC;
    border: 1px solid #E5E7EB;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    '<div class="main-title">FAST TUTOR</div>',
    unsafe_allow_html=True
)

st.sidebar.markdown(
    '<div class="sub-title">Student Performance System</div>',
    unsafe_allow_html=True
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Courses",
        "Students",
        "Assessments",
        "CLO Management",
        "PLO Management",
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
        '<div class="section-title">Dashboard</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Manage courses, students, assessments and academic performance."
    )

    courses = one(
        "SELECT COUNT(*) FROM courses"
    )[0]

    students = one(
        "SELECT COUNT(*) FROM students"
    )[0]

    assessments = one(
        "SELECT COUNT(*) FROM assessments"
    )[0]

    clos = one(
        "SELECT COUNT(*) FROM clos"
    )[0]

    plos = one(
        "SELECT COUNT(*) FROM plos"
    )[0]

    marks = one(
        "SELECT COUNT(*) FROM results"
    )[0]

    a, b, c = st.columns(3)

    a.metric(
        "Courses",
        courses
    )

    b.metric(
        "Students",
        students
    )

    c.metric(
        "Assessments",
        assessments
    )

    d, e, f = st.columns(3)

    d.metric(
        "CLOs",
        clos
    )

    e.metric(
        "PLOs",
        plos
    )

    f.metric(
        "Mark Records",
        marks
    )

    st.divider()

    st.subheader(
        "Course Performance"
    )

    rows = query("""
        SELECT
            course_code,
            AVG(percentage)
        FROM results
        GROUP BY course_code
        ORDER BY course_code
    """)

    if rows:

        df = make_df(
            rows,
            [
                "Course",
                "Average"
            ]
        )

        df["Average"] = pd.to_numeric(
            df["Average"],
            errors="coerce"
        )

        st.bar_chart(
            df.set_index("Course")
        )

    else:

        st.info(
            "Upload marks to display performance."
        )


# ============================================================
# COURSES
# ============================================================

elif page == "Courses":

    st.markdown(
        '<div class="section-title">Courses</div>',
        unsafe_allow_html=True
    )

    with st.form("course_form"):

        c1, c2 = st.columns(2)

        with c1:

            code = st.text_input(
                "Course Code",
                placeholder="CS101"
            )

            name = st.text_input(
                "Course Name",
                placeholder="Programming Fundamentals"
            )

        with c2:

            credits = st.number_input(
                "Credit Hours",
                min_value=1.0,
                max_value=10.0,
                value=3.0
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

            st.warning(
                "Course code and course name are required."
            )

        else:

            existing = one(
                "SELECT id FROM courses WHERE code=?",
                (code,)
            )

            if existing:

                execute("""
                    UPDATE courses
                    SET name=?,
                        credit_hours=?,
                        semester=?
                    WHERE code=?
                """, (
                    name,
                    credits,
                    semester,
                    code
                ))

            else:

                execute("""
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
                    semester
                ))

            st.success(
                "Course saved successfully."
            )

    st.divider()

    rows = query("""
        SELECT
            code,
            name,
            credit_hours,
            semester
        FROM courses
        ORDER BY code
    """)

    st.dataframe(
        make_df(
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
        '<div class="section-title">Students</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(
        [
            "Add Student",
            "Bulk Import"
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
                "Save Student",
                type="primary"
            )

        if save:

            roll = clean(roll)
            name = clean(name)

            if not roll or not name:

                st.warning(
                    "Roll number and student name are required."
                )

            else:

                existing = one(
                    "SELECT id FROM students WHERE roll_no=?",
                    (roll,)
                )

                if existing:

                    execute("""
                        UPDATE students
                        SET name=?,
                            program=?,
                            semester=?,
                            section=?
                        WHERE roll_no=?
                    """, (
                        name,
                        program,
                        semester,
                        section,
                        roll
                    ))

                else:

                    execute("""
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
                        name,
                        program,
                        semester,
                        section
                    ))

                st.success(
                    "Student saved."
                )

    with tab2:

        st.subheader(
            "Bulk Student Import"
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
                "BSCS",
                "BSCS"
            ],
            "Semester": [
                "1",
                "1"
            ],
            "Section": [
                "A",
                "A"
            ]
        })

        st.download_button(
            "Download Student Template",
            template.to_csv(
                index=False
            ).encode(),
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
            key="students_file"
        )

        if uploaded:

            df = read_uploaded_file(
                uploaded
            )

            if df is not None:

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                if st.button(
                    "IMPORT STUDENTS",
                    type="primary"
                ):

                    success_count = 0
                    skip_count = 0

                    columns = {
                        str(c).lower().strip(): c
                        for c in df.columns
                    }

                    roll_col = (
                        columns.get("roll number")
                        or columns.get("roll_no")
                        or columns.get("roll")
                    )

                    name_col = (
                        columns.get("student name")
                        or columns.get("name")
                    )

                    if not roll_col or not name_col:

                        st.error(
                            "The file must contain "
                            "'Roll Number' and "
                            "'Student Name' columns."
                        )

                    else:

                        for _, row in df.iterrows():

                            r = clean(
                                row[roll_col]
                            )

                            n = clean(
                                row[name_col]
                            )

                            if not r or not n:

                                skip_count += 1
                                continue

                            execute("""
                                INSERT OR REPLACE INTO students
                                (
                                    id,
                                    roll_no,
                                    name,
                                    program,
                                    semester,
                                    section
                                )
                                VALUES (
                                    (
                                        SELECT id
                                        FROM students
                                        WHERE roll_no=?
                                    ),
                                    ?,
                                    ?,
                                    ?,
                                    ?,
                                    ?
                                )
                            """, (
                                r,
                                r,
                                n,
                                "",
                                "",
                                ""
                            ))

                            success_count += 1

                        st.success(
                            f"{success_count} students imported."
                        )

                        if skip_count:
                            st.warning(
                                f"{skip_count} rows skipped."
                            )

    st.divider()

    rows = query("""
        SELECT
            roll_no,
            name,
            program,
            semester,
            section
        FROM students
        ORDER BY roll_no
    """)

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

elif page == "Assessments":

    st.markdown(
        '<div class="section-title">Assessment Creation</div>',
        unsafe_allow_html=True
    )

    courses = query("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    if not courses:

        st.info(
            "Create a course first."
        )

    else:

        course_options = [
            f"{x[0]} - {x[1]}"
            for x in courses
        ]

        selected = st.selectbox(
            "Course",
            course_options
        )

        course_code = selected.split(
            " - "
        )[0]

        with st.form("assessment_form"):

            name = st.text_input(
                "Assessment Name",
                placeholder="Midterm Examination"
            )

            assessment_type = st.selectbox(
                "Assessment Type",
                [
                    "Quiz",
                    "Assignment",
                    "Midterm",
                    "Final",
                    "Project",
                    "Lab",
                    "Presentation",
                    "Other"
                ]
            )

            total = st.number_input(
                "Total Marks",
                min_value=1.0,
                value=100.0
            )

            weight = st.number_input(
                "Weightage %",
                min_value=0.0,
                max_value=100.0,
                value=20.0
            )

            save = st.form_submit_button(
                "Create Assessment",
                type="primary"
            )

        if save:

            if not clean(name):

                st.warning(
                    "Assessment name is required."
                )

            else:

                execute("""
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
                    clean(name),
                    assessment_type,
                    total,
                    weight
                ))

                st.success(
                    "Assessment created."
                )

        rows = query("""
            SELECT
                name,
                assessment_type,
                total_marks,
                weightage
            FROM assessments
            WHERE course_code=?
            ORDER BY id DESC
        """, (
            course_code,
        ))

        st.dataframe(
            make_df(
                rows,
                [
                    "Assessment",
                    "Type",
                    "Total Marks",
                    "Weightage"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CLO MANAGEMENT
# ============================================================

elif page == "CLO Management":

    st.markdown(
        '<div class="section-title">CLO Management</div>',
        unsafe_allow_html=True
    )

    courses = query("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    if not courses:

        st.info(
            "Create a course first."
        )

    else:

        options = [
            f"{x[0]} - {x[1]}"
            for x in courses
        ]

        selected = st.selectbox(
            "Course",
            options
        )

        course_code = selected.split(
            " - "
        )[0]

        with st.form("clo_form"):

            clo = st.text_input(
                "CLO",
                placeholder="CLO1"
            )

            description = st.text_area(
                "CLO Description"
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

                st.warning(
                    "Enter a CLO."
                )

            else:

                execute("""
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
                    clo,
                    description,
                    bloom
                ))

                st.success(
                    "CLO saved."
                )

        rows = query("""
            SELECT
                clo,
                description,
                bloom
            FROM clos
            WHERE course_code=?
            ORDER BY clo
        """, (
            course_code,
        ))

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

elif page == "PLO Management":

    st.markdown(
        '<div class="section-title">PLO Management</div>',
        unsafe_allow_html=True
    )

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

            st.warning(
                "Enter a PLO."
            )

        else:

            existing = one(
                "SELECT id FROM plos WHERE plo=?",
                (plo,)
            )

            if existing:

                execute("""
                    UPDATE plos
                    SET description=?
                    WHERE plo=?
                """, (
                    description,
                    plo
                ))

            else:

                execute("""
                    INSERT INTO plos
                    (
                        plo,
                        description
                    )
                    VALUES (?, ?)
                """, (
                    plo,
                    description
                ))

            st.success(
                "PLO saved."
            )

    rows = query("""
        SELECT
            plo,
            description
        FROM plos
        ORDER BY plo
    """)

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

elif page == "CLO-PLO Mapping":

    st.markdown(
        '<div class="section-title">CLO-PLO Mapping</div>',
        unsafe_allow_html=True
    )

    courses = query("""
        SELECT code, name
        FROM courses
        ORDER BY code
    """)

    plos = query("""
        SELECT plo
        FROM plos
        ORDER BY plo
    """)

    if not courses:

        st.info(
            "Create courses first."
        )

    elif not plos:

        st.info(
            "Create PLOs first."
        )

    else:

        options = [
            f"{x[0]} - {x[1]}"
            for x in courses
        ]

        selected = st.selectbox(
            "Course",
            options
        )

        course_code = selected.split(
            " - "
        )[0]

        clos = query("""
            SELECT clo
            FROM clos
            WHERE course_code=?
            ORDER BY clo
        """, (
            course_code,
        ))

        plo_codes = [
            x[0]
            for x in plos
        ]

        if not clos:

            st.info(
                "Create CLOs for this course first."
            )

        else:

            st.write(
                "0 = None | 1 = Low | "
                "2 = Medium | 3 = High"
            )

            for clo_row in clos:

                clo = clo_row[0]

                st.markdown(
                    f"**{clo}**"
                )

                cols = st.columns(
                    len(plo_codes)
                )

                for i, plo in enumerate(
                    plo_codes
                ):

                    existing = one("""
                        SELECT strength
                        FROM mappings
                        WHERE course_code=?
                        AND clo=?
                        AND plo=?
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
                        key=f"{course_code}_{clo}_{plo}"
                    )

                    old = one("""
                        SELECT id
                        FROM mappings
                        WHERE course_code=?
                        AND clo=?
                        AND plo=?
                    """, (
                        course_code,
                        clo,
                        plo
                    ))

                    if old:

                        execute("""
                            UPDATE mappings
                            SET strength=?
                            WHERE id=?
                        """, (
                            value,
                            old[0]
                        ))

                    else:

                        execute("""
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
                "Mapping saved."
            )


# ============================================================
# BULK MARKS
# ============================================================

elif page == "Bulk Marks":

    st.markdown(
        '<div class="section-title">Bulk Marks Upload</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload the complete class marks file. "
        "You do NOT need to enter marks one student at a time."
    )

    template = pd.DataFrame({
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
    })

    st.subheader(
        "Required Format"
    )

    st.dataframe(
        template,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download Marks Template",
        template.to_csv(
            index=False
        ).encode(),
        "Fast_Tutor_Marks_Template.csv",
        "text/csv"
    )

    uploaded = st.file_uploader(
        "Upload Marks File",
        type=[
            "csv",
            "xlsx",
            "xls"
        ],
        key="marks_file"
    )

    if uploaded:

        df = read_uploaded_file(
            uploaded
        )

        if df is not None:

            st.write(
                f"Rows detected: **{len(df)}**"
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            if st.button(
                "IMPORT ALL MARKS",
                type="primary"
            ):

                imported = 0
                skipped = 0

                cols = {
                    str(c).lower().strip(): c
                    for c in df.columns
                }

                roll_col = (
                    cols.get("roll number")
                    or cols.get("roll_no")
                    or cols.get("roll")
                )

                course_col = (
                    cols.get("course code")
                    or cols.get("course_code")
                    or cols.get("course")
                )

                assessment_col = (
                    cols.get("assessment")
                    or cols.get("assessment name")
                )

                clo_col = (
                    cols.get("clo")
                    or cols.get("clo code")
                )

                obtained_col = (
                    cols.get("obtained marks")
                    or cols.get("obtained")
                    or cols.get("marks")
                )

                total_col = (
                    cols.get("total marks")
                    or cols.get("total")
                )

                required = [
                    roll_col,
                    course_col,
                    assessment_col,
                    obtained_col,
                    total_col
                ]

                if any(
                    x is None
                    for x in required
                ):

                    st.error(
                        "Required columns are: "
                        "Roll Number, Course Code, "
                        "Assessment, Obtained Marks, "
                        "Total Marks."
                    )

                else:

                    for _, row in df.iterrows():

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

                        if clo_col:

                            clo = clean(
                                row[clo_col]
                            ).upper()

                        if (
                            not roll
                            or not course
                            or not assessment
                            or total <= 0
                            or obtained < 0
                            or obtained > total
                        ):

                            skipped += 1
                            continue

                        student = one("""
                            SELECT id
                            FROM students
                            WHERE roll_no=?
                        """, (
                            roll,
                        ))

                        if not student:

                            skipped += 1
                            continue

                        pct = get_percentage(
                            obtained,
                            total
                        )

                        grd = get_grade(
                            pct
                        )

                        execute("""
                            DELETE FROM results
                            WHERE roll_no=?
                            AND course_code=?
                            AND assessment=?
                            AND clo=?
                        """, (
                            roll,
                            course,
                            assessment,
                            clo
                        ))

                        execute("""
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
                            roll,
                            course,
                            assessment,
                            clo,
                            obtained,
                            total,
                            pct,
                            grd
                        ))

                        imported += 1

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

elif page == "Student Performance":

    st.markdown(
        '<div class="section-title">Student Performance</div>',
        unsafe_allow_html=True
    )

    students = query("""
        SELECT
            roll_no,
            name
        FROM students
        ORDER BY roll_no
    """)

    if not students:

        st.info(
            "Import students first."
        )

    else:

        options = [
            f"{x[0]} - {x[1]}"
            for x in students
        ]

        selected = st.selectbox(
            "Select Student",
            options
        )

        roll = selected.split(
            " - "
        )[0]

        student = one("""
            SELECT
                name,
                program,
                semester,
                section
            FROM students
            WHERE roll_no=?
        """, (
            roll,
        ))

        if student:

            st.subheader(
                f"🎓 {student[0]}"
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Roll Number",
                roll
            )

            c2.metric(
                "Program",
                student[1] or "-"
            )

            c3.metric(
                "Semester",
                student[2] or "-"
            )

            c4.metric(
                "Section",
                student[3] or "-"
            )

            rows = query("""
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
            """, (
                roll,
            ))

            if not rows:

                st.info(
                    "No marks found."
                )

            else:

                df = make_df(
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

                df["Percentage"] = pd.to_numeric(
                    df["Percentage"],
                    errors="coerce"
                )

                average = df[
                    "Percentage"
                ].mean()

                st.metric(
                    "Overall Performance",
                    f"{average:.2f}%"
                )

                st.subheader(
                    "Performance by Course"
                )

                chart = (
                    df.groupby(
                        "Course"
                    )["Percentage"]
                    .mean()
                )

                st.bar_chart(
                    chart
                )

                clo_df = df[
                    df["CLO"].astype(str).str.strip() != ""
                ]

                if not clo_df.empty:

                    st.subheader(
                        "CLO Performance"
                    )

                    clo_chart = (
                        clo_df.groupby(
                            "CLO"
                        )["Percentage"]
                        .mean()
                    )

                    st.bar_chart(
                        clo_chart
                    )

                st.subheader(
                    "Marks Detail"
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )


# ============================================================
# ATTAINMENT
# ============================================================

elif page == "Attainment":

    st.markdown(
        '<div class="section-title">CLO / PLO Attainment</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(
        [
            "CLO Attainment",
            "PLO Attainment"
        ]
    )

    # --------------------------------------------------------
    # CLO
    # --------------------------------------------------------

    with tab1:

        rows = query("""
            SELECT
                clo,
                AVG(percentage)
            FROM results
            WHERE clo != ''
            GROUP BY clo
            ORDER BY clo
        """)

        if rows:

            df = make_df(
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

        else:

            st.info(
                "No CLO marks available."
            )

    # --------------------------------------------------------
    # PLO
    # --------------------------------------------------------

    with tab2:

        mapping_rows = query("""
            SELECT
                course_code,
                clo,
                plo,
                strength
            FROM mappings
            WHERE strength > 0
        """)

        result_rows = query("""
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
                "Upload marks first."
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
                    "No matching attainment data."
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

elif page == "Reports":

    st.markdown(
        '<div class="section-title">Reports</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Download your Fast Tutor data as an Excel workbook."
    )

    courses_df = make_df(
        query("""
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

    students_df = make_df(
        query("""
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

    assessments_df = make_df(
        query("""
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

    clos_df = make_df(
        query("""
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

    plos_df = make_df(
        query("""
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

    mapping_df = make_df(
        query("""
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

    results_df = make_df(
        query("""
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
                sheet_name="Mapping",
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
            f"Could not create Excel report: {error}"
        )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "Fast Tutor • Student Performance System"
)
