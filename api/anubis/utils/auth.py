import logging
from datetime import datetime, timedelta
from typing import Union

import jwt
from flask import request

from anubis.config import config
from anubis.models import User


def load_user(username: Union[str, None]) -> Union[User, None]:
    """
    Load a user by username

    :param username: netid of wanted user
    :return: User object or None
    """
    if username is None:
        return None
    u1 = User.query.filter_by(username=username).first()

    return u1


def current_user() -> Union[User, None]:
    """
    Load current user based on the token

    :return: User or None
    """
    token = request.headers.get('token', default=None) or request.cookies.get('token', default=None)
    if token is None:
        return None

    try:
        decoded = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
    except Exception as e:
        return None

    if 'netid' not in decoded:
        return None

    return load_user(decoded['netid'])


def get_token(username: str) -> Union[str, None]:
    """
    Get token for user by netid

    :param username:
    :return: token string or None (if user not found)
    """

    # Get user
    user: User = load_user(username)

    # Verify user exists
    if user is None:
        return None

    # Create new token
    return jwt.encode({
        'netid': user.username,
        'exp': datetime.utcnow() + timedelta(hours=6),
    }, config.SECRET_KEY, algorithm='HS256').decode()
