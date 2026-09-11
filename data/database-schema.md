# Student Information System Database Schema

The `education_workshop_db` database is queryable via Amazon Athena (Presto/Trino
SQL dialect) through the `education-athena-query` Lambda. It contains 12 tables of
university data. The dataset is scoped to the **College of Engineering** and its
five departments: Aeronautics (AERO), Computer Science (COMP), Data Science,
Engineering, and Environment and Natural Resources.

Schema derived from the source CSVs in `education-data/`.

## SQL Dialect Notes (Athena / Presto / Trino)

- Use single quotes for string literals: `WHERE student_id = '100016'`.
- IDs are stored as strings in some tables (e.g. `student_id`) and integers in
  others. When in doubt, compare as strings.
- Use standard ANSI joins (`JOIN ... ON ...`). No `USING` shortcuts needed.
- `date`/timestamp columns are stored as strings in the CSVs; cast if you need
  date arithmetic (e.g. `CAST(start_date AS DATE)`).
- Sentinel/placeholder values appear in the data: e.g. `date_dropped = '0001-01-01'`
  means "not dropped", and several `_id`/gpa fields use `0` as "not provided".

## Tables

### student
Core student records. Note: there is **no `program` column**; a student's
program/major is derived via `department_id` → `department`.

| Column | Type | Notes |
| --- | --- | --- |
| student_id | string | PK |
| first_name | string | |
| last_name | string | |
| gender | string | |
| birth_date | string | may be empty |
| email_address | string | |
| admitted | int | 0/1 |
| enrolled | int | 0/1 |
| parent_alum | int | 0/1 |
| parent_highest_ed | int | FK-ish → ed_level.ed_level_id |
| first_gen_hed_student | int | 0/1 |
| high_school_gpa | double | |
| was_hs_athlete_ind | int | 0/1 |
| home_state_name | string | |
| admit_type | string | e.g. 'Regular' |
| private_hs_indicator | int | 0/1 |
| multiple_majors_indicator | int | 0/1 |
| secondary_class_percentile | int | |
| department_id | int | FK → department.department_id |
| admit_semester_id | int | FK → semester.semester_id |
| first_year_gpa | double | 0 = not provided |
| cumulative_gpa | double | |
| enroll_status | string | e.g. 'admitted', 'enrolled' |
| planned_grad_semester_id | int | FK → semester.semester_id |

### course
Course catalogue.

| Column | Type | Notes |
| --- | --- | --- |
| course_id | int | PK |
| course_name | string | |
| course_level | int | e.g. 100, 200 |
| course_code | string | e.g. 'AERO-0100', 'COMP-0100' |
| school_id | int | FK → school.school_id |
| department_id | int | FK → department.department_id |

### course_registration
Which students registered for which courses in which semester.

| Column | Type | Notes |
| --- | --- | --- |
| date_registered | string | date |
| date_dropped | string | '0001-01-01' = not dropped |
| student_id | string | FK → student.student_id |
| course_id | int | FK → course.course_id |
| status | string | e.g. 'completed', 'registered', 'dropped' |
| semester_id | int | FK → semester.semester_id |
| update_ts | string | timestamp |

### course_outcome
Student grades and outcomes per course/semester.

| Column | Type | Notes |
| --- | --- | --- |
| student_id | string | FK → student.student_id |
| course_id | int | FK → course.course_id |
| semester_id | int | FK → semester.semester_id |
| score | double | numeric score |
| letter_grade | string | e.g. 'A+' |

### course_schedule
When and where courses are offered. `lecture_days`/`lab_days` are 7-char day
bitmasks (Mon..Sun), e.g. `0101010`.

| Column | Type | Notes |
| --- | --- | --- |
| course_id | int | FK → course.course_id |
| semester_id | int | FK → semester.semester_id |
| staff_id | int | FK → faculty.faculty_id |
| lecture_days | string | 7-char day bitmask |
| lecture_start_hour | int | 24h |
| lecture_duration | int | minutes |
| lab_days | string | 7-char day bitmask |
| lab_start_hour | int | 24h |
| lab_duration | int | minutes |

