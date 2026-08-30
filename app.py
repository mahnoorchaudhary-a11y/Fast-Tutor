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
