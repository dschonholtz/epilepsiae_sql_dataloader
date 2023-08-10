"""
Heh...
I had a patient whose data I am not longer interested in.
I need to remove that patient's DataChunk data from the database.
I need to leave everything else intact
"""


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.LoaderTables import DataChunk
import click
from epilepsiae_sql_dataloader.utils import ENGINE_STR


@click.command()
@click.argument("patient_id", type=int)
@click.option(
    "--engine-string", default=ENGINE_STR, help="Database engine connection string."
)
def remove_patient_data(patient_id, engine_string):
    """Remove all DataChunks associated with the given patient ID."""
    engine = create_engine(engine_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        # Query all DataChunks with the given patient ID
        data_chunks = (
            session.query(DataChunk).filter(DataChunk.patient_id == patient_id).all()
        )

        # Delete each DataChunk
        for chunk in data_chunks:
            session.delete(chunk)

        session.commit()
        click.echo(f"Successfully deleted data chunks for patient ID {patient_id}")
    except Exception as e:
        click.echo(
            f"An error occurred while deleting data chunks for patient ID {patient_id}: {e}"
        )
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    remove_patient_data()
