
from rest_tools.server import RestHandler

class MyHandler(RestHandler):
    def initialize(self, db=None, **kwargs):
        super(MyHandler, self).initialize(**kwargs)
        self.db = db
