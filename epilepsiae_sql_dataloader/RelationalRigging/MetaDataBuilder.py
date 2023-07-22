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

    def read_seizure_data(self, fp: Path):
        """
        Read in the data from the seizurefile
        # colums are tab-separated:
        # onset	offset	onset_sample	offset_sample
        2008-11-11 06:10:03.416992	2008-11-11 06:10:08.325195	1526187	1531213

        2008-11-11 06:35:33.729492	2008-11-11 06:35:39.258789	3093227	3098889

        2008-11-11 07:25:57.974609	2008-11-11 07:26:03.691406	2466790	2472644

        2008-11-11 07:54:56.308594	2008-11-11 07:55:01.308594	558396	563516
        """

        def str_to_datetime(x):
            try:
                if "." not in x:
                    x += ".000000"
                return datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                return np.nan

        # Function to convert string to int
        def str_to_int(x):
            try:
                return int(x)
            except ValueError:
                return np.nan

        # Define converters
        converters = {
            0: str_to_datetime,
            1: str_to_datetime,
            2: str_to_int,
            3: str_to_int,
        }

        # Read the file using pandas, which can handle comments and ignore blank lines
        data = pd.read_csv(
            fp,
            delimiter="\t",
            comment="#",
            skip_blank_lines=True,
            header=None,
            converters=converters,
        )
        data = data.dropna()

        # Convert the DataFrame to a numpy array and return
        return data.values

    def load_seizure_data_to_db(self, data, patient: Patient):
        """
        Load the seizure data into the database.
        Data has been cast to a numpy array [datetime, datetime, int, int]
        """
        with session_scope(self.engine_str) as session:
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
            "pat_id",
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
                        value = [to_datetime(value)]
                    except ValueError:
                        if key in mandatory_fields:
                            return DataFrame()  # Bad format for a mandatory field
                elif key in mandatory_fields:
                    try:
                        value = [int(value)]
                    except ValueError:
                        return DataFrame()  # Bad format for a mandatory field
                elif key == "conversion_factor":
                    try:
                        value = [float(value)]
                    except ValueError:
                        # Bad format for conversion_factor, but it's not mandatory
                        data[key] = None
                elif key == "sample_bytes":
                    try:
                        value = [int(value)]
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
                try:
                    data = self.read_sample_data(head_file)
                    print(data)
                    data["data_file"] = str(head_file.with_suffix(".data"))
                    sample = Sample(**data)
                    patient.samples.append(sample)
                except Exception as e:
                    print(f"Error processing file {head_file}: {e}")

    def create_patient(self, pat_id: int, dataset_id: int):
        with session_scope(self.engine_str) as session:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            print(f"Dataset query with id: {dataset.id} returned: {dataset}")
            patient = Patient(id=pat_id)
            session.add(patient)
            patient_id = patient.id
            dataset.patients.append(patient)
        return patient_id

    def load_data_in_pat_dir(self, directory, dataset_id: int):
        print(directory)
        directory_path = Path(directory)
        pat_id = directory.split("/")[-1]
        data = self.read_seizure_data(directory_path / "seizure_list")
        patient_id = self.create_patient(pat_id.split("_")[1], dataset_id)
        self.load_seizure_data_to_db(data, pat_id.split("_")[1], patient_id)
        self.load_sample_dir_to_db(directory_path, patient_id)

    def load_data(self, paths, dataset_id: int):
        """
        Each has a pat dir of the format pat_#####
        In each pat we have a seizurelist
        :return:
        """
        for path in paths:
            for directory in glob.glob(path):
                self.load_data_in_pat_dir(directory, dataset_id)


def create_dataset(name, engine_str) -> int:
    """
    Creates a dataset with the given name and returns the id
    """
    with session_scope(engine_str) as session:
        dataset = Dataset(name=name)
        session.add(dataset)
        dataset_id = dataset.id
        print(f"Created dataset {name} with id {dataset_id}")

    return dataset_id


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
    if drop_tables:
        engine = create_engine(engine_str)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)

    loader = MetaDataBuilder(engine_str)
    paths = []
    for dir in directories:
        # If the dir ends in inv create the inv dataset if it doesn't already exist
        # if the dir ends in surf30 create the surf dataset if it doesn't already exist
        if dir.endswith("inv"):
            dataset_id = create_dataset("inv", engine_str)
        elif dir.endswith("surf30"):
            dataset_id = create_dataset("surf", engine_str)
        else:
            raise ValueError("Unknown dataset")
        paths.extend(
            [
                f"{dir}/pat_*",
            ]
        )
    loader.load_data(paths, dataset_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
