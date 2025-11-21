from shared import RPCWorker, RPCHandler
from .repository import PostsRepository

worker = RPCWorker("amqp://guest:guest@rabbitmq:5672/", "posts_exchange")
repo = PostsRepository()

@RPCHandler("post.create")
async def handle_create_post(payload):
    post = await repo.create_post(payload["author_id"], payload["title"], payload["content"])
    return {"ok": True, "post": post}

@RPCHandler("post.get")
async def handle_get_posts(payload):
    posts = await repo.get_posts_by_user(payload["user_id"])
    return {"ok": True, "posts": posts}

worker.register_handlers(module=__import__(__name__))

async def main():
    await worker.start()
