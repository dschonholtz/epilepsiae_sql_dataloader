import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.LoaderTables import Dataset, Patient, DataChunk
from epilepsiae_sql_dataloader.utils import ENGINE_STR


def get_data_summary(session):
    # Query all datasets
    datasets = session.query(Dataset).all()
    summary = []

    for dataset in datasets:
        dataset_summary = {"name": dataset.name, "patients": []}
        for patient in dataset.patients:
            patient_summary = {
                "id": patient.id,
                "name": patient.name,
                "data_chunks": {},
            }

            # Grouping data chunks by data_type and seizure_state
            for chunk in patient.chunks:
                key = (chunk.data_type, chunk.seizure_state)
                patient_summary["data_chunks"][key] = (
                    patient_summary["data_chunks"].get(key, 0) + 1
                )

            dataset_summary["patients"].append(patient_summary)
        summary.append(dataset_summary)

    return summary


def print_summary(summary):
    for dataset in summary:
        print(f"Dataset Name: {dataset['name']}")
        for patient in dataset["patients"]:
            print(f"  Patient ID: {patient['id']}")
            print(f"  Name: {patient['name']}")
            for (data_type, seizure_state), count in patient["data_chunks"].items():
                print(
                    f"    Data Type: {data_type}, Seizure State: {seizure_state}, Count: {count}"
                )


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
