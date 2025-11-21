import aio_pika
import asyncio
import json
import uuid
from typing import Callable, Dict


class RPCClient:

    def __init__(self, rabbit_url: str):
        self.rabbit_url = rabbit_url
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.pending_futures: Dict[str, asyncio.Future] = {}

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.rabbit_url)
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self._on_response)

    async def _on_response(self, message: aio_pika.IncomingMessage):
        correlation_id = message.correlation_id
        if correlation_id in self.pending_futures:
            future = self.pending_futures.pop(correlation_id)
            payload = json.loads(message.body)
            future.set_result(payload)

    async def call(self, exchange: str, routing_key: str, payload: dict, timeout: float = 10.0):
        correlation_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self.pending_futures[correlation_id] = future

        exchange_obj = await self.channel.get_exchange(exchange)
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            correlation_id=correlation_id,
            reply_to=self.callback_queue.name,
        )

        await exchange_obj.publish(message, routing_key=routing_key)

        return await asyncio.wait_for(future, timeout=timeout)

    async def close(self):
        await self.connection.close()


class RPCWorker:

    def __init__(self, rabbit_url: str, exchange_name: str):
        self.rabbit_url = rabbit_url
        self.exchange_name = exchange_name
        self.handlers: Dict[str, Callable] = {}

    def register_handlers(self, module):
        for attr in dir(module):
            fn = getattr(module, attr)
            if hasattr(fn, "__rpc_handler__"):
                routing_key = fn.__rpc_handler__
                self.handlers[routing_key] = fn
                print(f"[RPCWorker] registered handler for: {routing_key}")

    async def start(self):
        self.connection = await aio_pika.connect_robust(self.rabbit_url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC)

        for routing_key, handler in self.handlers.items():
            queue = await self.channel.declare_queue(routing_key, durable=True)
            await queue.bind(self.exchange, routing_key)
            await queue.consume(self._build_consumer(handler))

        print(f"[RPCWorker] Started for {self.exchange_name}")

    def _build_consumer(self, handler):
        async def _consumer(message: aio_pika.IncomingMessage):
            async with message.process():
                payload = json.loads(message.body)
                result = await handler(payload)
                if message.reply_to:
                    await self.exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode(),
                            correlation_id=message.correlation_id
                        ),
                        routing_key=message.reply_to
                    )
        return _consumer

    async def close(self):
        await self.connection.close()
