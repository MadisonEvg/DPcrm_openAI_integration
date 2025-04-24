import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base
import logging

logging.basicConfig()

load_dotenv()

DB_URL = (
    f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_async_engine(DB_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()