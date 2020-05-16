"""
Handle group mamagement actions.
"""
from . import MyHandler

class Groups(MyHandler):
    def get(self):
        self.write({})