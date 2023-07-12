from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey


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


class Sample(declarative_base()):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True)
    start_ts = Column(DateTime, nullable=False)
    num_samples = Column(Integer, nullable=False)
    sample_freq = Column(Integer, nullable=False)
    conversion_factor = Column(Float, nullable=False)
    num_channels = Column(Integer, nullable=False)
    elec_names = Column(String, nullable=False)
    pat_id = Column(Integer, ForeignKey('patients.id'), nullable=False)
    adm_id = Column(Integer, nullable=False)
    rec_id = Column(Integer, nullable=False)
    duration_in_sec = Column(Integer, nullable=False)
    sample_bytes = Column(Integer, nullable=False)
    data_file = Column(String, nullable=False)

    patient = relationship('Patient', back_populates='samples')
    chunks = relationship('DataChunk', back_populates='samples')

    def __repr__(self):
        return f"<Sample(start_ts={self.start_ts}, " \
               f"num_samples={self.num_samples}, " \
               f"sample_freq={self.sample_freq}, " \
               f"conversion_factor={self.conversion_factor}, " \
               f"num_channels={self.num_channels}, " \
               f"elec_names={self.elec_names}, " \
               f"pat_id={self.pat_id}, " \
               f"adm_id={self.adm_id}, " \
               f"rec_id={self.rec_id}, " \
               f"duration_in_sec={self.duration_in_sec}, " \
               f"sample_bytes={self.sample_bytes})" \
               f"data_file={self.data_file}>"
