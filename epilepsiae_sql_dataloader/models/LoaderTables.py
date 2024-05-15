"""
This module contains the models for the dataloader.
Everything here references what will be updated and queried to load data into an ML model later
"""

from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    ForeignKey,
    SmallInteger,
    BigInteger,
    MetaData,
    Index,
)
from sqlalchemy.dialects.postgresql import BYTEA

metadata = MetaData()

datasets = Table(
    "datasets",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
)

patients = Table(
    "patients",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("dataset_id", Integer, ForeignKey("datasets.id")),
)

data_chunks = Table(
    "data_chunks",
    metadata,
    Column("id", BigInteger, primary_key=True),
    Column("patient_id", Integer, ForeignKey("patients.id")),
    Column("data_type", SmallInteger),
    Column("data", BYTEA),
    Column("seizure_state", Integer),
    Column("seizure_state_5m", Integer),
    Column("seizure_state_15m", Integer),
    Column("seizure_state_30m", Integer),
    Column("seizure_state_60m", Integer),
    Column("seizure_state_90m", Integer),
    Column("seizure_state_120m", Integer),
    Index("idx_patient_seizure_data_type", "patient_id", "data_type", "seizure_state"),
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