### degree_plan
Planned course sequences per student.

| Column | Type | Notes |
| --- | --- | --- |
| student_id | string | FK → student.student_id |
| course_id | int | FK → course.course_id |
| course_seq_no | int | order within the plan |
| status | string | e.g. 'completed', 'planned' |
| is_major_ind | int | 0/1 |
| semester_seq_no | int | |

### department
Departments within a school.

| Column | Type | Notes |
| --- | --- | --- |
| department_id | int | PK |
| department_name | string | e.g. 'Aeronautics' |
| department_code | string | e.g. 'AERO', 'COMP' |
| school_id | int | FK → school.school_id |

### school
Schools/colleges within the university.

| Column | Type | Notes |
| --- | --- | --- |
| school_id | int | PK |
| school_name | string | e.g. 'College of Engineering' |
| relative_website_url | string | e.g. '/coe' |
| university_id | int | FK → university.university_id |

### faculty
Instructor details. Joined from `course_schedule.staff_id`.

| Column | Type | Notes |
| --- | --- | --- |
| faculty_id | int | PK (referenced by course_schedule.staff_id) |
| first_name | string | |
| last_name | string | |
| gender | string | |
| department_id | int | FK → department.department_id |
| tenure_years | int | |
| is_tenured | int | 0/1 |
| title | string | e.g. 'associate professor' |
| dept_chair | int | 0/1 |

### semester
Academic terms and dates.

| Column | Type | Notes |
| --- | --- | --- |
| semester_id | int | PK |
| start_date | string | date |
| end_date | string | date |
| term_name | string | e.g. 'Fall', 'Spring' |
| semester_year | int | |
| school_year_name | string | e.g. '2014-2015' |

### ed_level
Education level descriptions (lookup).

| Column | Type | Notes |
| --- | --- | --- |
| ed_level_id | int | PK |
| ed_level_code | string | e.g. 'NA' |
| ed_level_desc | string | e.g. 'Not provided' |

### university
University metadata (single row for Peculiar U).

| Column | Type | Notes |
| --- | --- | --- |
| university_id | int | PK |
| university_name | string | e.g. 'Peculiar U' |
| website_url | string | |

## Key Relationships

- `student.department_id` → `department.department_id` (a student's program/major)
- `department.school_id` → `school.school_id`
- `school.university_id` → `university.university_id`
- `course.department_id` → `department.department_id`
- `course.school_id` → `school.school_id`
- `course_registration.student_id` → `student.student_id`
- `course_registration.course_id` → `course.course_id`
- `course_registration.semester_id` → `semester.semester_id`
- `course_outcome.student_id` → `student.student_id`
- `course_outcome.course_id` → `course.course_id`
- `course_outcome.semester_id` → `semester.semester_id`
- `course_schedule.course_id` → `course.course_id`
- `course_schedule.staff_id` → `faculty.faculty_id`
- `degree_plan.student_id` → `student.student_id`
- `degree_plan.course_id` → `course.course_id`

## Common Query Patterns

```sql
-- A student's enrollment details (program comes from department)
SELECT s.student_id, s.first_name, s.last_name, d.department_name,
       s.cumulative_gpa, s.enroll_status
FROM student s
JOIN department d ON s.department_id = d.department_id
WHERE s.student_id = '100016';

-- Courses a student has completed
SELECT c.course_code, c.course_name, cr.status
FROM course_registration cr
JOIN course c ON cr.course_id = c.course_id
WHERE cr.student_id = '100016' AND cr.status = 'completed';

-- Most-registered courses in the COMP department
SELECT c.course_code, c.course_name, COUNT(*) AS registrations
FROM course_registration cr
JOIN course c ON cr.course_id = c.course_id
JOIN department d ON c.department_id = d.department_id
WHERE d.department_code = 'COMP'
GROUP BY c.course_code, c.course_name
ORDER BY registrations DESC;
```
