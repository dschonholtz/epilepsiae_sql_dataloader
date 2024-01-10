"""
This module contains the models for the dataloader.
Everything here references what will be updated and queried to load data into an ML model later
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    SmallInteger,
    Index,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import BYTEA
from epilepsiae_sql_dataloader.models.Seizures import Seizure
from epilepsiae_sql_dataloader.models.Base import Base
import sqlalchemy


class Dataset(Base):
    """
    Dataset class corresponds to the 'datasets' table in the database.

    Attributes:
    id: An integer that serves as the primary key.
    name: A string representing the dataset name (such as 'inv', 'inv2', or 'surf30').
    chunks: A relationship that links to the DataChunk instances associated with a dataset.
    """

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    patients = relationship(
        "Patient", back_populates="dataset", cascade="all, delete, delete-orphan"
    )


class Patient(Base):
    """
    Patient class corresponds to the 'patients' table in the database.
    It is assumed that ID will always be set to the patient's ID in the database.

    Attributes:
    id: An integer that serves as the primary key.
    info: A string containing patient information.
    chunks: A relationship that links to the DataChunk instances associated with a patient.
    """

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


class DataChunk(Base):
    """
    DataChunk class corresponds to the 'data_chunks' table in the database.

    Attributes:
    id: An integer that serves as the primary key.
    patient_id: An integer that serves as the foreign key linking to the 'patients' table.
    dataset_id: An integer that serves as the foreign key linking to the 'datasets' table.
    seizure_state: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure
    data_type: An integer that is 0 for ieeg, 1 for ecg 2 for ekg, and 3 for eeg.
    data: A binary type holding 256 uint16 values. Or 1 second of downsampled data. 512 Bytes as 256 uint16 values.
    patient: A relationship that links to the Patient instance associated with a data chunk.
    dataset: A relationship that links to the Dataset instance associated with a data chunk.
    state: A relationship that links to the SeizureState instance associated with a data chunk.
    seizure_state_15m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 15 minutes
    seizure_state_30m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 30 minutes
    seizure_state_45m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 45 minutes
    seizure_state_60m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 60 minutes
    seizure_state_75m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 75 minutes
    seizure_state_90m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 90 minutes
    seizure_state_105m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 105 minutes
    seizure_state_120m: An integer that is a 0 for non-seizure data and 1 for seizure data and 2 for pre-seizure at 120 minutes
    """

    __tablename__ = "data_chunks"

    id = Column(BigInteger, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    data_type = Column(SmallInteger)
    data = Column(BYTEA)
    seizure_state = Column(Integer)
    seizure_state_15m = Column(Integer)
    seizure_state_30m = Column(Integer)
    seizure_state_45m = Column(Integer)
    seizure_state_60m = Column(Integer)
    seizure_state_75m = Column(Integer)
    seizure_state_90m = Column(Integer)
    seizure_state_105m = Column(Integer)
    seizure_state_120m = Column(Integer)

    patient = relationship(Patient, back_populates="chunks")
    idx_patient_seizure_data_type = Index(
        "idx_patient_seizure_data_type", "patient_id", "data_type", "seizure_state"
    )


def object_as_dict(obj):
    """
    Converts an SQLAlchemy object into a dictionary.

    Args:
    obj: An SQLAlchemy object.

    Returns:
    dict: A dictionary representation of the object.
    """
    return {
        c.key: getattr(obj, c.key) for c in sqlalchemy.inspect(obj).mapper.column_attrs
    }


class dict_with_attrs:
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)
