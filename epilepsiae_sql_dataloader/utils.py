from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


ENGINE_STR = "postgresql+psycopg2://postgres:postgres@localhost/seizure_db"


def get_session(engine_str=ENGINE_STR):
    """
    Create a session to the database.
    """
    # Create an engine that stores data in the local directory's
    # on the server we could easily stuff this on /mnt/wines if we wanted to
    engine = create_engine(engine_str)
    declarative_base().metadata.create_all(engine)

    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL.
    declarative_base().metadata.bind = engine

    # Create a configured "Session" class
    db_session = sessionmaker(bind=engine)

    # Create a Session
    session = db_session()

    return session


from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker


ENGINE_STR = "postgresql+psycopg2://postgres:postgres@localhost/seizure_db_test"


@contextmanager
def session_scope(engine_str):
    """Provide a transactional scope around a series of operations."""
    engine = create_engine(engine_str)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
