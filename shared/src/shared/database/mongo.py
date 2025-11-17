from motor.motor_asyncio import AsyncIOMotorClient

class MongoConnection:
    def __init__(self, url: str, db_name: str, pool_size: int = 20):
        self.client = AsyncIOMotorClient(url, maxPoolSize=pool_size)
        self.db = self.client[db_name]

    def get_db(self):
        return self.db

    def close(self):
        self.client.close()
