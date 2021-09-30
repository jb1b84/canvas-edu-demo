from datetime import datetime
from dotenv import loaddotenv

import csv
import os
import pytz
import requests

# get your own token in canvas
token = os.environ.get('TOKEN')

headers = {"Authorization": "Bearer {}".format(token)}
base_url = 'https://canvas.uw.edu/api/v1/courses'

# university 501, excel for biz etc
ignored_courses = [873225, 1490894, 1104039]

csvData = []


def fetch_course_data(course_id, endpoint):
    # canvas has a pesky per page default of 10
    res = requests.get(
        "{}/{}/{}?per_page=50".format(base_url, course_id, endpoint), headers=headers)
    if res.status_code == 200:
        return res.json()


def get_discussions(course):
    topics = fetch_course_data(course['id'], 'discussion_topics')
    # this is only for console output, could remove
    if topics:
        print('found {} topics'.format(len(topics)))
    else:
        print('no topics for course {}'.format(course['name']))
        return

    for topic in topics:
        # refactor this later but i don't really care right now
        base_due = topic.get('due_at')
        base_unlock = topic.get('unlock_at')

        due_pst, due_cst = prep_dates(base_due)
        unlock_pst, unlock_cst = prep_dates(base_due)

        csvData.append({
            "course": course.get('name'),
            # title instead of name bcuz canvas
            "name": topic.get('title'),
            "type": topic.get('discussion_type'),
            "url": topic.get('html_url'),
            "due date PST": due_pst,
            "due date CST": due_cst,
            "unlock date PST": unlock_pst,
            "unlock date CST": unlock_cst
        })


def get_quizzes(course):
    quizzes = fetch_course_data(course['id'], 'quizzes')
    if quizzes:
        print('found {} quizzes'.format(len(quizzes)))
    else:
        print('no quizzes for course {}'.format(course['name']))
        return

    for quiz in quizzes:
        base_due = quiz.get('due_at')
        base_unlock = quiz.get('unlock_at')

        due_pst, due_cst = prep_dates(base_due)
        unlock_pst, unlock_cst = prep_dates(base_due)

        csvData.append({
            "course": course.get('name'),
            # name <> title flip again
            "name": quiz.get('title'),
            "type": quiz.get('quiz_type'),
            "url": quiz.get('html_url'),
            "due date PST": due_pst,
            "due date CST": due_cst,
            "unlock date PST": unlock_pst,
            "unlock date CST": unlock_cst
        })


def get_assignments(course):
    assignments = fetch_course_data(course['id'], 'assignments')

    if assignments:
        print('found {} assignments'.format(len(assignments)))
    else:
        print('no assignments found for course {}'.format(course['name']))
        return

    for asgn in assignments:
        base_due = asgn.get('due_at')
        base_unlock = asgn.get('unlock_at')

        due_pst, due_cst = prep_dates(base_due)
        unlock_pst, unlock_cst = prep_dates(base_due)

        csvData.append({
            "course": course.get('name'),
            "name": asgn.get('name'),
            # canvas likes to change this up per type
            "type": asgn.get('submission_types'),
            "url": asgn.get('html_url'),
            "due date PST": due_pst,
            "due date CST": due_cst,
            "unlock date PST": unlock_pst,
            "unlock date CST": unlock_cst
        })


def get_courses():
    courses = requests.get(base_url, headers=headers).json()

    # filter out the nonsense courses
    filtered_courses = [
        course for course in courses if course['id'] not in ignored_courses]

    for course in filtered_courses:
        # now get all the good stuff
        get_assignments(course)
        get_quizzes(course)
        get_discussions(course)

    return


def write_csv():
    with open('Q1.Assignments.9.29.21.csv', 'w', newline='') as csvfile:
        fieldnames = ['course', 'name', 'type',
                      'url', 'due date PST', 'due date CST', 'unlock date PST', 'unlock date CST']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in csvData:
            writer.writerow(row)
    return


def prep_dates(base_date):
    if not base_date:
        return '', ''

    # format to print in excel
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'

    # base date in utc
    utc = datetime.strptime(
        base_date, '%Y-%m-%dT%H:%M:%SZ')

    pst = utc.astimezone(pytz.timezone('US/Pacific'))
    cst = utc.astimezone(pytz.timezone('US/Central'))

    # tuple of tz adjusted dates
    return pst.strftime(fmt), cst.strftime(fmt)


if __name__ == "__main__":
    get_courses()
    write_csv()
    print("...csv created!")
