import logging
from contextlib import asynccontextmanager
from datetime import date
from sqlalchemy import Column, String, ForeignKey, Table, create_engine, select, Date, Integer, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.pool import NullPool

from wp_log import input_cyan
from wp_config import CONFIG
conf = CONFIG["wp_db"]

def create_database_if_not_exists(wp_database_name):
    try:
        # Connect to the default 'postgres' database to create new database from it
        default_engine = create_engine(conf['DATABASE_URL_ASYNC'].replace(wp_database_name, "postgres").replace("+asyncpg", ""))
        with default_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{wp_database_name}'"))
            exists = result.fetchone()
            if not exists:
                response = input_cyan(f"Database {wp_database_name} does not exist. Do you want to create it? (Y/N): ")
                if response.strip().upper() == 'Y':
                    conn.execute(text(f"CREATE DATABASE {wp_database_name}"))
                    print(f"Database {wp_database_name} created successfully.")
                    exit(0)
                else:
                    print("Database creation aborted.")
    except OperationalError as e:
        print(f"An error occurred: {e}")

create_database_if_not_exists(conf['db_name'])


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARN)


engine = create_async_engine(
        conf['DATABASE_URL_ASYNC'],
        echo=False,
        poolclass=NullPool
)

SessionLocal = async_sessionmaker(
    class_=AsyncSession,
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@asynccontextmanager
async def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        await session.close()

Base = declarative_base()
web_to_list = Table('web_to_list', Base.metadata,
                    Column('list_path', String, ForeignKey('file_list.path'), primary_key=True),
                    Column('web_link', String, ForeignKey('web.wp_link'), primary_key=True),
                    Column('date', Date, nullable=True, default=date.today)
                  )

class Web(Base):
    __tablename__ = 'web'
    wp_link = Column(String, primary_key=True)

    wpscan = Column(String, nullable=True) #WPScan jsons
    cracked = Column(String, nullable=True)
    file_lists = relationship('FileList',secondary=web_to_list, back_populates='webs', lazy="selectin")

# file_list is definned by path
class FileList(Base):
    __tablename__ = 'file_list'
    path = Column(String, primary_key=True)
    name = Column(String, nullable=True, unique=True)
    description = Column(String, nullable=True)

    format = Column(String, nullable=True)
    list_type = Column(String, nullable=True) # pass|user|link|cewl|dork

    webs = relationship('Web',secondary=web_to_list, back_populates='file_lists', lazy="selectin")

class BrutalRun(Base):
    __tablename__ = 'brutal_run'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_list = Column(String, ForeignKey('file_list.path'))
    pass_list = Column(String, ForeignKey('file_list.path'))
    wp_link = Column(String, ForeignKey('web.wp_link'))
    date = Column(Date, default=date.today)
    path = Column(String)

class CewlList(Base):
    __tablename__ = 'cewl_run'
    file_list = Column(String, ForeignKey('file_list.path'), primary_key=True)
    date = Column(Date, default=date.today)
    arguments = Column(String, nullable=True)
    web_link = Column(String, ForeignKey('web.wp_link'), primary_key=True)

async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Create a synchronous engine
sync_engine = create_engine(conf['DATABASE_URL_ASYNC'].replace("+asyncpg", ""))
Base.metadata.create_all(sync_engine)

#select funtions
async def getWeb_whereNull(null_column):
    async with get_session() as session:
        return (await session.execute(
            select(Web).filter(null_column is None)
        )).scalars().all()

# functions to validate
async def valid_wp_link(wp_link):
    async with get_session() as session:
        result = await session.execute(select(Web).filter(Web.wp_link == wp_link))
        web_instance = result.scalars().first()
        return bool(web_instance)

#create file list if not exists
async def get_or_create_list(session, list_type, file_list_path):
    file_list = (await session.execute(
        select(FileList).filter_by(path=file_list_path, list_type=list_type)
    )).scalars().first()

    if not file_list:
        file_list = FileList(
            path=file_list_path,
            list_type=list_type
        )
        session.add(file_list)
        await session.commit()
    return file_list

async def get_webs():
    async with get_session() as session:
        result = await session.execute(select(Web))
        return result.scalars().all()