"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

        testmsg = Message(text="testmessage",
                          user_id=self.testuser.id)

        db.session.add(testmsg)
        db.session.commit()

        self.testmsg_id = testmsg.id

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msgs = Message.query.filter_by(user_id=self.testuser.id)
            self.assertEqual(msgs[1].text, "Hello")
            self.assertEqual(msgs.count(), 2)

    def test_delete_message(self):
        """When you’re logged in, can you delete a message as yourself?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post(f"/messages/{self.testmsg_id}/delete")

            self.assertEqual(resp.status_code, 302)

            msgs = Message.query.filter_by(user_id=self.testuser.id)
            self.assertEqual(msgs.count(), 0)

    def test_logout_add_message(self):
        """When you’re logged out, are you prohibited from adding messages?"""

        with self.client as c:
            # with c.session_transaction() as sess:
            #     sess[CURR_USER_KEY] = self.testuser.id

            #     if CURR_USER_KEY in sess:
            #         del sess[CURR_USER_KEY]

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)
            msgs = Message.query.all()

            self.assertNotIn("Hello", msgs[0].text)
            self.assertEqual(len(msgs), 1)

    def test_logout_delete_message(self):
        """When you’re logged out, are you prohibited from deleting messages?"""

        with self.client as c:

            resp = c.post(f"/messages/{self.testmsg_id}/delete")

            self.assertEqual(resp.status_code, 302)
            msgs = Message.query.all()

            self.assertEqual(len(msgs), 1)

    def test_logout_add_message(self):
        """When you’re logged in, are you prohibiting from adding a message as another user?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

                testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

                db.session.commit()

                resp = c.post("/messages/new", data={"text": "Hello"})

                self.assertEqual(resp.status_code, 302)
                msgs = Message.query.all()

                self.assertNotIn("Hello", msgs[0].text)
                self.assertEqual(len(msgs), 1)



# MESS When you’re logged in, are you prohibiting from adding a message as another user?
# MESS When you’re logged in, are you prohibiting from deleting a message as another user?

# USER When you’re logged in, can you see the follower / following pages for any user?
# USER When you’re logged out, are you disallowed from visiting a user’s follower / following pages?

