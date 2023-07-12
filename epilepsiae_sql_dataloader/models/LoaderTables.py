"""
This module contains the models for the dataloader.
Everything here references what will be updated and queried to load data into an ML model later
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import BYTEA

Base = declarative_base()


class Patient(Base):
    """
    Patient class corresponds to the 'patients' table in the database.
    It is assumed that ID will always be set to the patient's ID in the database.

    Attributes:
    id: An integer that serves as the primary key.
    info: A string containing patient information.
    chunks: A relationship that links to the DataChunk instances associated with a patient.
    """
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True)
    info = Column(String)

    chunks = relationship('DataChunk', back_populates='patient', cascade='all, delete, delete-orphan')
    samples = relationship('DataChunk', back_populates='patient', cascade='all, delete, delete-orphan')
    seizures = relationship('DataChunk', back_populates='patient', cascade='all, delete, delete-orphan')


class Dataset(Base):
    """
    Dataset class corresponds to the 'datasets' table in the database.

    Attributes:
    id: An integer that serves as the primary key.
    name: A string representing the dataset name (such as 'inv', 'inv2', or 'surf30').
    chunks: A relationship that links to the DataChunk instances associated with a dataset.
    """
    __tablename__ = 'datasets'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    chunks = relationship('DataChunk', back_populates='dataset', cascade='all, delete, delete-orphan')


class SeizureState(Base):
    """
    SeizureState class corresponds to the 'seizure_states' table in the database.

    Attributes:
    id: An integer that serves as the primary key.
    state: A string representing the seizure state (such as 'pre-seiz', 'non-seiz', or 'seizure').
    chunks: A relationship that links to the DataChunk instances associated with a seizure state.
    """
    __tablename__ = 'seizure_states'

    id = Column(Integer, primary_key=True)
    state = Column(String)

    chunks = relationship('DataChunk', back_populates='state', cascade='all, delete, delete-orphan')


class DataChunk(Base):
    """
    DataChunk class corresponds to the 'data_chunks' table in the database.

    Attributes:
    id: An integer that serves as the primary key.
    patient_id: An integer that serves as the foreign key linking to the 'patients' table.
    dataset_id: An integer that serves as the foreign key linking to the 'datasets' table.
    state_id: An integer that serves as the foreign key linking to the 'seizure_states' table.
    data: A binary type holding 256 uint16 values. Or 1 second of downsampled data. 512 Bytes as 256 uint16 values.
    patient: A relationship that links to the Patient instance associated with a data chunk.
    dataset: A relationship that links to the Dataset instance associated with a data chunk.
    state: A relationship that links to the SeizureState instance associated with a data chunk.
    """
    __tablename__ = 'data_chunks'

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    dataset_id = Column(Integer, ForeignKey('datasets.id'))
    state_id = Column(Integer, ForeignKey('seizure_states.id'))
    data = Column(BYTEA)

    patient = relationship('Patient', back_populates='chunks')
    dataset = relationship('Dataset', back_populates='chunks')
    state = relationship('SeizureState', back_populates='chunks')
