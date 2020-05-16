import asyncio
from .server import create_server

create_server()
asyncio.get_event_loop().run_forever()
