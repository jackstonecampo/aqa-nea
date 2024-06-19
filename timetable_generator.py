import sqlite3

class DatabaseManager:
    def __init__(self, db_file):
        self.db_file = db_file

    def connect(self):
        return sqlite3.connect(self.db_file)

    def get_num_groups(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM 'Group'")
            return cursor.fetchone()[0]

    def execute_query(self, query, params=None):
        with self.connect() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def get_pupil_names(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT FirstName, LastName FROM Pupil")
            return [f"{row[0]} {row[1]}" for row in cursor.fetchall()]

    def get_teacher_names(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT FirstName, LastName FROM Teacher")
            return [f"{row[0]} {row[1]}" for row in cursor.fetchall()]
        
    def get_pupil_schedule(self, pupil_name):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT PeriodID, 'Group'.GroupID, ClassroomID, 'Group'.SubjectID FROM Schedule JOIN PupilGroup ON Schedule.GroupID = PupilGroup.GroupID JOIN Pupil ON PupilGroup.PupilID = Pupil.PupilID JOIN 'Group' ON PupilGroup.GroupID = 'Group'.GroupID WHERE Pupil.FirstName || ' ' || Pupil.LastName = ?", (pupil_name,))
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            return [dict(zip(column_names, row)) for row in rows]

    def get_teacher_schedule(self, teacher_name):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT PeriodID, 'Group'.GroupID, ClassroomID, 'Group'.SubjectID FROM Schedule JOIN 'Group' ON Schedule.GroupID = 'Group'.GroupID JOIN Teacher ON 'Group'.TeacherID = Teacher.TeacherID WHERE Teacher.FirstName || ' ' || Teacher.LastName = ?", (teacher_name,))
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            return [dict(zip(column_names, row)) for row in rows]
        
    def get_pupil_id(self, full_name):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT PupilID FROM Pupil WHERE FirstName || ' ' || LastName = ?", (full_name,))
            result = cursor.fetchone()
            return result[0]

    def get_teacher_id(self, full_name):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT TeacherID FROM Teacher WHERE FirstName || ' ' || LastName = ?", (full_name,))
            result = cursor.fetchone()
            return result[0]

class GroupCompatibilityManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_compatible_groups_by_pupil_id(self):
        num_groups = self.db_manager.get_num_groups()
        compatible_groups = {}
        for group_id in range(num_groups):
            query = "SELECT PupilID FROM PupilGroup WHERE GroupID = ?"
            pupil_ids = self.db_manager.execute_query(query, (group_id,))
            pupils = set([pupil_id[0] for pupil_id in pupil_ids])
            temp_compat = []
            for compare_group in range(num_groups):
                query = "SELECT PupilID FROM PupilGroup WHERE GroupID = ?"
                compare_ids = self.db_manager.execute_query(query, (compare_group,))
                compare_pupils = set([pupil_id[0] for pupil_id in compare_ids])
                if pupils.isdisjoint(compare_pupils):
                    temp_compat.append(compare_group)
            compatible_groups[group_id] = temp_compat
        return compatible_groups

    def get_compatible_groups_by_teacher_id(self):
        num_groups = self.db_manager.get_num_groups()
        compatible_groups = {}
        for group_id in range(num_groups):
            query = "SELECT TeacherID FROM 'Group' WHERE GroupID = ?"
            teacher_id = self.db_manager.execute_query(query, (group_id,))[0][0]
            query = "SELECT GroupID FROM 'Group' WHERE TeacherID != ?"
            group_ids = self.db_manager.execute_query(query, (teacher_id,))
            compatible_groups[group_id] = [group_id[0] for group_id in group_ids]
        return compatible_groups
    
    def get_compatible_groups(self):
        num_groups = self.db_manager.get_num_groups()
        dict_pupil = self.get_compatible_groups_by_pupil_id()
        dict_teacher = self.get_compatible_groups_by_teacher_id()
        compatible_groups = {}
        for group_id in range(num_groups):
            compatible_pupils = set(dict_pupil[group_id])
            compatible_teachers = set(dict_teacher[group_id])
            compatible_groups[group_id] = list(set(compatible_pupils) & set(compatible_teachers))
        
        return compatible_groups
    
    def get_group_subjects(self, groupids):
        subject_ids = []
        for groupid in groupids:
            query = "SELECT SubjectID FROM 'Group' WHERE GroupID = ?"
            subject_id = self.db_manager.execute_query(query, (groupid,))[0][0]
            subject_ids.append(subject_id)
        return subject_ids
    
    def count_subjects(self, groupids):
        subjects = self.get_group_subjects(groupids)
        counts = {}
        for subjectid in subjects:
            if subjectid not in counts:
                counts[subjectid] = 1
            else:
                counts[subjectid] += 1
        return counts

    def get_available_classrooms_by_subject(self):
        available_classrooms = {}
        query = "SELECT SubjectID, COUNT(*) FROM Classroom GROUP BY SubjectID"
        results = self.db_manager.execute_query(query)
        for row in results:
            subjectid, count = row
            available_classrooms[subjectid] = count
        return available_classrooms
    
    def get_groups_by_subject(self, subjectid):
        query = "SELECT GroupID FROM 'Group' WHERE SubjectID = ?"
        groups = self.db_manager.execute_query(query, (subjectid,))[0]
        return groups

    def find_compatible_groupings(self, groupids, excluded_groupids, compatible_groups, available_classrooms):
        current_id = groupids[-1]
        subject_counts = self.count_subjects(groupids)
        for subjectid in subject_counts:
            if subject_counts[subjectid] == available_classrooms[subjectid]:
                excluded_groupids += self.get_groups_by_subject(subjectid)
        for groupid in compatible_groups[current_id]:
            if all(groupid in compatible_groups[compare_group] for compare_group in groupids) and groupid not in excluded_groupids:
                return self.find_compatible_groupings(groupids + [groupid], excluded_groupids, compatible_groups, available_classrooms)

        return groupids
    
class ScheduleManager:

    def __init__(self, db_file):
        self.db_manager = DatabaseManager(db_file)
        self.compat_manager = GroupCompatibilityManager(self.db_manager)
        query = "SELECT MAX(PeriodNumber), MAX(Day) FROM Period"
        periods_per_day, num_days = self.db_manager.execute_query(query)[0]
        self.slots = [[] for _ in range((periods_per_day + 1) * (num_days + 1))]

    def get_counts(self):
        num_groups = self.db_manager.get_num_groups()
        counts = {groupid: 0 for groupid in range(num_groups)}
        for slot in self.slots:
            for groupid in slot:
                counts[groupid] += 1
        return counts

    def get_minimum_count(self):
        counts = self.get_counts()
        minimum_count = min(counts, key=counts.get)
        return minimum_count

    def get_max_counts(self):
        counts = self.get_counts()
        max_count = max(counts.values())
        top_x = int(self.db_manager.get_num_groups() * 0.8)
        max_counts = [k for k in counts if counts[k] == max_count][:top_x]
        return max_counts
    
    def assign_slots(self):
        compatible_groups = self.compat_manager.get_compatible_groups()
        available_classrooms = self.compat_manager.get_available_classrooms_by_subject()
        for i in range(len(self.slots)):
            group_min = self.get_minimum_count()
            excluded_groupids = self.get_max_counts()
            self.slots[i] = self.compat_manager.find_compatible_groupings([group_min], excluded_groupids, compatible_groups, available_classrooms)
    
    def assign_classrooms_to_slot(self, slot):
        query = "SELECT Classroom.ClassroomID FROM Classroom JOIN 'Group' ON Classroom.SubjectID = 'Group'.SubjectID WHERE 'Group'.GroupID = ?"
        classrooms = []
        for groupid in slot:
            result = [classroomid[0] for classroomid in self.db_manager.execute_query(query, (groupid,))]
            for classroomid in result:
                if classroomid not in classrooms:
                    classrooms.append(classroomid)
        return classrooms
        

    def save_to_table(self):
        query = "DELETE FROM Schedule"
        self.db_manager.execute_query(query)

        query = "INSERT INTO Schedule (PeriodID, GroupID, ClassroomID) VALUES (?, ?, ?)"
        for periodid in range(len(self.slots)):
            classrooms = self.assign_classrooms_to_slot(self.slots[periodid])
            for i, groupid in enumerate(self.slots[periodid]):
                classroomid = classrooms[i]
                self.db_manager.execute_query(query, (periodid, groupid, classroomid,))

if __name__ == "__main__":
    db_manager = DatabaseManager("neadb.db")
    query = "SELECT MAX(PeriodNumber), MAX(Day) FROM Period"
    
    