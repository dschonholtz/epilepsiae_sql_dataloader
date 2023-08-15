"""
This is a CLI tool that allows you to load data from the https://epilepsiae.uniklinik-freiburg.de/ 
dataset into a SQL database.
It is pointed at a database that has already been configured with the tables from 
epilepsiae_sql_dataloader/models/LoaderTables.py and the MetaDataBuilder class also in RelationshalRigging

The way this file accomplishes that.
Is by reading in an entire binary blob, finding the corresponding sample and seizure information
Noting the exact sample now and after downsamping, downsampling, then breaking the data into 1 second chunks, then applying the seizure state
info accordingly.
"""

from epilepsiae_sql_dataloader.utils import session_scope, ENGINE_STR
from epilepsiae_sql_dataloader.models.LoaderTables import (
    Patient,
    Dataset,
    DataChunk,
    object_as_dict,
    dict_with_attrs,
)

from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure
import numpy as np
from scipy.signal import decimate
from sklearn.preprocessing import normalize
from datetime import timedelta
from typing import List

import os
import click


class BinaryToSql:
    def __init__(self, engine_str):
        """
        Initializes a new instance of the MetaDataBuilder class.

        Args:
        engine_str (str): A string representing the SQLAlchemy engine connection string.
        """
        self.engine_str = engine_str

    def get_patient_seizures(self, pat_id):
        """
        Retrieves all seizures from the 'seizures' table in the database.

        Returns:
        list[Seizure]: A list of all Seizure instances in the database.
        """
        with session_scope(self.engine_str) as session:
            results = (
                session.query(Seizure)
                .where(Seizure.pat_id == pat_id)
                .order_by(Seizure.onset)
                .all()
            )
            results = [dict_with_attrs(object_as_dict(seizure)) for seizure in results]
        return results

    def get_patient_samples(self, pat_id):
        """
        Retrieves all samples from the 'samples' table in the database.
        Sorting them by start_ts

        Returns:
        list[Sample]: A list of all Sample instances in the database.
        """
        with session_scope(self.engine_str) as session:
            results = (
                session.query(Sample)
                .where(Sample.pat_id == pat_id)
                .order_by(Sample.start_ts)
                .all()
            )
            results = [dict_with_attrs(object_as_dict(sample)) for sample in results]
        return results

    def load_binary(self, fp, num_channels, dtype=np.uint16):
        """
        Loads the binary data from the given file pointer.
        It is assumed that the binary data is stored as a 2D array of uint16 values of size -1, num_channels
        """
        print(f"Loading binary data from {fp}")
        binary = np.fromfile(fp, dtype=dtype)
        binary = binary.reshape(-1, num_channels)

        return binary

    def preprocess_binary(self, binary, sample_freq, new_sample_freq):
        """
        Downsamples and normalizes the given binary data.
        """
        # Downsample the data
        decimate_factor = sample_freq // new_sample_freq
        x = decimate(binary, decimate_factor, axis=0)
        x = normalize(x, norm="l2", axis=1, copy=True, return_norm=False)
        return x

    def get_dataset_id(self, patient_id):
        """
        Retrieves the ID for the given dataset name.

        Returns:
        int: The ID of the dataset.
        """
        with session_scope(self.engine_str) as session:
            # Get the dataset name from the patient information:
            patient = session.query(Patient).filter(Patient.id == patient_id).one()
            dataset_id = patient.dataset.id
            return dataset_id

    def break_into_chunks(
        self,
        session,
        data: np.ndarray,
        sample: Sample,
        seizures: List[Seizure],
        freq,
        sample_length: int = 1,
    ) -> List[DataChunk]:
        # Query the database to get the dataset associated with the patient
        dataset_id = self.get_dataset_id(sample.pat_id)
        dataset = session.query(Dataset).filter(Dataset.id == dataset_id).one()
        dataset_name = dataset.name

        data_chunks = []
        num_samples, num_channels = data.shape
        num_chunks = num_samples // (sample_length * freq)

        # Extract the electrode names for the sample (outside the loop)
        elect_names = Sample.elect_names_to_list(elect_names=sample.elec_names)

        # Go through the data chunk by chunk
        for i in range(num_chunks):
            chunk_start_ts = sample.start_ts + timedelta(seconds=i * sample_length)
            chunk_end_ts = chunk_start_ts + timedelta(seconds=sample_length)
            seizure_state = self.get_seizure_state(
                seizures, chunk_start_ts, chunk_end_ts
            )
            chunk_data = data[
                i * sample_length * freq : (i + 1) * sample_length * freq, :
            ]

            # Convert the entire chunk data to bytes
            chunk_data_bytes = chunk_data.astype(np.uint16).tobytes()

            # Separate the chunk into its component channels
            for j in range(num_channels):
                channel_data_bytes = chunk_data_bytes[
                    j * sample_length * freq * 2 : (j + 1) * sample_length * freq * 2
                ]

                # Create a DataChunk mapping (without instantiating an object)
                chunk_mapping = {
                    "data": channel_data_bytes,
                    "seizure_state": seizure_state,
                    "data_type": self.process_data_types(elect_names[j], dataset_name),
                    "patient_id": sample.pat_id,
                }

                data_chunks.append(chunk_mapping)

        # Use bulk insert to add all DataChunk mappings to the database
        session.bulk_insert_mappings(DataChunk, data_chunks)
        session.commit()

        return data_chunks

    def process_data_types(
        self,
        electrode: str,
        dataset_name: str,
    ) -> int:
        # Assign data types based on the dataset and electrode name
        if dataset_name == "inv":
            if electrode in {"ECG", "EKG"}:
                data_type = 1 if electrode == "ECG" else 2
            elif electrode in {
                "N",
                "FP",
                "AF",
                "F",
                "FT",
                "FC",
                "A",
                "T",
                "C",
                "TP",
                "CP",
                "P",
                "PO",
                "O",
                "I",
                "EMG",
                "EOG",
                "PHO",
            }:
                data_type = 3
            else:
                data_type = 0
        elif dataset_name == "surf":
            if electrode in {"ECG", "EKG"}:
                data_type = 1 if electrode == "ECG" else 2
            else:
                data_type = 3

        return data_type

    def get_seizure_state(
        self, seizures, chunk_start_ts, chunk_end_ts, pre_seizure_time=3600
    ):
        """
        Determines the seizure state for the given chunk.
        seizure_state: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure

        Args:
        seizures (list[Seizure]): A list of Seizure instances.
        chunk_start_ts (datetime.datetime): The timestamp for the start of the chunk.
        chunk_end_ts (datetime.datetime): The timestamp for the end of the chunk.
        pre_seizure_time (int): The number of seconds before a seizure to consider as pre-seizure data.

        Returns:
        int: The seizure state for the chunk.
        """
        # Determine the seizure state
        seizure_state = 0
        for seizure in seizures:
            if seizure.onset <= chunk_end_ts and seizure.offset >= chunk_start_ts:
                seizure_state = 1  # The chunk is during a seizure
                break
            elif (
                seizure.onset - timedelta(seconds=pre_seizure_time) <= chunk_end_ts
                and seizure.onset >= chunk_end_ts
            ):
                seizure_state = 2  # The chunk is during the pre-seizure period
        return seizure_state

    def load_patient(self, pat_id: int):
        """
        Gets the seizures and samples for the given patient.
        Loads the first two seizures and the first sample.
        Gets the first binary file corresponding with the first sample.data_file
        Loads the binary file and down_samples it to 256 Hz
        Breaks the binary file into 1 second chunks
        Applies the seizure state to each chunk checking against the timestamp the sample started and what 1 second chunk we are on.
        """
        seizures = self.get_patient_seizures(pat_id)
        samples = self.get_patient_samples(pat_id)
        bad_binaries = 0

        for i, sample in enumerate(samples):
            with session_scope(self.engine_str) as session:
                # Load binary data
                print(f"Handling sample: {i} of {len(samples)}")
                try:
                    binary_data = self.load_binary(
                        sample.data_file, sample.num_channels
                    )
                except Exception as e:
                    print(f"Error loading binary data for sample: {sample}")
                    # we don't wan tto stop the whole process if one sample is bad.
                    print(e)
                    bad_binaries += 1
                    continue

                try:
                    # Downsample binary data to 256 Hz
                    down_sampled = self.preprocess_binary(
                        binary_data, sample.sample_freq, 256
                    )
                except Exception as e:
                    print(f"Error downsampling binary data for sample: {sample}")
                    print(e)
                    bad_binaries += 1
                    continue

                try:
                    # Break downsampled data into 1-second chunks
                    self.break_into_chunks(
                        session, down_sampled, sample, seizures, 256, sample_length=1
                    )
                except Exception as e:
                    print(
                        f"Error breaking downsampled data into chunks for sample: {sample}"
                    )
                    print(e)
                    bad_binaries += 1
                    continue
        print("Bad Binaries: ", bad_binaries)


