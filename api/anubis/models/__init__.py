import base64
import logging
import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_json import MutableJson

db = SQLAlchemy()


class Config(db.Model):
    __tablename__ = 'config'
    key = db.Column(db.String(128), primary_key=True)
    value = db.Column(db.String(2048))


class User(db.Model):
    __tablename__ = 'user'

    # id
    id = db.Column(db.String(128), primary_key=True, default=lambda: base64.b16encode(os.urandom(32)).decode())

    # Fields
    username = db.Column(db.String(128), primary_key=True, unique=True, index=True)
    password = db.Column(db.String(128))

    # Timestamps
    created = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    in_class = db.relationship('InClass', cascade='all,delete')

    @property
    def data(self):
        return {
            'id': self.id,
            'netid': self.username,
        }


class Class_(db.Model):
    __tablename__ = '_class'

    # id
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Fields
    name = db.Column(db.String(256), nullable=False)
    professor = db.Column(db.String(256), nullable=False)

    in_class = db.relationship('InClass', cascade='all,delete')
    assignments = db.relationship('Assignment', cascade='all,delete')

    @property
    def total_assignments(self):
        return len(list(self.assignments))

    @property
    def open_assignments(self):
        now = datetime.now()
        return Assignment.query.filter(
            Assignment.class_id == self.id,
            Assignment.release_date >= now,
            Assignment.due_date <= now
        ).count()

    @property
    def data(self):
        return {
            'name': self.name,
            'professor': self.professor,

            'total_assignments': self.total_assignments,
            'open_assignment': self.open_assignments,
        }


class InClass(db.Model):
    __tablename__ = 'in_class'

    # Foreign Keys
    owner_id = db.Column(db.String(128), db.ForeignKey(User.id), primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey(Class_.id), primary_key=True)

    owner = db.relationship(User, cascade='all,delete')
    class_ = db.relationship(Class_, cascade='all,delete')

    @property
    def data(self):
        return {'owner_id': self.owner_id, 'class_id': self.class_id}


class Assignment(db.Model):
    __tablename__ = 'assignment'

    # id
    id = db.Column(db.String(128), primary_key=True, default=lambda: base64.b16encode(os.urandom(32)).decode())

    # Foreign Keys
    class_id = db.Column(db.Integer, db.ForeignKey(Class_.id), index=True)

    # Fields
    name = db.Column(db.String(256), nullable=False, unique=True)
    hidden = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text, nullable=True)
    code = db.Column(db.String(1500), nullable=False)
    pipeline_image = db.Column(db.String(256), unique=True, nullable=True)

    # Dates
    release_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    grace_date = db.Column(db.DateTime, nullable=True)

    class_ = db.relationship(Class_, cascade='all,delete')
    tests = db.relationship('AssignmentTest', cascade='all,delete')

    @property
    def data(self):
        return {
            'id': self.id,
            'name': self.name,
            'due_date': str(self.due_date),
            'course': self.class_.data,
            'description': self.description,

            'tests': [t.data for t in self.tests]
        }

    @property
    def meta_shape(self):
        return {
            'assignment': {
                "name": str,
                "class": str,
                "unique_code": str,
                "hidden": bool,
                "pipeline_image": str,
                "release_date": str,
                "due_date": str,
                "grace_date": str,
                "description": str,
            }
        }


class AssignmentTest(db.Model):
    __tablename__ = 'assignment_test'

    # id
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    assignment_id = db.Column(db.String(128), db.ForeignKey(Assignment.id))

    # Fields
    name = db.Column(db.String(128), index=True)

    # Relationships
    assignment = db.relationship(Assignment, cascade='all,delete')

    @property
    def data(self):
        return {
            'name': self.name
        }


