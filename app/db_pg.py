import asyncpg
from asyncpg import Pool
from app.config import settings

db_instance = None


class PostgresDB:
    def __init__(self):
        self.pool: Pool = None
        self.dsn = settings.database_url

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args):
        connection: asyncpg.Connection
        async with self.pool.acquire() as connection:
            await connection.execute(query, *args)

    async def execute_transaction(self, queries):
        connection: asyncpg.Connection
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                for query, *args in queries:
                    await connection.execute(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record:
        connection: asyncpg.Connection
        async with self.pool.acquire() as connection:
            result = await connection.fetchrow(query, *args)
            return result

    async def fetch(self, query: str, *args) -> list[asyncpg.Record]:
        connection: asyncpg.Connection
        async with self.pool.acquire() as connection:
            result = await connection.fetch(query, *args)
            return result


async def get_db_instance() -> PostgresDB:
    global db_instance
    if db_instance is None:
        db_instance = PostgresDB()
        await db_instance.connect()
    return db_instance