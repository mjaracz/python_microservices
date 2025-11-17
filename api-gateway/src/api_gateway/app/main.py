import os
import json
import asyncio
import httpx
import aio_pika
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from shared.messagebus import start_worker_sync  # not used here, but src available
from shared.messagebus import MessagePattern

from auth import ws_authenticate
from ws_manager import connect_user, disconnect_user, join_room, leave_room, send_to_user, send_to_room
from middleware.metrics_middleware import MetricsMiddleware

app = FastAPI()
app.add_middleware(MetricsMiddleware)

POSTS_EX = os.getenv("POSTS_EXCHANGE", "posts_exchange")
USERS_EX = os.getenv("USERS_EXCHANGE", "users_exchange")
RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

@app.on_event("startup")
async def startup():
    app.state.rabbit = await aio_pika.connect_robust(RABBIT_URL)
    app.state.channel = await app.state.rabbit.channel()
    app.state.callback_queue = await app.state.channel.declare_queue(exclusive=True)
    async def on_response(msg: aio_pika.IncomingMessage):
        async with msg.process():
            try:
                payload = json.loads(msg.body.decode())
                user_id = payload.get("user_id")
                # deliver to websocket client(s)
                await send_to_user(str(user_id), {"type":"rpc_response","payload":payload})
            except Exception as e:
                print("response handling error", e)
    await app.state.callback_queue.consume(on_response)

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    try:
        payload = await ws_authenticate(ws)
    except Exception:
        return
    user_id = str(payload.get("user_id"))
    await ws.accept()
    await connect_user(user_id, ws)
    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action")
            if action == "get_posts":
                
                ex = await app.state.channel.declare_exchange(POSTS_EX, aio_pika.ExchangeType.TOPIC)
                corr = data.get("correlation_id")
                await ex.publish(
                    aio_pika.Message(body=json.dumps({"type":"get_user_posts","user_id":user_id,"correlation_id":corr}).encode(),
                                     reply_to=app.state.callback_queue.name,
                                     correlation_id=corr),
                    routing_key="post.get"
                )
            else:
                await ws.send_json({"error":"unknown action"})
    except WebSocketDisconnect:
        await disconnect_user(user_id, ws)
    except Exception:
        await disconnect_user(user_id, ws)
        try:
            await ws.close()
        except Exception:
            pass
