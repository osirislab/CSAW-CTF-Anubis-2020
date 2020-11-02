#!/usr/bin/env python3

import os
import sys
import json
import logging
import traceback
from redis import Redis

import assignment
import requests
import yaml

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(logging.StreamHandler())


from utils import registered_tests, build_function
from utils import fix_permissions, Panic, DEBUG


TOKEN = os.environ.get('TOKEN')
SUBMISSION_ID = os.environ.get('SUBMISSION_ID')
CODE = sys.argv[1]


def report_panic(message: str, traceback: str, ):
    """
    Report and error to the API

    :param message: error message
    :param traceback: optional traceback
    :return:
    """
    data = {
        'token': TOKEN,
        'submission_id': SUBMISSION_ID,
        'message': message,
        'traceback': traceback,
    }
    logging.info('report_error {}'.format(json.dumps(data, indent=2)))
    post('/pipeline/report/panic/{}'.format(SUBMISSION_ID), data)


def post(path: str, data: dict, params=None):
    if params is None:
        params = {}
    headers = {'Content-Type': 'application/json'}
    params['token'] = TOKEN

    if DEBUG:
        logging.info("post: {} data: {}".format(path, data))
        return None

    # Attempt to contact the pipeline API
    try:
        res = requests.post(
            'http://anubis-pipeline-api:5000' + path,
            headers=headers,
            params=params,
            json=data,
        )
    except:
        logging.error('UNABLE TO REPORT POST TO PIPELINE API')
        exit(0)

    # If the call to the api failed we're in trouble,
    # and need to abort.
    if res.status_code != 200:
        logging.error('UNABLE TO REPORT POST TO PIPELINE API')
        exit(0)

    return res


def report_state(state: str, params=None):
    """
    Report a state update for the current submission

    :param params:
    :param state: text representation of state
    :return:
    """
    data = {
        'token': TOKEN,
        'submission_id': SUBMISSION_ID,
        'state': state,
    }
    logging.info('report_state {}'.format(json.dumps(data, indent=2)))
    post('/pipeline/report/state/{}'.format(SUBMISSION_ID), data, params=params)


def report_build_results(stdout: str, passed: bool):
    """
    Report the results of a given build.

    :param stdout:
    :param passed:
    :return:
    """
    data = {
        'token': TOKEN,
        'submission_id': SUBMISSION_ID,
        # 'stdout': base64.b16encode(stdout).decode(),
        'stdout': stdout,
        'passed': passed,
    }
    logging.info('report_build {}'.format(json.dumps(data, indent=2)))
    post('/pipeline/report/build/{}'.format(SUBMISSION_ID), data)


def report_test_results(test_name: str, stdout: str, message: str, passed: bool):
    """
    Report a single test result to the pipeline API.

    :param test_name:
    :param stdout:
    :param message:
    :param passed:
    :return:
    """
    data = {
        'token': TOKEN,
        'submission_id': SUBMISSION_ID,
        'test_name': test_name,
        'stdout': stdout,
        'message': message,
        'passed': passed,
    }
    logging.info('report_test_results {}'.format(json.dumps(data, indent=2)))
    post('/pipeline/report/test/{}'.format(SUBMISSION_ID), data)


def get_assignment_data() -> dict:
    """
    Load the assignment metadata out from the assignment yaml file

    :return:
    """

    # Figure out filename
    assignment_filename = None
    for assignment_filename_option in ['assignment.yml', 'assignment.yaml']:
        if os.path.isfile(assignment_filename_option):
            assignment_filename = assignment_filename_option
            break

    # Make sure we figured out the metadata filename
    if assignment_filename is None:
        report_panic('No assignment.yml was found', '')
        exit(0)

    # Load yaml
    with open(assignment_filename, 'r') as f:
        try:
            assignment_data = yaml.safe_load(f.read())
        except yaml.YAMLError:
            report_panic('Unable to read assignment yaml', traceback.format_exc())

    logging.info(assignment_data)

    return assignment_data


def run_build(assignment_data: dict):
    """
    Build the student repo.

    :param assignment_data: assignment meta
    :return:
    """
    # build
    report_state('Running Build...')
    result = build_function()
    report_build_results(result.stdout, result.passed)
    if not result.passed:
        exit(0)


def run_tests(assignment_data: dict):
    """
    Run the assignment test scripts. Update submission state as you go.

    :param assignment_data:
    :return:
    """

    # Tests
    for test_name in registered_tests:
        report_state('Running test: {}'.format(test_name))
        result = registered_tests[test_name]()

        report_test_results(test_name, result.stdout, result.message, result.passed)


def setup():
    with open('student/code.cpp', 'w') as f:
        f.write(CODE)
        f.close()
    fix_permissions()


def main():
    try:
        assignment_data = get_assignment_data()
        setup()
        os.chdir('./student')

        run_build(assignment_data)
        run_tests(assignment_data)
        report_state('Finished!', params={'processed': '1'})
    except Panic as e:

        try:
            report_panic(repr(e), traceback.format_exc())
        except Exception:
            # If we reach here this is a huge yikes. It means the pipeline api
            # is unreachable to report our error to. As a last ditch effort, we
            # will throw our panic at redis
            redis = Redis('redis')
            redis.setex("panic:{}".format(SUBMISSION_ID), 60, traceback.format_exc())

    except Exception as e:
        report_panic(repr(e), traceback.format_exc())


if __name__ == '__main__':
    main()
