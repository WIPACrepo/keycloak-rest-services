import logging

from tornado.web import HTTPError
from tornado.escape import json_decode, json_encode
from rest_tools.server import RestHandler

class MyHandler(RestHandler):
    def initialize(self, db=None, token=None, **kwargs):
        super().initialize(**kwargs)
        self.db = db
        self.token = token

    def write(self, chunk):
        """
        Writes the given chunk to the output buffer.

        A copy of the Tornado src, without the list json restriction.
        """
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")
        if not isinstance(chunk, (bytes, str, dict, list)):
            message = "write() only accepts bytes, str, dict, and list objects"
            raise TypeError(message)
        if isinstance(chunk, (dict,list)):
            chunk = json_encode(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")
        self._write_buffer.append(chunk)

    def json_filter(self, req_fields, opt_fields):
        """
        Filter json body data.

        Args:
            req_fields (dict): required fields and type
            opt_fields (dict): optional fields and type
        Returns:
            dict: data
        """
        incoming_data = json_decode(self.request.body)
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
        return data

    async def get_admin_groups(self):
        if '/admin' in self.auth_data['groups']: # super admin - all groups
            admin_groups = await krs.groups.list_groups(token=self.token)
        else:
            admin_groups = [g[:-6] for g in self.auth_data['groups'] if g.endswith('/_admin')]
        groups = set()
        for group in admin_groups:
            val = group.strip('/').split('/')
            if len(val) > 1 and val[0] != 'institutions':
                groups.add(group)
        return groups

    async def get_admin_institutions(self):
        if '/admin' in self.auth_data['groups']: # super admin - all institutions
            admin_groups = await krs.groups.list_groups(token=self.token)
        else:
            admin_groups = [g[:-6] for g in self.auth_data['groups'] if g.endswith('/_admin')]
        insts = {}
        for group in admin_groups:
            val = group.strip('/').split('/')
            if len(val) == 3 and val[0] == 'institutions':
                insts[val[1]] = val[2]
        logging.info(f'get_admin_instutitons: {insts}')
        return insts