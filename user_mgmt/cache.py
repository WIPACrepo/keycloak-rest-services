import logging

from cachetools import TTLCache

from krs.groups import list_groups, group_info, group_info_by_id, get_group_membership_by_id
from krs.institutions import list_insts


logger = logging.getLogger('cache')


class KeycloakGroupCache:
    """
    A TTL cache for Keycloak group requests.

    Args:
        ttl (int): number of seconds to keep items in cache (default: 3600)
        krs_client (RestClient): rest client for talking to Keycloak
    """
    def __init__(self, ttl=3600, krs_client=None):
        self._ttl = ttl
        self._krs_client = krs_client
        self._group_ids = TTLCache(1000000, ttl*24)  # group ids (shouldn't change)
        self._group_info = TTLCache(10000000, ttl*24)  # group info by id (shouldn't change)
        self._group_list = TTLCache(10000000, ttl/60)  # group_path list for all groups
        self._group_members = TTLCache(10000000, ttl)  # group memberships

    async def list_groups(self):
        if 'groups' not in self._group_list:
            logger.info('list_groups() is not cached')
            ret = await list_groups(rest_client=self._krs_client)
            self._group_list['groups'] = ret
        return self._group_list['groups']

    async def list_institutions(self):
        if 'inst' not in self._group_list:
            logger.info('list_institutions() is not cached')
            ret = await list_insts(rest_client=self._krs_client)
            self._group_list['inst'] = ret
        return self._group_list['inst']

    async def get_group_id(self, group_path):
        if group_path not in self._group_ids:
            logger.info(f'get_group_id({group_path}) is not cached')
            ret = await group_info(group_path, rest_client=self._krs_client)
            self._group_ids[group_path] = ret['id']
        return self._group_ids[group_path]

    async def get_group_info_from_id(self, group_id):
        if group_id not in self._group_info:
            logger.info(f'get_group_info_from_id({group_id}) is not cached')
            ret = await group_info_by_id(group_id, rest_client=self._krs_client)
            self._group_info[group_id] = ret
        return self._group_info[group_id]

    async def get_members(self, group_path):
        if group_path not in self._group_members:
            logger.info(f'get_members({group_path}) is not cached')
            group_id = await self.get_group_id(group_path)
            ret = await get_group_membership_by_id(group_id, rest_client=self._krs_client)
            self._group_members[group_path] = ret
        return self._group_members[group_path]

    def invalidate(self, path=None):
        if not path:
            self._group_members.clear()
        else:
            for k in list(self._group_members):
                if k.startswith(path):
                    del self._group_members[k]
