"""User model tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest -v test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY, DEFAULT_IMAGE
from flask import g, session
from sqlalchemy.exc import IntegrityError

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        # TODO: Likes?

        self.client = app.test_client()

        test_user = User.signup(
                    email="test@test.com",
                    username="testuser",
                    password="HASHED_PASSWORD",
                    image_url=DEFAULT_IMAGE)

        test_user2 = User.signup(
                    email="test2@test2.com",
                    username="testuser2",
                    password="HASHED_PASSWORD2",
                    image_url=DEFAULT_IMAGE)


        db.session.add_all([test_user, test_user2])
        db.session.commit()

        self.user_id = test_user.id
        self.user_id2 = test_user2.id


    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        adduser = User(
            email="testadd@test.com",
            username="testadduser",
            password="ADDHASHED_PASSWORD"
        )

        db.session.add(adduser)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(adduser.messages), 0)
        self.assertEqual(len(adduser.followers), 0)

    def test_user_repr(self):
        """Does the repr method work as expected"""

        user = User.query.get(self.user_id)

        self.assertEqual(str(user), f'<User #{user.id}: {user.username}, {user.email}>')


    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        with self.client as c:
            with c.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.user_id

            resp = c.post(f"/users/follow/{self.user_id2}",
                        follow_redirects=True)

            user = User.query.get(self.user_id)
            user2 = User.query.get(self.user_id2)

            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.is_following(user2))
            # self.assertIn(user2,user.following)


    def test_not_following(self):
        """Does is_following successfully detect when user1 is not following user2?"""

        with self.client as c:
            with c.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.user_id

            user = User.query.get(self.user_id)
            user2 = User.query.get(self.user_id2)

            self.assertFalse(user.is_following(user2))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""

        with self.client as c:
            with c.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.user_id2

            resp = c.post(f"/users/follow/{self.user_id}",
                        follow_redirects=True)

            user = User.query.get(self.user_id)
            user2 = User.query.get(self.user_id2)

            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.is_followed_by(user2))

    def test_not_followed_by(self):
        """ Does is_followed_by successfully detect when user1 is not followed by user2? """

        with self.client as c:
            with c.session_transaction() as change_session:
                change_session[CURR_USER_KEY] = self.user_id2

            user = User.query.get(self.user_id)
            user2 = User.query.get(self.user_id2)

            self.assertFalse(user.is_followed_by(user2))

    def test_user_signup(self):
        """ Does User.signup successfully create a new user given valid credentials? """

        new_user = User.signup(
            email="testadd@test.com",
            username="testadduser",
            password="ADDHASHED_PASSWORD",
            image_url= DEFAULT_IMAGE
        )
        db.session.commit()

        self.assertIsNotNone(User.query.get(new_user.id))

    def test_user_signup_fail(self):
        """Does User.signup fail to create a new user if any of the validations (eg uniqueness, non-nullable fields) fail?"""

        User.signup(
            email="testadd@test.com",
            username="testuser",
            password= "HASHED",
            image_url= DEFAULT_IMAGE
        )

        self.assertRaises(IntegrityError, db.session.commit)

    def test_user_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""

        authenticated_user = User.authenticate("testuser","HASHED_PASSWORD")

        user = User.query.get(self.user_id)

        self.assertEqual(authenticated_user,user)

    def test_user_authenticate_username_fail(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        authenticated_user = User.authenticate("ttttt","HASHED_PASSWORD")

        self.assertFalse(authenticated_user)

    def test_user_authenticate_password_fail(self):
        """ Does User.authenticate fail to return a user when the password is invalid?"""

        authenticated_user = User.authenticate("testuser","qqqqqqq")

        self.assertFalse(authenticated_user)

