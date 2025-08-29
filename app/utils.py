import random
import string
import hashlib
from typing import Optional
# from app.models import DynamicLink
from app.db_pg import PostgresDB


def generate_short_code(length: int = 7) -> str:
    """Generate a random short code for the dynamic link."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


async def generate_unique_short_code(db: PostgresDB, length: int = 7, max_attempts: int = 100) -> str:
    """Generate a unique short code that doesn't exist in the database."""
    for _ in range(max_attempts):
        short_code = generate_short_code(length)
        query = "SELECT 1 FROM dynamic_links WHERE short_code = $1;"
        if not await db.fetchrow(query, short_code):
            return short_code
    raise Exception("Could not generate a unique short code.")


async def generate_custom_short_code(custom_code: str, db: PostgresDB) -> str:
    """Validate and return a custom short code if it's not taken."""
    # Basic validation (e.g., length, characters)
    if not (3 <= len(custom_code) <= 10) or not custom_code.isalnum():
        return None
    
    query = "SELECT 1 FROM dynamic_links WHERE short_code = $1;"
    if await db.fetchrow(query, custom_code):
        return None  # Already taken
        
    return custom_code


def hash_ip_address(ip_address: str, salt: str = "dynalinks_salt") -> str:
    """Hash IP address for privacy compliance."""
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
