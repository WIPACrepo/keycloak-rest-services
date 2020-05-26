"""
Handle user registration actions.
"""

import logging
import uuid
from functools import wraps

from tornado.web import HTTPError
from tornado.escape import json_decode
from rest_tools.server import catch_error

from . import MyHandler

class UserRegistration(MyHandler):
    async def get(self):
        self.write({})

    @catch_error
    async def post(self):
        """Register a new user"""
        incoming_data = json_decode(self.request.body)
        req_fields = {
            'institution': str,
            'first_name': str,
            'last_name': str,
        }
        opt_fields = {
            'author_name': str,
        }
        data = {}
        for f in req_fields:
            if f not in incoming_data:
                raise HTTPError(400, f'missing field "{f}"', reason=f'missing field "{f}"')
            elif not isinstance(incoming_data[f], req_fields[f]):
                raise HTTPError(400, reason=f'invalid type for field "{f}"')
            data[f] = incoming_data[f]
        for f in opt_fields:
            if f in incoming_data:
                if not isinstance(incoming_data[f], opt_fields[f]):
                    raise HTTPError(400, reason=f'invalid type for field "{f}"')
                data[f] = incoming_data[f]
        extra_fields = set(incoming_data)-set(req_fields)-set(opt_fields)
        if extra_fields:
            raise HTTPError(400, f'invalid fields: {extra_fields}', reason='extra invalid fields in request')

        data['id'] = uuid.uuid1().hex

        logging.info(await self.db.list_collection_names())

        await self.db.user_registrations.insert_one(data)

        self.set_status(201)
        self.write({})
