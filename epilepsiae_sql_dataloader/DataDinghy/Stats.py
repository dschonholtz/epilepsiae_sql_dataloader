import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure
from epilepsiae_sql_dataloader.models.LoaderTables import Dataset, Patient, DataChunk
from epilepsiae_sql_dataloader.utils import ENGINE_STR


from sqlalchemy import func


def get_data_summary(session):
    summary = []
    print("about to query datasets")
    # Query all datasets
    datasets = session.query(Dataset).all()
    print("queried datasets")

    for dataset in datasets:
        print(f"In dataset: {dataset.name}")
        print(f"Patients are: {dataset.patients}")
        dataset_summary = {"name": dataset.name, "patients": []}

        for patient in dataset.patients:
            patient_summary = {"id": patient.id, "data_chunks": {}}
            print(f"about to query data chunks for patient {patient.id}")

            # Query data chunk counts by data_type and seizure_state
            data_chunk_counts = (
                session.query(
                    DataChunk.data_type,
                    DataChunk.seizure_state,
                    func.count(DataChunk.id).label("count"),
                )
                .filter(DataChunk.patient_id == patient.id)
                .group_by(DataChunk.data_type, DataChunk.seizure_state)
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
                patient_summary["seizures"].append(
                    {"onset": seizure.onset, "offset": seizure.offset}
                )
                print(f"  seizure: {seizure.onset}, {seizure.offset}")

            dataset_summary["patients"].append(patient_summary)

        summary.append(dataset_summary)

    return summary


def print_summary(summary):
    for dataset in summary:
        print(f"Dataset Name: {dataset['name']}")
        for patient in dataset["patients"]:
            print(f"  Patient ID: {patient['id']}")
            for (data_type, seizure_state), count in patient["data_chunks"].items():
                print(
                    f"    Data Type: {data_type}, Seizure State: {seizure_state}, Count: {count}"
                )
            print("  Seizures:")
            for seizure in patient["seizures"]:
                print(f"    Onset: {seizure['onset']}, Offset: {seizure['offset']}")


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
        summary = get_data_summary(session)
        print_summary(summary)
    finally:
        session.close()


if __name__ == "__main__":
    main()