"""Message model tests."""

# run these tests like:
#
# FLASK_ENV=production python -m unittest -v test_message_model.py

from app import app, CURR_USER_KEY, DEFAULT_IMAGE
import os
from unittest import TestCase

from models import db, User, Message, Follows, Like

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

        user = User.query.get(self.user_id)
        user2 = User.query.get(self.user_id2)
        msg = Message.query.get(self.message_id)

        user2.liked_messages.append(msg)
        db.session.commit()

        self.assertIn(msg,user2.liked_messages)
        self.assertNotIn(msg,user.liked_messages)

    def test_delete_message(self):
        """Can user delete their own message?"""

        user = User.query.get(self.user_id)
        msg = Message.query.get(self.message_id)

        Message.query.filter_by(id=self.message_id).delete()
        db.session.commit()

        self.assertNotIn(msg,user.messages)

