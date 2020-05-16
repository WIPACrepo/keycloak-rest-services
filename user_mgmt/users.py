"""
Handle user actions.
"""
from . import MyHandler


class Users(MyHandler):
    def get(self):
        self.write({})

    def post(self):
        self.write({})


class UserDetails(MyHandler):
    def get(self, user_id):
        self.write({})



class UserGroups(MyHandler):
    def get(self, user_id):
        """Get a user's group membership"""
        self.write({"groups":[]})