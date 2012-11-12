#!/usr/bin/env python

from flaskext.script import Manager

from app import app, db
manager = Manager(app)


@manager.command
def createdb(drop=False):
    """
    Create the initial database structure.
    """

    if drop:
        db.drop_all()

    db.create_all()


@manager.command
def fetch():

    from pep.tasks import fetch_peps
    print fetch_peps()

if __name__ == "__main__":
    manager.run()
