"""
Uses the SQL Alchemy models in models/ to load everything you could possibly want to the database
"""

import glob
from sqlalchemy import create_engine
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd
from pandas import DataFrame, to_datetime

from epilepsiae_sql_dataloader.utils import ENGINE_STR
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.LoaderTables import Patient, Dataset
from epilepsiae_sql_dataloader.models.Seizures import Seizure

import sys
import click


class MetaDataBuilder(object):
    def __init__(self, engine_str):
        self.engine = create_engine(engine_str)

    def get_samples(self):
        """
        Get all samples from the database.
        """
        with self.engine.connect() as connection:
            result = connection.execute("SELECT * FROM samples")
            samples = result.fetchall()
            return samples

    def read_seizure_data(self, fp: str):
        # Lists to store the data
        onset_list = []
        offset_list = []
        onset_sample_list = []
        offset_sample_list = []

        # Open the file and read line by line
        with open(fp, "r") as file:
            for line in file:
                line = line.strip()  # Remove leading/trailing whitespace
                if line.startswith("#") or line == "":
                    continue

                # Split the line by tabs
                try:
                    (
                        onset0,
                        onset1,
                        offset0,
                        offset1,
                        onset_sample,
                        offset_sample,
                    ) = line.split(" ")
                except ValueError:
                    print(f"Error parsing line: {line}")
                    continue
                # Convert to appropriate types
                onset = onset0 + " " + onset1
                offset = offset0 + " " + offset1
                onset = datetime.strptime(
                    onset + (".000000" if "." not in onset else ""),
                    "%Y-%m-%d %H:%M:%S.%f",
                )
                offset = datetime.strptime(
                    offset + (".000000" if "." not in offset else ""),
                    "%Y-%m-%d %H:%M:%S.%f",
                )
                onset_sample = int(onset_sample)
                offset_sample = int(offset_sample)

                # Append to lists
                onset_list.append(onset)
                offset_list.append(offset)
                onset_sample_list.append(onset_sample)
                offset_sample_list.append(offset_sample)

        # Create a DataFrame from the lists
        data = pd.DataFrame(
            {
                "onset": onset_list,
                "offset": offset_list,
                "onset_sample": onset_sample_list,
                "offset_sample": offset_sample_list,
            }
        )

        # print(data)

        # Convert the DataFrame to a numpy array and return
        return data.values

    def load_seizure_data_to_db(self, data, patient_id: int):
        """
        Load the seizure data into the database.
        Data has been cast to a numpy array [datetime, datetime, int, int]
        """
        with self.engine.connect() as connection:
            for row in data:
                onset, offset, onset_sample, offset_sample = row
                connection.execute(
                    "INSERT INTO seizures (pat_id, onset, offset, onset_sample, offset_sample) VALUES (%s, %s, %s, %s, %s)",
                    (patient_id, onset, offset, onset_sample, offset_sample),
                )

    def read_sample_data(self, fp: Path):
        """
        Format of file:
        start_ts=2008-11-03 20:34:03.000
        num_samples=3686400
        sample_freq=1024
        conversion_factor=0.179000
        num_channels=93
        elec_names=[GA1,GA2,GA3,GA4,GA5,GA6,GA7,GA8,GB1,GB2,GB3,GB4,GB5,GB6,GB7,GB8,GC1,GC2,GC3,GC4,GC5,GC6,GC7,GC8,GD1,GD2,GD3,GD4,GD5,GD6,GD7,GD8,GE1,GE2,GE3,GE4,GE5,GE6,GE7,GE8,GF1,GF2,GF3,GF4,GF5,GF6,GF7,GF8,GG1,GG2,GG3,GG4,GG5,GG6,GG7,GG8,GH1,GH2,GH3,GH4,GH5,GH6,GH7,GH8,M1,M2,M3,M4,M5,M6,M7,M8,IHA1,IHA2,IHA3,IHA4,IHB1,IHB2,IHB3,IHB4,IHC1,IHC2,IHC3,IHC4,IHD1,IHD2,IHD3,IHD4,FL1,FL2,FL3,FL4,ECG]
        pat_id=108402
        adm_id=1084102
        rec_id=108400102
        duration_in_sec=3600
        sample_bytes=2

            id = Column(Integer, primary_key=True)
        start_ts = Column(DateTime, nullable=False)
        num_samples = Column(Integer, nullable=False)
        sample_freq = Column(Integer, nullable=False)
        conversion_factor = Column(Float, nullable=False)
        num_channels = Column(Integer, nullable=False)
        elec_names = Column(String, nullable=False)
        pat_id = Column(Integer, nullable=False)
        adm_id = Column(Integer, nullable=False)
        rec_id = Column(Integer, nullable=False)
        duration_in_sec = Column(Integer, nullable=False)
        sample_bytes = Column(Integer, nullable=False)
        seizure_id = Column(Integer, ForeignKey('seizures.id'))

        We need to make sure that everything is the right type

        :param fp: a file path to the sample data
        :return: A DataFrame that will be easily loaded to pandas later
        """
        mandatory_fields = {
            "start_ts",
            "num_samples",
            "sample_freq",
            "num_channels",
            "adm_id",
            "rec_id",
            "duration_in_sec",
        }
        data = {}
        with fp.open("r") as f:
            reader = csv.reader(f, delimiter="=")
            for line in reader:
                key, value = line
                if key.startswith("#"):
                    continue
                if key == "elec_names":
                    value = value.strip("[]").split(",")
                elif key == "start_ts":
                    value = pd.to_datetime(value)
                elif key in {
                    "num_samples",
                    "sample_freq",
                    "num_channels",
                    "adm_id",
                    "rec_id",
                    "duration_in_sec",
                    "sample_bytes",
                }:
                    value = int(value)
                elif key == "conversion_factor":
                    value = float(value)
                data[key] = value
        if not mandatory_fields.issubset(data.keys()):
            return pd.DataFrame()
        return pd.DataFrame([data])

    def file_generator(self, directory):
        adm_dirs = directory.glob("adm_*")
        for adm_dir in adm_dirs:
            rec_dirs = adm_dir.glob("rec_*")
            for rec_dir in rec_dirs:
                head_files = rec_dir.glob("*.head")
                for head_file in head_files:
                    yield head_file

    def load_sample_dir_to_db(self, directory: Path, patient_id: int):
        """
        Load the sample data into the database.
        """
        with self.engine.connect() as connection:
            for head_file in self.file_generator(directory):
                data = self.read_sample_data(head_file).to_dict("records")[0]
                data["data_file"] = str(head_file.with_suffix(".data"))
                connection.execute(
                    "INSERT INTO samples (start_ts, num_samples, sample_freq, conversion_factor, num_channels, elec_names, pat_id, adm_id, rec_id, duration_in_sec, sample_bytes, data_file) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        data["start_ts"],
                        data["num_samples"],
                        data["sample_freq"],
                        data["conversion_factor"],
                        data["num_channels"],
                        data["elec_names"],
                        patient_id,
                        data["adm_id"],
                        data["rec_id"],
                        data["duration_in_sec"],
                        data["sample_bytes"],
                        data["data_file"],
                    ),
                )

    def create_patient(self, pat_id: int, dataset_id: int):
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(
                    "INSERT INTO patients (id, dataset_id) VALUES (%s, %s)",
                    (pat_id, dataset_id),
                )
                transaction.commit()
            except:
                transaction.rollback()
                raise

    def load_data_in_pat_dir(self, directory, dataset_id: int):
        print(directory)
        directory_path = Path(directory)
        pat_id = directory.split("/")[-1]
        data = self.read_seizure_data(directory_path / "seizure_list")
        patient_id_int = int(pat_id.split("_")[1])
        self.create_patient(patient_id_int, dataset_id)
        self.load_seizure_data_to_db(data, patient_id_int)
        self.load_sample_dir_to_db(directory_path, patient_id_int)

    def load_data(self, paths, dataset_id: int):
        """
        Each has a pat dir of the format pat_#####
        In each pat we have a seizurelist
        :return:
        """
        for path in paths:
            for directory in glob.glob(path):
                self.load_data_in_pat_dir(directory, dataset_id)

    def create_dataset(self, name) -> int:
        """
        Creates a dataset with the given name and returns the id
        """
        with self.engine.connect() as connection:
            result = connection.execute(
                "INSERT INTO datasets (name) VALUES (%s) RETURNING id", (name,)
            )
            dataset_id = result.fetchone()[0]
        return dataset_id

    def start(self, directories):
        paths = []
        for directory in directories:
            directory = str(directory)
            if directory.endswith("inv"):
                dataset_id = self.create_dataset("inv")
            elif directory.endswith("surf30"):
                dataset_id = self.create_dataset("surf")
            else:
                raise ValueError("Unknown dataset")
            paths.extend(
                [
                    f"{directory}/pat_*",
                ]
            )
        self.load_data(paths, dataset_id)


