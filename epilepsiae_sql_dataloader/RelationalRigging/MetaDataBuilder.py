"""
Uses the SQL Alchemy models in models/ to load everything you could possibly want to the database
"""

import glob
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import csv
from pathlib import Path
from datetime import datetime
import pandas as pd
from pandas import DataFrame
from pandas import to_datetime

from epilepsiae_sql_dataloader.utils import ENGINE_STR, session_scope
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.LoaderTables import Patient, Dataset
from epilepsiae_sql_dataloader.models.Seizures import Seizure
from epilepsiae_sql_dataloader.models.Base import Base

import sys
import click


class MetaDataBuilder(object):
    def __init__(self, engine_str):
        self.engine_str = engine_str

    def get_samples(self):
        """
        Get all samples from the database.
        """
        with session_scope(self.engine_str) as session:
            samples = session.query(Sample).all()
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
        with session_scope(self.engine_str) as session:
            # Query for the patient passed to the method with the session
            patient = session.query(Patient).filter(Patient.id == patient_id).first()
            for row in data:
                onset = row[0]
                offset = row[1]
                onset_sample = row[2]
                offset_sample = row[3]
                seizure = Seizure(
                    onset=onset,
                    offset=offset,
                    onset_sample=int(onset_sample),
                    offset_sample=int(offset_sample),
                )
                patient.seizures.append(seizure)
                print(f"Patient has this many seizures: {len(patient.seizures)}")

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
        # Define the expected mandatory fields
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
                    value = [",".join(value[1:-1].split(","))]
                elif key == "start_ts":
                    try:
                        value = to_datetime(value)
                    except ValueError:
                        if key in mandatory_fields:
                            return DataFrame()  # Bad format for a mandatory field
                elif key == "pat_id":
                    continue
                elif key in mandatory_fields:
                    try:
                        value = int(value)
                    except ValueError:
                        return DataFrame()  # Bad format for a mandatory field
                elif key == "conversion_factor":
                    try:
                        value = float(value)
                    except ValueError:
                        # Bad format for conversion_factor, but it's not mandatory
                        data[key] = None
                elif key == "sample_bytes":
                    try:
                        value = int(value)
                    except ValueError:
                        # Bad format for sample_bytes, but it's not mandatory
                        data[key] = None
                else:
                    # Non-mandatory field with an unexpected type
                    data[key] = None
                data[key] = value

        # Check if all mandatory fields are present
        if not mandatory_fields.issubset(data.keys()):
            return (
                DataFrame()
            )  # Return an empty DataFrame if any mandatory field is missing

        return DataFrame(data)

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
        with session_scope(self.engine_str) as session:
            # Query for the patient passed to the method with the session
            patient = session.query(Patient).filter(Patient.id == patient_id).first()

            for head_file in self.file_generator(directory):
                # try:
                data = self.read_sample_data(head_file).to_dict("records")[0]
                # print(data)
                data["data_file"] = str(head_file.with_suffix(".data"))
                sample = Sample(**data)
                patient.samples.append(sample)
                # except Exception as e:
                #     print(f"Error processing file {head_file}: {e}")

    def create_patient(self, pat_id: int, dataset_id: int):
        with session_scope(self.engine_str) as session:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            print(f"Dataset query with id: {dataset.id} returned: {dataset}")
            patient = Patient(id=pat_id)
            session.add(patient)
            dataset.patients.append(patient)
            session.commit()

    def load_data_in_pat_dir(self, directory, dataset_id: int):
        print(directory)
        directory_path = Path(directory)
        pat_id = directory.split("/")[-1]
        data = self.read_seizure_data(directory_path / "seizure_list")
        patient_id_int = int(pat_id.split("_")[1])
        self.create_patient(patient_id_int, dataset_id)
        # print("Found seizure data: ", data)
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
        with session_scope(self.engine_str) as session:
            dataset = Dataset(name=name)
            session.add(dataset)
            session.commit()
            dataset_id = dataset.id

        return dataset_id

    def start(self, directories):
        paths = []
        for directory in directories:
            # If the dir ends in inv create the inv dataset if it doesn't already exist
            # if the dir ends in surf30 create the surf dataset if it doesn't already exist
            directory = str(directory)
            print("directory: ", directory)
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
    "--directories",
    multiple=True,
    default=["/mnt/wines/intra/original_data/inv"],
    help="Directories to hunt for.",
)
@click.option("--engine-str", default=ENGINE_STR, help="Engine string for postgreSQL.")
@click.option("--drop-tables", is_flag=True, help="Drop all previous tables.")
def main(directories, engine_str, drop_tables):
    """Console script for epilepsiae_sql_dataloader."""
    if len(directories) > 1:
        raise ValueError("Only one directory is supported at this time.")
    if drop_tables:
        engine = create_engine(engine_str)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    loader = MetaDataBuilder(engine_str)
    loader.start(directories)

    return 0


if __name__ == "__main__":
    sys.exit(main())
