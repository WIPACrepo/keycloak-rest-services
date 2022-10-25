"""
RabbitMQ utilities
"""
import asyncio
import logging

from rest_tools.utils.json_util import json_decode
from wipac_dev_tools import from_environment
import requests
import aio_pika


logger = logging.getLogger('rabbitmq')


class RabbitMQListener:
    """
    RabbitMQ exchange listener.

    Calls `action` with dict message body for each message received.

    Args:
        action (callable): message processing function
        address (str): RabbitMQ server address
        exchange (str): exchange topic
        routing_key (str): routing key regexp pattern
        message_count (int): number of messages to prefetch
        dedup (int): deduplicate multiple requests received over specified time interval
    """
    def __init__(self, action, address=None, exchange=None,
                 routing_key=None, message_count=100, dedup=None):
        config = from_environment({
            'RABBITMQ_URL': 'amqp://keycloak_guest:guest@127.0.0.1/keycloak',
            'RABBITMQ_EXCHANGE': 'amq.topic',
            'RABBITMQ_ROUTING_KEY': 'KK.EVENT.ADMIN.#',
        })

        self.action = action
        self.address = address if address else config['RABBITMQ_URL']
        self.exchange = exchange if exchange else config['RABBITMQ_EXCHANGE']
        self.routing_key = routing_key if routing_key else config['RABBITMQ_ROUTING_KEY']
        self.message_count = message_count
        self.connection = None

        logger.info(f'RabbitMQListener created on {self.address} for {self.exchange} exchange, {self.routing_key} routing key')

        assert dedup is None or dedup >= 0
        self.dedup = dedup
        self.message_queue = []

    async def start(self):
        if self.connection:
            raise RuntimeError('connection already started')

        self.connection = await aio_pika.connect_robust(self.address)

        # Creating channel
        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=self.message_count)
        exchange = await channel.declare_exchange(
            self.exchange, aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declaring queue
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange, routing_key=self.routing_key)

        logger.info(f'started rabbitmq listener on {self.exchange} exchange, {self.routing_key} routing key')

        fn = self._process_dedup if self.dedup else self._process
        await queue.consume(fn)

    async def stop(self):
        if self.connection:
            logger.info(f'closing rabbitmq listener on {self.exchange} exchange, {self.routing_key} routing key')
            await self.connection.close()
            self.connection = None

    async def _process(self, message):
        """Process messages one by one"""
        async with message.process():
            try:
                body = json_decode(message.body)
                if 'representation' in body:
                    try:
                        body['representation'] = json_decode(body['representation'])
                    except Exception:
                        pass
                else:
                    raise Exception(f'unknown message body: {body}')
                await self.action(body)
            except Exception:
                logger.warning('error processing message', exc_info=True)

    async def _process_dedup(self, message):
        """Process messages with deduplication"""
        if not self.message_queue:
            asyncio.create_task(self._process_dedup_helper())
        self.message_queue.append(message)

    async def _process_dedup_helper(self):
        await asyncio.sleep(self.dedup)
        message = self.message_queue.pop()
        self.message_queue = []
        await self._process(message)


def create_user(username, password):
    config = from_environment({
        'RABBITMQ_MGMT_URL': 'http://localhost:15672',
        'RABBITMQ_ADMIN_USER': 'admin',
        'RABBITMQ_ADMIN_PASSWORD': 'admin',
        'RABBITMQ_VHOST': 'keycloak',
        'RABBITMQ_EXCHANGE': 'amq.topic',
    })
    auth = (config['RABBITMQ_ADMIN_USER'], config['RABBITMQ_ADMIN_PASSWORD'])

    r = requests.put(f'{config["RABBITMQ_MGMT_URL"]}/api/users/{username}', json={'password': password, 'tags': ''}, auth=auth)
    r.raise_for_status()
    r = requests.put(f'{config["RABBITMQ_MGMT_URL"]}/api/permissions/{config["RABBITMQ_VHOST"]}/{username}',
                     json={'configure': '.*', 'write': '.*', 'read': '.*'}, auth=auth)
    r.raise_for_status()
    r = requests.put(f'{config["RABBITMQ_MGMT_URL"]}/api/topic-permissions/{config["RABBITMQ_VHOST"]}/{username}',
                     json={'exchange': config['RABBITMQ_EXCHANGE'], 'write': '', 'read': '.*'}, auth=auth)
    r.raise_for_status()


if __name__ == "__main__":
    import argparse
    from pprint import pprint

    parser = argparse.ArgumentParser(description='RabbitMQ Exchange Listener')
    parser.add_argument('--address', help='RabbitMQ address')
    parser.add_argument('--exchange', help='RabbitMQ exchange')
    parser.add_argument('--routing-key', help='RabbitMQ routing key')
    parser.add_argument('--message-count', type=int, help='message buffer count')
    parser.add_argument('--dedup', type=int, help='dedup time (default: disabled)')
    args = vars(parser.parse_args())
    for a in list(args):
        if args[a] is None:
            args.pop(a)

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    async def action(body):
        pprint(body)

    loop = asyncio.get_event_loop()
    listener = RabbitMQListener(action, **args)
    loop.create_task(listener.start())
    loop.run_forever()
