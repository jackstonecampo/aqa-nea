import sqlite3

filename = "schooldb.db"
conn = sqlite3.connect(filename)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE Period (
    PeriodID     NUMERIC PRIMARY KEY
                         UNIQUE
                         NOT NULL,
    Day          NUMERIC,
    PeriodNumber NUMERIC
);
""")

cursor.execute("""
CREATE TABLE Subject (
    SubjectID   NUMERIC PRIMARY KEY
                        UNIQUE
                        NOT NULL,
    SubjectName TEXT
);
""")

cursor.execute("""
    CREATE TABLE Teacher (
    TeacherID NUMERIC PRIMARY KEY
                      UNIQUE
                      NOT NULL,
    FirstName TEXT,
    LastName  TEXT
);
""")

cursor.execute("""
    CREATE TABLE TeacherSubject (
    TeacherID  REFERENCES Teacher (TeacherID),
    SubjectID  REFERENCES Subject (SubjectID) 
);
""")

cursor.execute("""
    CREATE TABLE Pupil (
    PupilID   NUMERIC PRIMARY KEY
                      UNIQUE
                      NOT NULL,
    FirstName TEXT,
    LastName  TEXT,
    YearGroup NUMERIC
);
""")

cursor.execute("""
    CREATE TABLE [Group] (
    GroupID   NUMERIC PRIMARY KEY
                      NOT NULL
                      UNIQUE,
    TeacherID NUMERIC REFERENCES Teacher (TeacherID),
    SubjectID NUMERIC REFERENCES Subject (SubjectID) 
);
""")

cursor.execute("""
    CREATE TABLE PupilGroup (
    GroupID NUMERIC REFERENCES [Group] (GroupID),
    PupilID NUMERIC REFERENCES Pupil (PupilID) 
);
""")

cursor.execute("""
    CREATE TABLE Classroom (
    ClassroomID NUMERIC PRIMARY KEY
                        UNIQUE
                        NOT NULL,
    SubjectID   NUMERIC REFERENCES Subject (SubjectID) 
);
""")

cursor.execute("""
    CREATE TABLE Schedule (
    PeriodID    NUMERIC REFERENCES Period (PeriodID),
    GroupID     NUMERIC REFERENCES [Group] (GroupID),
    ClassroomID NUMERIC REFERENCES Classroom (ClassroomID) 
);
""")