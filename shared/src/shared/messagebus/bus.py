import asyncio
import json
import aio_pika
import os
from .decorators import HANDLERS

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "posts_exchange")

async def _send_reply(channel, reply_to, correlation_id, result):
    if not reply_to:
        return
    exchange = await channel.declare_exchange(reply_to, aio_pika.ExchangeType.FANOUT)
    await exchange.publish(
        aio_pika.Message(body=json.dumps(result).encode(), correlation_id=correlation_id),
        routing_key=""
    )

async def _handle(msg, channel):
    async with msg.process():
        handler = HANDLERS.get(msg.routing_key)
        if not handler:
            print("No handler for", msg.routing_key)
            return
        payload = None
        if msg.body:
            try:
                payload = json.loads(msg.body.decode())
            except Exception:
                payload = {"_raw": True}
        # call handler
        if asyncio.iscoroutinefunction(handler):
            result = await handler(payload)
        else:
            result = handler(payload)
        await _send_reply(channel, msg.reply_to, msg.correlation_id, result)

async def start_worker():
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("", exclusive=False, durable=True)
    for rk in HANDLERS.keys():
        await queue.bind(exchange, rk)
    async with queue.iterator() as it:
        async for message in it:
            asyncio.create_task(_handle(message, channel))

def start_worker_sync():
    asyncio.run(start_worker())
