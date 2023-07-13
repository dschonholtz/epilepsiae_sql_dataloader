from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


ENGINE_STR = 'postgresql+psycopg2://postgres:postgres@localhost/seizure_db'


def get_session():
    """
    Create a session to the database.
    """
    # Create an engine that stores data in the local directory's
    # on the server we could easily stuff this on /mnt/wines if we wanted to
    engine = create_engine(ENGINE_STR)
    declarative_base().metadata.create_all(engine)

    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    declarative_base().metadata.bind = engine

    # Create a configured "Session" class
    db_session = sessionmaker(bind=engine)

    # Create a Session
    session = db_session()

    return session