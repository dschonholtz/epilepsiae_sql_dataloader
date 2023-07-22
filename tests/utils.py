import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.LoaderTables import Base


@pytest.fixture(scope="function")
def db_session():
    postgres_ip = "172.17.0.2"
    username = "postgres"
    password = "postgres"
    # test with a postgres db as we are using some db types that are specific to postgres
    # you need to have postgres running locally with a test_db configured and the user/pass set up as postgres/postgres
    engine = create_engine(
        f"postgresql://{username}:{password}@{postgres_ip}/seizure_db_test"
    )
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)  # creates the tables
    print("created all of the tables")

    Session = sessionmaker(bind=engine)
    session = Session()
    yield session  # this is where the testing happens

    # after the test function has completed, we rollback any changes to the DB and close the connection
    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)  # deletes the tables
