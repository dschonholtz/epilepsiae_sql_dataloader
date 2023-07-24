"""
This is a CLI tool that allows you to load data from the https://epilepsiae.uniklinik-freiburg.de/ 
dataset into a SQL database.
It is pointed at a database that has already been configured with the tables from 
epilepsiae_sql_dataloader/models/LoaderTables.py and the MetaDataBuilder class also in RelationshalRigging

Samples are already defined:
class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True)
    start_ts = Column(DateTime, nullable=False)
    num_samples = Column(Integer, nullable=False)
    sample_freq = Column(Integer, nullable=False)
    conversion_factor = Column(Float, nullable=False)
    num_channels = Column(Integer, nullable=False)
    elec_names = Column(String, nullable=False)
    pat_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    adm_id = Column(Integer, nullable=False)
    rec_id = Column(BigInteger, nullable=False)
    duration_in_sec = Column(Integer, nullable=False)
    sample_bytes = Column(Integer, nullable=False)
    data_file = Column(String, nullable=False)

    patient = relationship("Patient", back_populates="samples")

Seizures are already defined:
class Seizure(Base):
    __tablename__ = "seizures"

    id = Column(Integer, primary_key=True)
    pat_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    onset = Column(DateTime, nullable=False)
    offset = Column(DateTime, nullable=False)
    onset_sample = Column(Integer, nullable=False)
    offset_sample = Column(Integer, nullable=False)

    patient = relationship("Patient", back_populates="seizures")

Patients and datasets are also already defined:
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))

    dataset = relationship("Dataset", back_populates="patients")
    chunks = relationship(
        "DataChunk", back_populates="patient", cascade="all, delete, delete-orphan"
    )
    samples = relationship(
        "Sample", back_populates="patient", cascade="all, delete, delete-orphan"
    )
    seizures = relationship(
        "Seizure", back_populates="patient", cascade="all, delete, delete-orphan"
    )

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    patients = relationship(
        "Patient", back_populates="dataset", cascade="all, delete, delete-orphan"
    )

The only thing this class adds is DataChunks:
class DataChunk(Base):
```
    DataChunk class corresponds to the 'data_chunks' table in the database.

    Attributes:
    id: An integer that serves as the primary key.
    patient_id: An integer that serves as the foreign key linking to the 'patients' table.
    dataset_id: An integer that serves as the foreign key linking to the 'datasets' table.
    state_id: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure
    data: A binary type holding 256 uint16 values. Or 1 second of downsampled data. 512 Bytes as 256 uint16 values.
    patient: A relationship that links to the Patient instance associated with a data chunk.
    dataset: A relationship that links to the Dataset instance associated with a data chunk.
    state: A relationship that links to the SeizureState instance associated with a data chunk.
    ```

    __tablename__ = "data_chunks"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    seizure_state = Column(Integer)
    data = Column(BYTEA)

    patient = relationship(Patient, back_populates="chunks")

The way this file accomplishes that.
Is by reading in an entire binary blob, finding the corresponding sample and seizure information
Noting the exact sample now and after downsamping, downsampling, then breaking the data into 1 second chunks, then applying the seizure state
info accordingly.
"""

from epilepsiae_sql_dataloader.utils import session_scope
from epilepsiae_sql_dataloader.models.LoaderTables import (
    Patient,
    Dataset,
    DataChunk,
)

from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure
import numpy as np
from scipy.signal import decimate
from sklearn.preprocessing import normalize
from datetime import timedelta


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
            return (
                session.query(Seizure)
                .where(Seizure.pat_id == pat_id)
                .order_by(Seizure.onset)
                .all()
            )

    def get_patient_samples(self, pat_id):
        """
        Retrieves all samples from the 'samples' table in the database.
        Sorting them by start_ts

        Returns:
        list[Sample]: A list of all Sample instances in the database.
        """
        with session_scope(self.engine_str) as session:
            return (
                session.query(Sample)
                .where(Sample.pat_id == pat_id)
                .order_by(Sample.start_ts)
                .all()
            )

    def load_binary(self, fp, dtype=np.uint16):
        binary = np.fromfile(fp, dtype=dtype)
        return binary

    def preprocess_binary(self, binary, sample_freq, new_sample_freq):
        """
        Downsamples and normalizes the given binary data.
        """
        # Downsample the data
        decimate_factor = sample_freq // new_sample_freq
        x = decimate(binary, decimate_factor, axis=1)
        x = normalize(x, norm="l2", axis=1, copy=True, return_norm=False)
        return x

    def get_dataset_id(self, dataset_name):
        """
        Retrieves the ID for the given dataset name.

        Args:
        dataset_name (str): The name of the dataset.

        Returns:
        int: The ID of the dataset.
        """
        with session_scope(self.engine_str) as session:
            dataset = session.query(Dataset).filter(Dataset.name == dataset_name).one()
            return dataset.id

    def break_into_chunks(self, data, sample_freq):
        """
        Breaks the given data into one-second chunks based on the sample frequency.

        Args:
        data (list[int]): The data to be broken into chunks.
        sample_freq (int): The sample frequency, i.e., the number of data points per second.

        Returns:
        list[list[int]]: The data broken into one-second chunks.
        """
        # Determine the number of chunks
        num_chunks = len(data) // sample_freq

        # Break the data into chunks
        chunks = [
            data[i * sample_freq : (i + 1) * sample_freq] for i in range(num_chunks)
        ]

        return chunks

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
                seizure.onset - timedelta(seconds=pre_seizure_time)
                <= chunk_end_ts
                < seizure.onset
            ):
                seizure_state = 2  # The chunk is during the pre-seizure period
        return seizure_state

    def load_patient(self, pat_id):
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

        sample = samples[0]  # get first sample

        # Load binary data
        binary_data = self.load_binary(sample.data_file)

        # Downsample binary data to 256 Hz
        downsampled_data = self.preprocess_binary(binary_data, sample.sample_freq, 256)

        # Break downsampled data into 1-second chunks
        chunks = self.break_into_chunks(downsampled_data, 256)

        # Apply seizure state to each chunk
        for i, chunk in enumerate(chunks):
            chunk_start_ts = sample.start_ts + timedelta(seconds=i)
            chunk_end_ts = chunk_start_ts + timedelta(seconds=1)
            seizure_state = self.get_seizure_state(
                seizures, chunk_start_ts, chunk_end_ts
            )

            # Here you could add code to save the chunk and its seizure state to the database

        # This function currently doesn't return anything. Depending on your needs, you might want to return the chunks, seizure states, or any other data.
