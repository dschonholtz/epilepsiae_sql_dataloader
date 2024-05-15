"""
Example header file
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
"""

from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    BigInteger,
    MetaData,
    ForeignKey,
)


import datetime


class SampleValidator:
    @staticmethod
    def validate_start_ts(start_ts):
        if not isinstance(start_ts, datetime.datetime):
            raise TypeError(
                "start_ts must be a datetime.datetime object. but is of type: "
                + str(type(start_ts))
                + " with value: "
                + str(start_ts)
            )

    @staticmethod
    def validate_num_samples(num_samples):
        if not isinstance(num_samples, int):
            raise TypeError("num_samples must be an integer.")

    @staticmethod
    def validate_sample_freq(sample_freq):
        if not isinstance(sample_freq, int):
            raise TypeError("sample_freq must be an integer.")

    @staticmethod
    def validate_conversion_factor(conversion_factor):
        if not isinstance(conversion_factor, float):
            raise TypeError("conversion_factor must be a float.")

    @staticmethod
    def validate_num_channels(num_channels):
        if not isinstance(num_channels, int):
            raise TypeError("num_channels must be an integer.")

    @staticmethod
    def validate_elec_names(elec_names):
        if not isinstance(elec_names, str):
            raise TypeError("elec_names must be a string.")
        SampleValidator.elect_names_to_list(elec_names)

    @staticmethod
    def validate_adm_id(adm_id):
        if not isinstance(adm_id, int):
            raise TypeError("adm_id must be an integer.")

    @staticmethod
    def validate_rec_id(rec_id):
        if not isinstance(rec_id, int):
            raise TypeError("rec_id must be an integer.")

    @staticmethod
    def validate_duration_in_sec(duration_in_sec):
        if not isinstance(duration_in_sec, int):
            raise TypeError("duration_in_sec must be an integer.")

    @staticmethod
    def validate_sample_bytes(sample_bytes):
        if not isinstance(sample_bytes, int):
            raise TypeError("sample_bytes must be an integer.")

    @staticmethod
    def validate_data_file(data_file):
        if not isinstance(data_file, str):
            raise TypeError("data_file must be a string.")

    @staticmethod
    def elect_names_to_list(elec_names):
        try:
            elec_names_list = elec_names.strip("[]").split(",")
            elec_names_list = [
                name.strip().replace("'", "") for name in elec_names_list
            ]
        except:
            raise ValueError("elec_names must be a string representation of a list.")
        return elec_names_list

    @classmethod
    def validate_all(cls, **kwargs):
        cls.validate_start_ts(kwargs.get("start_ts"))
        cls.validate_num_samples(kwargs.get("num_samples"))
        cls.validate_sample_freq(kwargs.get("sample_freq"))
        cls.validate_conversion_factor(kwargs.get("conversion_factor"))
        cls.validate_num_channels(kwargs.get("num_channels"))
        cls.validate_elec_names(kwargs.get("elec_names"))
        cls.validate_adm_id(kwargs.get("adm_id"))
        cls.validate_rec_id(kwargs.get("rec_id"))
        cls.validate_duration_in_sec(kwargs.get("duration_in_sec"))
        cls.validate_sample_bytes(kwargs.get("sample_bytes"))
        cls.validate_data_file(kwargs.get("data_file"))


samples_table = Table(
    "samples",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("start_ts", DateTime, nullable=False),
    Column("num_samples", Integer, nullable=False),
    Column("sample_freq", Integer, nullable=False),
    Column("conversion_factor", Float, nullable=False),
    Column("num_channels", Integer, nullable=False),
    Column("elec_names", String, nullable=False),
    Column("pat_id", Integer, ForeignKey("patients.id"), nullable=False),
    Column("adm_id", Integer, nullable=False),
    Column("rec_id", BigInteger, nullable=False),
    Column("duration_in_sec", Integer, nullable=False),
    Column("sample_bytes", Integer, nullable=False),
    Column("data_file", String, nullable=False),
)
