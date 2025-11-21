import aio_pika
import json
from typing import Callable, Dict


class EventPublisher:
    def __init__(self, rabbit_url: str, exchange_name: str):
        self.rabbit_url = rabbit_url
        self.exchange_name = exchange_name

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.rabbit_url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC)

    async def publish(self, routing_key: str, event: dict):
        await self.exchange.publish(
            aio_pika.Message(body=json.dumps(event).encode()),
            routing_key=routing_key
        )


class EventWorker:
    def __init__(self, rabbit_url: str, exchange_name: str):
        self.rabbit_url = rabbit_url
        self.exchange_name = exchange_name
        self.handlers: Dict[str, Callable] = {}

    def register_handlers(self, module):
        for attr in dir(module):
            fn = getattr(module, attr)
            if hasattr(fn, "__event_handler__"):
                routing_key = fn.__event_handler__
                self.handlers[routing_key] = fn
                print(f"[EventWorker] registered event: {routing_key}")

    async def start(self):
        self.connection = await aio_pika.connect_robust(self.rabbit_url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC)

        for routing_key, handler in self.handlers.items():
            queue = await self.channel.declare_queue(routing_key, durable=True)
            await queue.bind(self.exchange, routing_key)
            await queue.consume(self._build_consumer(handler))

        print(f"[EventWorker] Started for {self.exchange_name}")

    def _build_consumer(self, handler):
        async def _consumer(message: aio_pika.IncomingMessage):
            async with message.process():
                payload = json.loads(message.body)
                await handler(payload)
        return _consumer
