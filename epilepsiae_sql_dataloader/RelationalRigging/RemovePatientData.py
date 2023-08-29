"""
Heh...
I had a patient whose data I am not longer interested in.
I need to remove that patient's DataChunk data from the database.
I need to leave everything else intact
"""

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.LoaderTables import DataChunk
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure
import click
from epilepsiae_sql_dataloader.utils import ENGINE_STR


@click.command()
@click.argument("patient_ids", nargs=-1, type=int)  # Accepts multiple patient IDs
@click.option(
    "--engine-string", default=ENGINE_STR, help="Database engine connection string."
)
def remove_patient_data(patient_ids, engine_string):
    """Remove all DataChunks associated with the given patient IDs."""
    engine = create_engine(engine_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        # Query and delete DataChunks for all provided patient IDs in bulk
        session.query(DataChunk).filter(DataChunk.patient_id.in_(patient_ids)).delete(
            synchronize_session="fetch"
        )

        session.commit()
        click.echo(
            f"Successfully deleted data chunks for patient IDs {', '.join(map(str, patient_ids))}"
        )
    except Exception as e:
        click.echo(
            f"An error occurred while deleting data chunks for patient IDs {', '.join(map(str, patient_ids))}: {e}"
        )
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    remove_patient_data()
