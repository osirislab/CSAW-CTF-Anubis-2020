import os
from datetime import datetime

from anubis.models import db, User, Class_, InClass, Assignment, AssignmentTest, Config
from anubis.app import create_app


def seed():
    app = create_app()

    with app.app_context():
        db.create_all()

        u = User.query.filter_by(username='root').first()
        if u is not None:
            return

        u = User(username='root')
        c = Class_(name='Kubernetes 101', professor='Prof. Wabscale')
        ic = InClass(owner=u, class_=c)
        a = Assignment(
            id='A9FBD997AA5B01D43682EE2920364B147C12C9B59886C9473FAEA9C65C6970D4',
            name='Linked Lists', hidden=False, description='Merge and sort some linked lists',
            pipeline_image='assignment-1', release_date=datetime(2020, 11, 13),
            due_date=datetime(2020, 11, 15),
            grace_date=datetime(2020, 11, 15), code=open(
                os.path.join(os.path.dirname(__file__), 'linkedlist.cpp')
            ).read(),
            class_=c)
        at = AssignmentTest(name='Sorted linked list', assignment=a)
        cg = Config(key='MAX_JOBS', value='10')
        items = [u, c, ic, a, at, cg]
        db.session.add_all(items)
        db.session.commit()


if __name__ == '__main__':
    seed()
