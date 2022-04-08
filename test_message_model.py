"""Message model tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest -v test_message_model.py

from app import app, CURR_USER_KEY, DEFAULT_IMAGE
import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class MessageModelTestCase(TestCase):
    """Test Message Model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

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

        test_message = Message(
            text="testcontent",
            user_id=self.user_id)

        db.session.add_all([test_message])
        db.session.commit()

        self.message_id = test_message.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_message_model(self):
        """Does basic model work?"""

        add_message = Message(
            text="testcontent",
            user_id=self.user_id,
        )

        user = User.query.get(self.user_id)

        db.session.add(add_message)
        db.session.commit()

        self.assertEqual(len(user.messages), 2)
        self.assertEqual(add_message.author, user)
        self.assertEqual(user.messages[1].text, "testcontent")

    def test_message_repr(self):
        """Does the repr method work as expected"""

        message = Message.query.get(self.message_id)

        self.assertEqual(str(
            message), f'<Message #{message.id}: Content: {message.text}, Time: {message.timestamp}, By User#: {message.user_id}>')


    def test_message_is_liked(self):
        """When message is liked, does it successfully commit to "likes" database table?"""

        with self.client as c:
            # with c.session_transaction() as change_session:
            #     change_session[CURR_USER_KEY] = self.user_id

            #TODO: manually write it so no need for flask. 

            resp = c.post(f"/users/follow/{self.user_id2}",
                        follow_redirects=True)

            user = User.query.get(self.user_id)
            user2 = User.query.get(self.user_id2)

            self.assertEqual(resp.status_code, 200)
            self.assertTrue(user.is_following(user2))
            # self.assertIn(user2,user.following)

# Does is_following successfully detect when user1 is following user2?
# Does is_following successfully detect when user1 is not following user2?
# Does is_followed_by successfully detect when user1 is followed by user2?
# Does is_followed_by successfully detect when user1 is not followed by user2?
# Does User.signup successfully create a new user given valid credentials?
# Does User.signup fail to create a new user if any of the validations (eg uniqueness, non-nullable fields) fail?
# Does User.authenticate successfully return a user when given a valid username and password?
# Does User.authenticate fail to return a user when the username is invalid?
# Does User.authenticate fail to return a user when the password is invalid?
