import psycopg2
import pytest
from sqlalchemy.schema import CreateTable, DropTable
from epilepsiae_sql_dataloader.models.LoaderTables import (
    metadata,
    datasets,
    patients,
    data_chunks,
)

ENGINE_STR = "postgresql+psycopg2://postgres:postgres@localhost/seizure_db_test"


@pytest.fixture(scope="function")
def db_session():
    postgres_ip = "172.17.0.2"
    username = "postgres"
    password = "postgres"
    dbname = "seizure_db_test"

    conn = psycopg2.connect(
        dbname=dbname, user=username, password=password, host=postgres_ip
    )
    cursor = conn.cursor()

    # Drop existing tables
    for table in reversed(metadata.sorted_tables):
        cursor.execute(DropTable(table))

    # Create tables
    for table in metadata.sorted_tables:
        cursor.execute(CreateTable(table))

    conn.commit()
    print("Created all of the tables")

    yield cursor  # this is where the testing happens

    # After the test function has completed, rollback any changes to the DB and close the connection
    conn.rollback()
    cursor.close()
    conn.close()
