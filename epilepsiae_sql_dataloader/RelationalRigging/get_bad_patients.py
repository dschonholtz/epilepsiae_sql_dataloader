from sqlalchemy import create_engine, not_, exists
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.LoaderTables import DataChunk
from epilepsiae_sql_dataloader.models.Sample import (
    Sample,
)  # I assume this is the Patients table
from epilepsiae_sql_dataloader.utils import ENGINE_STR

# List of patient strings
patient_strings = [
    "pat_81802",
    "pat_11502",
    "pat_109602",
    "pat_26402",
    "pat_56502",
    "pat_38402",
    "pat_25302",
    "pat_92202",
    "pat_27302",
    "pat_59002",
    "pat_1308903",
    "pat_63502",
]

# Extract patient IDs from the list
patient_ids = [int(pat.split("_")[1]) for pat in patient_strings]


def get_non_matching_patient_ids(engine_string=ENGINE_STR):
    """Get patient IDs from Patients table that have DataChunks and don't match the specified list."""
    engine = create_engine(engine_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    non_matching_ids = []

    try:
        # Query distinct patient IDs from the Patients table
        all_patient_ids = (
            session.query(Sample.patient_id).distinct().all()
        )  # I assume Sample represents the Patients table

        for pid in all_patient_ids:
            # Check if there's at least one corresponding row in the DataChunk table
            has_data_chunk = session.query(
                exists().where(DataChunk.patient_id == pid[0])
            ).scalar()

            if has_data_chunk and pid[0] not in patient_ids:
                non_matching_ids.append(pid[0])

        return non_matching_ids

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        session.close()


if __name__ == "__main__":
    non_matching_ids = get_non_matching_patient_ids()
    print(
        f"Patient IDs in Patients table with DataChunks that don't match the specified list: {non_matching_ids}"
    )
