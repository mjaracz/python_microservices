from fastapi import WebSocket
from typing import Dict, Set
import asyncio

user_connections: Dict[str, Set[WebSocket]] = {}
rooms: Dict[str, Set[str]] = {}
lock = asyncio.Lock()

async def connect_user(user_id: str, websocket: WebSocket):
    async with lock:
        conns = user_connections.setdefault(user_id, set())
        conns.add(websocket)

async def disconnect_user(user_id: str, websocket: WebSocket):
    async with lock:
        conns = user_connections.get(user_id)
        if conns and websocket in conns:
            conns.remove(websocket)
            if not conns:
                user_connections.pop(user_id, None)

async def join_room(user_id: str, room_id: str):
    async with lock:
        members = rooms.setdefault(room_id, set())
        members.add(user_id)

async def leave_room(user_id: str, room_id: str):
    async with lock():
        members = rooms.get(room_id)
        if members and user_id in members:
            members.remove(user_id)
            if not members:
                rooms.pop(room_id, None)

async def send_to_user(user_id: str, message: dict):
    conns = user_connections.get(user_id, set())
    for ws in list(conns):
        try:
            await ws.send_json(message)
        except Exception:
            pass

async def send_to_room(room_id: str, message: dict):
    members = rooms.get(room_id, set())
    for uid in list(members):
        await send_to_user(uid, message)