class Submission(db.Model):
    __tablename__ = 'submission'

    # id
    id = db.Column(db.String(128), primary_key=True, default=lambda: base64.b16encode(os.urandom(32)).decode())

    # Foreign Keys
    owner_id = db.Column(db.String(128), db.ForeignKey(User.id), index=True, nullable=True)
    assignment_id = db.Column(db.String(128), db.ForeignKey(Assignment.id), index=True, nullable=False)

    # Timestamps
    created = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Fields
    processed = db.Column(db.Boolean, default=False)
    state = db.Column(db.String(128), default='')
    errors = db.Column(MutableJson, default=None, nullable=True)
    token = db.Column(db.String(64), default=lambda: base64.b16encode(os.urandom(32)).decode())
    code = db.Column(db.String(1500), nullable=False)

    # Relationships
    owner = db.relationship(User, cascade='all,delete')
    assignment = db.relationship(Assignment, cascade='all,delete')
    build = db.relationship('SubmissionBuild', cascade='all,delete', uselist=False)
    test_results = db.relationship('SubmissionTestResult', cascade='all,delete')

    def init_submission_models(self):
        """
        Create adjacent submission models.

        :return:
        """
        # If the models already exist, yeet
        if len(self.test_results) != 0:
            SubmissionTestResult.query.filter_by(submission_id=self.id).delete()
        if self.build is not None:
            SubmissionBuild.query.filter_by(submission_id=self.id).delete()

        # Commit deletions (if necessary)
        db.session.commit()

        # Find tests for the current assignment
        tests = AssignmentTest.query.filter_by(assignment_id=self.assignment_id).all()

        logging.error('found tests: {}'.format(list(map(lambda x: x.data, tests))))

        for test in tests:
            tr = SubmissionTestResult(submission=self, assignment_test=test)
            db.session.add(tr)
        sb = SubmissionBuild(submission=self)
        db.session.add(sb)

        self.processed = False
        self.state = 'Reset'
        db.session.add(self)

        # Commit new models
        db.session.commit()

    @property
    def url(self):
        return '/submission/{}'.format(self.id)

    @property
    def netid(self):
        if self.owner is not None:
            return self.owner.username
        return 'null'

    @property
    def tests(self):
        """
        Get a list of dictionaries of the matching Test, and TestResult
        for the current submission.

        :return:
        """

        # Query for matching AssignmentTests, and TestResults
        tests = SubmissionTestResult.query.filter_by(
            submission_id=self.id,
        ).all()

        logging.error('Loaded tests {}'.format(tests))

        # Convert to dictionary data
        return [
            {'test': result.assignment_test.data, 'result': result.data}
            for result in tests
        ]

    @property
    def data(self):
        return {
            'id': self.id,
            'assignment_name': self.assignment.name,
            'assignment_due': str(self.assignment.due_date),
            'url': self.url,
            'processed': self.processed,
            'state': self.state,
            'created': str(self.created),
            'last_updated': str(self.last_updated),
        }

    @property
    def full_data(self):
        data = self.data

        # Add connected models
        data['tests'] = self.tests
        data['build'] = self.build.data if self.build is not None else None

        return data


class SubmissionTestResult(db.Model):
    __tablename__ = 'submission_test_result'

    # id
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    submission_id = db.Column(db.String(128), db.ForeignKey(Submission.id), primary_key=True)
    assignment_test_id = db.Column(db.Integer, db.ForeignKey(AssignmentTest.id), primary_key=True)

    # Timestamps
    created = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Fields
    stdout = db.Column(db.Text)
    message = db.Column(db.Text)
    passed = db.Column(db.Boolean)

    # Relationships
    submission = db.relationship(Submission, cascade='all,delete')
    assignment_test = db.relationship(AssignmentTest, cascade='all,delete')

    @property
    def data(self):
        return {
            'id': self.id,
            'test_name': self.assignment_test.name,
            'passed': self.passed,
            'message': self.message,
            'stdout': self.stdout,
            'created': str(self.created),
            'last_updated': str(self.last_updated),
        }

    @property
    def stat_data(self):
        data = self.data
        del data['stdout']
        return data

    def __str__(self):
        return 'testname: {}\nerrors: {}\npassed: {}\n'.format(
            self.testname,
            self.errors,
            self.passed,
        )


class SubmissionBuild(db.Model):
    __tablename__ = 'submission_build'

    # id
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    submission_id = db.Column(db.String(128), db.ForeignKey(Submission.id), index=True)

    # Timestamps
    created = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Fields
    stdout = db.Column(db.Text)
    passed = db.Column(db.Boolean)

    # Relationships
    submission = db.relationship(Submission, cascade='all,delete')

    @property
    def data(self):
        return {
            'stdout': self.stdout,
            'passed': self.passed,
        }

    @property
    def stat_data(self):
        data = self.data
        del data['stdout']
        return data
