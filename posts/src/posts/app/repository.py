from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

class PostsRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_post(self, post: dict) -> dict:
        result = await self.db.posts.insert_one(post)
        saved = await self.db.posts.find_one({"_id": result.inserted_id})
        return saved

    async def get_posts_by_user(self, user_id: str) -> List[dict]:
        return await self.db.posts.find({"author_id": user_id}).to_list(length=None)
