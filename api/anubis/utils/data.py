from email.mime.text import MIMEText
from json import dumps
from os import environ
from smtplib import SMTP
from typing import List, Union, Dict

from flask import Response

from anubis.config import config
from anubis.models import User, Class_, InClass, Assignment, Submission
from anubis.models import db
from anubis.utils.auth import load_user
from anubis.utils.cache import cache
from anubis.utils.redis_queue import enque_submission_rpc


def is_debug() -> bool:
    """
    Returns true if the app is running in debug mode

    :return:
    """
    return config.DEBUG


#@cache.memoize(timeout=60, unless=is_debug)
def get_classes(netid: str):
    """
    Get all classes a given netid is in

    :param netid:
    :return:
    """
    # Query for classes
    classes = Class_.query.join(InClass).join(User).filter(
        User.username == netid
    ).all()

    # Convert to list of data representation
    return [c.data for c in classes]


#@cache.memoize(timeout=60, unless=is_debug)
def get_assignments(netid: str, class_name=None) -> Union[List[Dict[str, str]], None]:
    """
    Get all the current assignments for a netid. Optionally specify a class_name
    to filter by class.

    :param netid: netid of user
    :param class_name: optional class name
    :return: List[Assignment.data]
    """
    # Load user
    user = load_user(netid)

    # Verify user exists
    if user is None:
        return None

    filters = []
    if class_name is not None:
        filters.append(Class_.name == class_name)

    assignments = Assignment.query.join(Class_).join(InClass).join(User).filter(
        User.username == netid,
        Assignment.hidden == False,
        *filters
    ).order_by(Assignment.due_date.desc()).all()

    a = [a.data for a in assignments]
    for assignment_data in a:
        assignment_data['has_submission'] = Submission.query.join(User).join(Assignment).filter(
            Assignment.id == assignment_data['id'],
            User.username == netid,
        ).first() is not None

    return a


#@cache.memoize(timeout=3, unless=is_debug)
def get_submissions(netid: str, class_name=None, assignment_name=None) -> Union[List[Dict[str, str]], None]:
    """
    Get all submissions for a given netid. Cache the results. Optionally specify
    a class_name and / or assignment_name for additional filtering.

    :param netid: netid of student
    :param class_name: name of class
    :param assignment_name: name of assignment
    :return:
    """
    # Load user
    user = load_user(netid)

    # Verify user exists
    if user is None:
        return None

    # Build filters
    filters = []
    if class_name is not None:
        filters.append(Class_.name == class_name)
    if assignment_name is not None:
        filters.append(Assignment.name == assignment_name)

    owner = User.query.filter(User.username == netid).first()
    submissions = Submission.query.join(Assignment).join(Class_).join(InClass).join(User).filter(
        Submission.owner_id == owner.id,
        *filters
    ).all()

    return [s.full_data for s in submissions]


def regrade_submission(submission):
    """
    Regrade a submission

    :param submission: Submissions
    :return: dict response
    """

    if not submission.processed:
        return error_response('submission currently being processed')

    submission.processed = False
    submission.state = 'Waiting for resources...'
    submission.init_submission_models()

    enque_submission_rpc(submission.id)

    return success_response({'message': 'regrade started'})


def jsonify(data, status_code=200):
    """
    Wrap a data response to set proper headers for json
    """
    res = Response(dumps(data))
    res.status_code = status_code
    res.headers['Content-Type'] = 'application/json'
    res.headers['Access-Control-Allow-Origin'] = 'https://nyu.cool' \
        if not environ.get('DEBUG', False) \
        else 'https://localhost'
    return res


def error_response(error_message: str) -> dict:
    """
    Form an error REST api response dict.

    :param error_message: string error message
    :return:
    """
    return {
        'success': False,
        'error': error_message,
        'data': None,
    }


def success_response(data: Union[dict, str, None]) -> dict:
    """
    Form a success REST api response dict.

    :param data:
    :return:
    """
    return {
        'success': True,
        'error': None,
        'data': data,
    }
