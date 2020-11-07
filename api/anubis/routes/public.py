import string
from datetime import datetime, timedelta

from flask import request, redirect, Blueprint, make_response

from anubis.models import Assignment
from anubis.models import Submission
from anubis.models import db, User, Class_, InClass
from anubis.utils.auth import current_user, load_user, get_token
from anubis.utils.cache import cache
from anubis.utils.data import error_response, success_response, is_debug
from anubis.utils.data import get_classes, get_assignments, get_submissions
from anubis.utils.data import regrade_submission, enque_submission_rpc
from anubis.utils.decorators import json_response, json_endpoint, require_user, load_from_id
from anubis.utils.http import get_request_ip
from anubis.utils.logger import logger
from werkzeug.security import check_password_hash, generate_password_hash

public = Blueprint('public', __name__, url_prefix='/public')


@public.route('/memes')
def public_memes():
    logger.info('rick-roll')
    return redirect('https://www.youtube.com/watch?v=dQw4w9WgXcQ&autoplay=1')


@public.route('/login')
def public_login():
    next_url = request.args.get('next') or '/courses'

    # Load fields
    username: str = request.args.get('username', default=None)
    password: str = request.args.get('password', default=None)
    if username is None or password is None:
        return redirect('/login?error=Missing Fields')

    # Load user
    u: User = load_user(username)

    # Make sure we got one
    if u is None:
        return redirect('/login?error=Invalid username or password')

    # Verify password
    if not check_password_hash(u.password, password):
        return redirect('/login?error=Invalid username or password')

    # Set token cookie
    r = make_response(redirect(next_url))
    r.set_cookie('token', get_token(u.username))

    return r


@public.route('/logout')
def public_logout():
    r = make_response(redirect('/'))
    r.set_cookie('token', '')
    return r


@public.route('/register')
def public_register():
    next_url = request.args.get('next') or '/courses'

    # Load fields
    username: str = request.args.get('username', default=None)
    password: str = request.args.get('password', default=None)
    if username is None or password is None:
        return redirect('/register?error=Missing Fields')

    # Check if user already exists
    u = load_user(username)
    if u is not None:
        return redirect('/register?error=Username is already taken')

    # Create user
    u = User(username=username, password=generate_password_hash(password))

    # Add them to the web hacking class
    c = Class_.query.filter(
        Class_.name == 'Kubernetes 101'
    ).first()
    ic = InClass(owner=u, class_=c)

    # Commit changes
    db.session.add(u)
    db.session.add(ic)
    db.session.commit()

    # Set token cookie
    r = make_response(redirect(next_url))
    r.set_cookie('token', get_token(u.username))

    return r


@public.route('/submit/<string:id>', methods=["POST"])
@require_user
@load_from_id(Assignment, verify_owner=False)
def public_submit_assignment(assignment: Assignment):
    user: User = current_user()

    code = request.form.get('code', default=None)
    if code is None:
        return redirect('/courses/assignment/editor?error={}&assignment={}'.format(
            "Missing Fields".replace(' ', '%20'),
            assignment.id
        ))

    # Verify code length
    if len(code) > 1500:
        return redirect('/courses/assignment/editor?error={}&assignment={}'.format(
            'Please limit your code to 1500 characters'.replace(' ', '%20'),
            assignment.id
        ))

    # Create submission
    s = Submission(assignment=assignment, owner=user, code=code)
    db.session.add(s)
    db.session.commit()

    # Initialize test and build models
    s.init_submission_models()

    # Send submission to testing pipeline
    enque_submission_rpc(s.id)

    return redirect('/courses/assignments/submissions/info?submission={}'.format(s.id))


@public.route('/current-code/<id>')
@require_user
@load_from_id(Assignment, verify_owner=False)
def public_current_submission(assignment: Assignment):
    user: User = current_user()

    # Load most recent submission
    current: Submission = Submission.query.filter(
        Submission.assignment_id == assignment.id,
        Submission.owner_id == user.id,
    ).order_by(Submission.created.desc()).first()

    # If we dont have a recent submission, return starter code
    if current is None:
        return success_response({
            'code': assignment.code
        })

    # Return most recent code submission
    return success_response({
        'code': current.code
    })


@public.route('/classes')
@require_user
@json_response
def public_classes():
    """
    Get class data for current user

    :return:
    """
    user: User = current_user()
    return success_response({
        'classes': get_classes(user.username)
    })


@public.route('/assignments')
@require_user
@json_response
def public_assignments():
    """
    Get all the assignments for a user. Optionally specify a class
    name as a get query.

    /api/public/assignments?class=Intro to OS

    :return: { "assignments": [ assignment.data ] }
    """

    # Get optional class filter from get query
    class_name = request.args.get('class', default=None)

    # Load current user
    user: User = current_user()

    # Get (possibly cached) assignment data
    assignment_data = get_assignments(user.username, class_name)

    # Iterate over assignments, getting their data
    return success_response({
        'assignments': assignment_data
    })


@public.route('/submissions')
@require_user
@json_response
def public_submissions():
    """
    Get all submissions for a given student. Optionally specify class,
    and assignment name filters in get query.


    /api/public/submissions
    /api/public/submissions?class=Intro to OS
    /api/public/submissions?assignment=Assignment 1: uniq
    /api/public/submissions?class=Intro to OS&assignment=Assignment 1: uniq

    :return:
    """
    # Get optional filters
    class_name = request.args.get('class', default=None)
    assignment_name = request.args.get('assignment', default=None)

    # Load current user
    user: User = current_user()

    # Get submissions through cached function
    return success_response({
        'submissions': get_submissions(
            user.username,
            class_name=class_name,
            assignment_name=assignment_name)
    })


@public.route('/submission/<string:submission_id>')
@require_user
@json_response
#@cache.memoize(timeout=1, unless=is_debug)
def public_submission(submission_id: str):
    """
    Get submission data for a given commit.

    :param submission_id:
    :return:
    """
    # Get current user
    user: User = current_user()

    # Try to find commit (verifying ownership)
    s = Submission.query.join(User).filter(
        User.username == user.username,
        Submission.id == submission_id
    ).first()

    # Make sure we caught one
    if s is None:
        return error_response('Commit does not exist'), 406

    # Hand back submission
    return success_response({'submission': s.full_data})


@public.route('/regrade/<string:submission_id>')
@require_user
@json_response
def public_regrade_commit(submission_id):
    """
    This route will get hit whenever someone clicks the regrade button on a
    processed assignment. It should do some validity checks on the commit and
    netid, then reset the submission and re-enqueue the submission job.
    """

    # Load current user
    user: User = current_user()

    # Find the submission
    submission: Submission = Submission.query.join(User).filter(
        Submission.id == submission_id,
        User.username == user.username
    ).first()

    # Verify Ownership
    if submission is None:
        return error_response('invalid commit hash or netid'), 406

    # Regrade
    return regrade_submission(submission)


@public.route('/whoami')
def public_whoami():
    """
    Figure out who you are

    :return:
    """
    u: User = current_user()
    if u is None:
        return success_response(None)
    return success_response({
        'user': u.data,
        'classes': get_classes(u.username),
        'assignments': get_assignments(u.username),
    })
