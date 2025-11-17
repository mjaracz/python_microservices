from shared.messagebus import MessagePattern, start_worker_sync
from shared.database.mongo import MongoConnection
from .repository import PostsRepository

mongo = MongoConnection("mongodb://mongo_posts:27017", "posts_db")
repo = PostsRepository(mongo.get_db())

@MessagePattern("post.create")
async def handle_create(payload):
    post = {
        "title": payload.get("title"),
        "content": payload.get("content"),
        "author_id": payload.get("author_id"),
    }
    saved = await repo.create_post(post)
    return {"ok": True, "post": saved}

@MessagePattern("post.get")
async def handle_get(payload):
    posts = await repo.get_posts_by_user(payload.get("user_id"))
    return {"ok": True, "posts": posts}

if __name__ == "__main__":
    start_worker_sync()
