from sqlalchemy import create_engine, not_
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.LoaderTables import DataChunk
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
    """Get patient IDs from DataChunk table that don't match the specified list."""
    engine = create_engine(engine_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Query DataChunks for patient IDs not in the list
        non_matching_ids = (
            session.query(DataChunk.patient_id)
            .distinct()
            .filter(not_(DataChunk.patient_id.in_(patient_ids)))
            .all()
        )

        return [id_[0] for id_ in non_matching_ids]

    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        session.close()


if __name__ == "__main__":
    non_matching_ids = get_non_matching_patient_ids()
    print(
        f"Patient IDs in DataChunk that don't match the specified list: {non_matching_ids}"
    )
