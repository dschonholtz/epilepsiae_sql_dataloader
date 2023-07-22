from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from epilepsiae_sql_dataloader.models.LoaderTables import Patient
from epilepsiae_sql_dataloader.models.Base import Base


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


import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, BigInteger
from epilepsiae_sql_dataloader.models.LoaderTables import Patient
from epilepsiae_sql_dataloader.models.Base import Base


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

    def __init__(
        self,
        start_ts,
        num_samples,
        sample_freq,
        conversion_factor,
        num_channels,
        elec_names,
        adm_id,
        rec_id,
        duration_in_sec,
        sample_bytes,
        data_file,
    ):
        # Type verification for start_ts
        if not isinstance(start_ts, datetime.datetime):
            raise TypeError(
                "start_ts must be a datetime.datetime object. but is of type: "
                + str(type(start_ts))
                + " with value: "
                + str(start_ts)
            )

        # Type verification for num_samples
        if not isinstance(num_samples, int):
            raise TypeError("num_samples must be an integer.")

        # Type verification for sample_freq
        if not isinstance(sample_freq, int):
            raise TypeError("sample_freq must be an integer.")

        # Type verification for conversion_factor
        if not isinstance(conversion_factor, float):
            raise TypeError("conversion_factor must be a float.")

        # Type verification for num_channels
        if not isinstance(num_channels, int):
            raise TypeError("num_channels must be an integer.")

        # Type verification for elec_names
        if not isinstance(elec_names, str):
            raise TypeError("elec_names must be a string.")

        # Type verification for adm_id
        if not isinstance(adm_id, int):
            raise TypeError("adm_id must be an integer.")

        # Type verification for rec_id
        if not isinstance(rec_id, int):
            raise TypeError("rec_id must be an integer.")

        # Type verification for duration_in_sec
        if not isinstance(duration_in_sec, int):
            raise TypeError("duration_in_sec must be an integer.")

        # Type verification for sample_bytes
        if not isinstance(sample_bytes, int):
            raise TypeError("sample_bytes must be an integer.")

        # Type verification for data_file
        if not isinstance(data_file, str):
            raise TypeError("data_file must be a string.")

        # If all types are correct, assign the attributes
        self.start_ts = start_ts
        self.num_samples = num_samples
        self.sample_freq = sample_freq
        self.conversion_factor = conversion_factor
        self.num_channels = num_channels
        self.elec_names = elec_names
        self.adm_id = adm_id
        self.rec_id = rec_id
        self.duration_in_sec = duration_in_sec
        self.sample_bytes = sample_bytes
        self.data_file = data_file

    def __repr__(self):
        return (
            f"<Sample(start_ts={self.start_ts}, "
            f"num_samples={self.num_samples}, "
            f"sample_freq={self.sample_freq}, "
            f"conversion_factor={self.conversion_factor}, "
            f"num_channels={self.num_channels}, "
            f"elec_names={self.elec_names}, "
            f"pat_id={self.pat_id}, "
            f"adm_id={self.adm_id}, "
            f"rec_id={self.rec_id}, "
            f"duration_in_sec={self.duration_in_sec}, "
            f"sample_bytes={self.sample_bytes})"
            f"data_file={self.data_file}>"
        )
