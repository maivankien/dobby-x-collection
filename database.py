import logging
import aiosqlite
import asyncio
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = "data/dobby_bot.db"
logger = logging.getLogger(__name__)

_db_connection = None
_connection_lock = asyncio.Lock()


async def init_connection():
    global _db_connection
    async with _connection_lock:
        if _db_connection is None:
            _db_connection = await aiosqlite.connect(DATABASE_PATH)
            logger.info("Database connection initialized")
    return _db_connection


async def get_db_connection():
    if _db_connection is None:
        await init_connection()
    return _db_connection


async def init_database():
    db = await get_db_connection()
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            display_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            server_id INTEGER PRIMARY KEY,
            server_name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id INTEGER PRIMARY KEY,
            channel_name TEXT NOT NULL,
            server_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (server_id) REFERENCES servers (server_id),
            UNIQUE(channel_name, server_id)
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS x_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            link_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            FOREIGN KEY (channel_id) REFERENCES channels (channel_id),
            UNIQUE(user_id, link_url)
        )
    ''')

    await db.commit()
    logger.info("Database initialized successfully")


async def save_user(user_id: int, username: str, display_name: str):
    db = await get_db_connection()
    await db.execute('''
        INSERT OR REPLACE INTO users (user_id, username, display_name, last_seen)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, username, display_name))
    await db.commit()


async def save_server(server_id: int, server_name: str):
    db = await get_db_connection()
    await db.execute('''
        INSERT OR REPLACE INTO servers (server_id, server_name)
        VALUES (?, ?)
    ''', (server_id, server_name))
    await db.commit()


async def save_channel(channel_id: int, channel_name: str, server_id: int):
    db = await get_db_connection()
    await db.execute('''
        INSERT OR REPLACE INTO channels (channel_id, channel_name, server_id)
        VALUES (?, ?, ?)
    ''', (channel_id, channel_name, server_id))
    await db.commit()


async def get_or_create_channel_id(channel_name: str, server_id: int):
    db = await get_db_connection()
    cursor = await db.execute('''
        SELECT channel_id FROM channels 
        WHERE channel_name = ? AND server_id = ?
    ''', (channel_name, server_id))

    result = await cursor.fetchone()
    if result:
        return result[0]

    await db.execute('''
        INSERT INTO channels (channel_name, server_id)
        VALUES (?, ?)
    ''', (channel_name, server_id))

    cursor = await db.execute('''
        SELECT channel_id FROM channels 
        WHERE channel_name = ? AND server_id = ?
    ''', (channel_name, server_id))

    result = await cursor.fetchone()
    await db.commit()
    return result[0] if result else None


async def save_x_link(user_id: int, channel_id: int, link_url: str):
    db = await get_db_connection()
    await db.execute('''
        INSERT OR IGNORE INTO x_links (user_id, channel_id, link_url)
        VALUES (?, ?, ?)
    ''', (user_id, channel_id, link_url))
    await db.commit()


async def get_total_links_count():
    db = await get_db_connection()
    cursor = await db.execute('SELECT COUNT(*) FROM x_links')
    count = (await cursor.fetchone())[0]
    return count


async def get_user_links(user_id: int):
    db = await get_db_connection()
    cursor = await db.execute('''
        SELECT xl.link_url, c.channel_name, s.server_name, xl.created_at
        FROM x_links xl
        JOIN channels c ON xl.channel_id = c.channel_id
        JOIN servers s ON c.server_id = s.server_id
        WHERE xl.user_id = ?
        ORDER BY xl.created_at DESC
    ''', (user_id,))

    results = await cursor.fetchall()
    return [
        {
            'link_url': row[0],
            'channel_name': row[1],
            'server_name': row[2],
            'created_at': row[3]
        }
        for row in results
    ]


async def get_latest_links(limit: int = 5):
    db = await get_db_connection()
    cursor = await db.execute('''
        SELECT xl.link_url, u.display_name, c.channel_name, s.server_name, xl.created_at
        FROM x_links xl
        JOIN users u ON xl.user_id = u.user_id
        JOIN channels c ON xl.channel_id = c.channel_id
        JOIN servers s ON c.server_id = s.server_id
        ORDER BY xl.created_at DESC
        LIMIT ?
    ''', (limit,))

    results = await cursor.fetchall()
    return [
        {
            'link_url': row[0],
            'display_name': row[1],
            'channel_name': row[2],
            'server_name': row[3],
            'created_at': row[4]
        }
        for row in results
    ]


async def get_all_links_for_export():
    db = await get_db_connection()
    cursor = await db.execute('''
        SELECT xl.link_url, u.display_name, u.username, c.channel_name, s.server_name, xl.created_at
        FROM x_links xl
        JOIN users u ON xl.user_id = u.user_id
        JOIN channels c ON xl.channel_id = c.channel_id
        JOIN servers s ON c.server_id = s.server_id
        ORDER BY xl.created_at DESC
    ''')

    results = await cursor.fetchall()
    return [
        {
            'link_url': row[0],
            'display_name': row[1],
            'username': row[2],
            'channel_name': row[3],
            'server_name': row[4],
            'created_at': row[5]
        }
        for row in results
    ]
