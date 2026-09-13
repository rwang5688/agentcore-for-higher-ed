"""Live Student Information System query tool (self-contained thick-client copy).

Defines the ``query_student_db`` Strands tool, which runs SQL against the
``education_workshop_db`` Athena database by invoking the query Lambda (named in
the ``ATHENA_LAMBDA_NAME`` environment variable) via boto3. Because it uses
boto3 directly, it inherits the environment's IAM credentials automatically.
"""

import json

import boto3
from strands import tool

from config import get_config

# Constructed lazily so importing this module never requires AWS credentials.
_lambda_client = None


def _get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client(
            "lambda", region_name=get_config().aws_region
        )
    return _lambda_client


@tool
def query_student_db(sql: str) -> list | dict:
    """Query the Peculiar University Student Information System with SQL.

    Runs a read-only SQL query against the ``education_workshop_db`` Amazon
    Athena database (Presto/Trino SQL dialect) and returns the matching rows.
    Use this for live student records, course registrations, degree plans,
    grades, schedules, and related structured data. The dataset is scoped to
    the College of Engineering (departments: Aeronautics/AERO,
    Computer Science/COMP, Data Science, Engineering, Environment and Natural
    Resources).

    Tables and key columns:
      - student(student_id, first_name, last_name, cumulative_gpa,
        enroll_status, department_id, admit_type, high_school_gpa, ...)
        NOTE: no `program` column; a student's program is their department.
      - course(course_id, course_name, course_level, course_code,
        school_id, department_id)
      - course_registration(student_id, course_id, semester_id, status,
        date_registered, date_dropped)  -- status e.g. 'completed','registered','dropped'
      - course_outcome(student_id, course_id, semester_id, score, letter_grade)
      - course_schedule(course_id, semester_id, staff_id, lecture_days, ...)
      - degree_plan(student_id, course_id, course_seq_no, status, is_major_ind,
        semester_seq_no)
      - department(department_id, department_name, department_code, school_id)
      - school(school_id, school_name, university_id)
      - faculty(faculty_id, first_name, last_name, department_id, title, ...)
        -- referenced by course_schedule.staff_id
      - semester(semester_id, start_date, end_date, term_name, semester_year)
      - ed_level(ed_level_id, ed_level_code, ed_level_desc)
      - university(university_id, university_name, website_url)

    Key relationships:
      student.department_id -> department.department_id;
      department.school_id -> school.school_id;
      course.department_id -> department.department_id;
      course_registration/course_outcome/degree_plan.student_id -> student.student_id;
      *.course_id -> course.course_id; *.semester_id -> semester.semester_id.

    SQL notes (Athena/Presto/Trino):
      - Use single quotes for string literals: WHERE student_id = '100016'.
      - student_id is a string; most other _id columns are integers.
      - A student's completed courses: join course_registration to course on
        course_id, filter status = 'completed'.

    Args:
        sql: A single SQL query string to run against education_workshop_db.

    Returns:
        On success, a list of row dicts (one dict per row). On failure, a dict
        with an "error" key describing what went wrong (e.g. an Athena error
        returned by the Lambda, or a non-200 status code).
    """
    lambda_name = get_config().athena_lambda_name
    try:
        response = _get_lambda_client().invoke(
            FunctionName=lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps({"sql": sql}).encode("utf-8"),
        )
    except Exception as exc:  # boto3/client errors -> surface to the agent
        return {"error": f"Failed to invoke Lambda '{lambda_name}': {exc}"}

    payload = json.loads(response["Payload"].read())

    status_code = payload.get("statusCode")
    if status_code != 200:
        return {"error": f"Query failed (statusCode {status_code}): {payload.get('body')}"}

    body = json.loads(payload["body"])
    return body.get("result", [])