DEFAULT_DIR = "/mnt/external1/raw/inv"


@click.command()
@click.option(
    "--dir", default=DEFAULT_DIR, help="Directory containing the patient folders"
)
def main(dir):
    """
    Loops through all the pat directories in the given directory, extracts the patient ID, and processes the data using the BinaryToSQL class.
    """
    # Check if the directory exists
    if not os.path.exists(dir):
        click.echo(f"Directory {dir} does not exist.")
        return

    # Create an instance of BinaryToSQL
    binary_to_sql = BinaryToSql(ENGINE_STR)

    # Loop through all directories with a "pat_" prefix
    pat_dirs = os.listdir(dir)
    for i, item in enumerate(pat_dirs):
        if os.path.isdir(os.path.join(dir, item)) and item.startswith("pat_"):
            # pat_21602 seizures aren't loading! We'll have to fix that. and we are skipping it
            # the others have already been done.
            if item in [
                "pat_81802",
                "pat_11502",
                "pat_109602",
                "pat_26402",
                "pat_21602",
            ]:
                continue
            # Extract the patient ID
            pat_id = int(item.split("_")[1])
            click.echo(f"Processing patient ID: {pat_id}")
            click.echo(f"On patient {i} of {len(pat_dirs)}")

            # Load patient data using the BinaryToSQL class
            binary_to_sql.load_patient(pat_id)

    click.echo("All patients processed successfully.")


if __name__ == "__main__":
    main()
