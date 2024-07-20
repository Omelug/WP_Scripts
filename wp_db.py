import logging
from contextlib import asynccontextmanager
from datetime import date
from sqlalchemy import Column, String, ForeignKey, Table, create_engine, select, Date, Integer, exists
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.pool import NullPool

from wp_config import CONFIG

conf = CONFIG["wp_db"]

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
                    Column('list_path', String, ForeignKey('FILE_LIST.path'), primary_key=True),
                    Column('web_link', String, ForeignKey('WEB.wp_link'), primary_key=True),
                    Column('date', Date, nullable=True, default=date.today),
                    #Column('type', String, nullable=True),
                  )

class Web(Base):
    __tablename__ = 'WEB'
    wp_link = Column(String, primary_key=True)

    #WPScan jsons
    wpscan = Column(String, nullable=True)

    #optional lists
    cracked = Column(String, nullable=True)

    file_lists = relationship('FileList',secondary=web_to_list, back_populates='webs', lazy="selectin")
    #brutal_runs = relationship('BrutalRun', back_populates='web')

class FileList(Base):
    __tablename__ = 'FILE_LIST'
    path = Column(String, primary_key=True)
    name = Column(String, nullable=True, unique=True)
    description = Column(String, nullable=True)

    #optional
    format = Column(String, nullable=True)
    list_type = Column(String, nullable=True) # pass|user|link|cewl|dork

    webs = relationship('Web',secondary=web_to_list, back_populates='file_lists', lazy="selectin")
    #brutal_runs = relationship('BrutalRun', back_populates='file_list')

class BrutalRun(Base):
    __tablename__ = 'BRUTAL_RUN'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_list = Column(String, ForeignKey('FILE_LIST.path'))
    pass_list = Column(String, ForeignKey('FILE_LIST.path'))
    wp_link = Column(String, ForeignKey('WEB.wp_link'))
    date = Column(Date, default=date.today)
    path = Column(String)

    #web = relationship('Web', back_populates='brutal_runs')
    #file_list = relationship('FileList', back_populates='brutal_runs')

class CewlList(Base):
    __tablename__ = 'CEWL'
    file_list = Column(String, ForeignKey('FILE_LIST.path'), primary_key=True)
    date = Column(Date, default=date.today)
    arguments = Column(String, nullable=True)
    web_link = Column(String, ForeignKey('WEB.wp_link'), primary_key=True)

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
            select(Web).filter(null_column == None)
        )).scalars().all()

# functions to validate
async def valid_wp_link(wp_link):
    async with get_session() as session:
        result = await session.execute(select(Web).filter(Web.wp_link == wp_link))
        web_instance = result.scalars().first()
        return bool(web_instance)


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