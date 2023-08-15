import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure
from epilepsiae_sql_dataloader.models.LoaderTables import (
    Dataset,
    Patient,
    DataChunk,
    DataChunkSummary,
)
from epilepsiae_sql_dataloader.utils import ENGINE_STR


from sqlalchemy import func


def get_data_summary(session):
    print("about to query datasets")
    # Query all datasets
    datasets = session.query(Dataset).all()
    print("queried datasets")

    for dataset in datasets:
        print(f"In dataset: {dataset.name}")
        print(f"Patients are: {dataset.patients}")

        for patient in dataset.patients:
            patient_summary = {"id": patient.id, "data_chunks": {}}
            print(f"about to query data chunks for patient {patient.id}")

            # Query data chunk counts by data_type and seizure_state
            data_chunk_counts = (
                session.query(
                    DataChunkSummary.data_type,
                    DataChunkSummary.seizure_state,
                    func.count(DataChunkSummary.id).label("count"),
                )
                .filter(DataChunkSummary.patient_id == patient.id)
                .group_by(DataChunkSummary.data_type, DataChunkSummary.seizure_state)
                .all()
            )
            print(f"queried data chunks for patient {patient.id}")
            print(f"patient {patient.id} has {len(data_chunk_counts)} data chunks")

            for data_type, seizure_state, count in data_chunk_counts:
                patient_summary["data_chunks"][(data_type, seizure_state)] = count
                print(
                    f"  data_type: {data_type}, seizure_state: {seizure_state}, count: {count}"
                )

            print(f"about to query seizures for patient {patient.id}")
            print(f"Seizures are: {patient.seizures}")
            for seizure in patient.seizures:
                print(f"  seizure: {seizure.onset}, {seizure.offset}")


@click.command()
@click.option(
    "--connection-string",
    prompt="Database connection string",
    help="Connection string for the database.",
    default=ENGINE_STR,
)
def main(connection_string):
    """Script to print the summary of data chunks for each data_type and seizure_state for each patient, grouped by datasets."""
    engine = create_engine(connection_string)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        get_data_summary(session)
    finally:
        session.close()


if __name__ == "__main__":
    main()