@click.command()
@click.option(
    "--directory",
    help="Directory to load patient data from.",
)
@click.option("--engine-str", default=ENGINE_STR, help="Engine string for postgreSQL.")
@click.option("--drop-tables", is_flag=True, help="Drop all previous tables.")
@click.option("--patient-id", type=int, help="Patient ID to add seizure data to.")
@click.option(
    "--seizure-file",
    type=str,
    help="Path to the seizure file for a specific patient.",
)
def main(directory, engine_str, drop_tables, patient_id, seizure_file):
    """Console script for epilepsiae_sql_dataloader."""

    # Check if the user wants to add seizure data to a specific patient
    if patient_id is not None or seizure_file is not None:
        if patient_id is None or seizure_file is None:
            raise ValueError(
                "Both --patient-id and --seizure-file must be provided together."
            )
        if directory is not None or drop_tables:
            raise ValueError(
                "When adding seizure data to a specific patient, only --patient-id and --seizure-file should be provided."
            )
        loader = MetaDataBuilder(engine_str)
        data = loader.read_seizure_data(seizure_file)
        loader.load_seizure_data_to_db(data, patient_id)
        return 0

    # Check if the user wants to drop tables
    if drop_tables:
        confirmation = click.confirm(
            "Are you sure you want to drop all tables? This action is irreversible."
        )
        if confirmation:
            engine = create_engine(engine_str)
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
        else:
            click.echo("Operation canceled.")
            return 0

    loader = MetaDataBuilder(engine_str)
    loader.start(directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())
