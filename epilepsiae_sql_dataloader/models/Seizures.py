from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

"""
Example seizure file

# list of seizures of patient FR_1084

# columns are tab-separated:
# onset	offset	onset_sample	offset_sample
2008-11-11 06:10:03.416992	2008-11-11 06:10:08.325195	1526187	1531213

2008-11-11 06:35:33.729492	2008-11-11 06:35:39.258789	3093227	3098889

2008-11-11 07:25:57.974609	2008-11-11 07:26:03.691406	2466790	2472644

2008-11-11 07:54:56.308594	2008-11-11 07:55:01.308594	558396	563516
"""


class Seizure(declarative_base()):
    __tablename__ = "seizures"

    id = Column(Integer, primary_key=True)
    pat_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    onset = Column(DateTime, nullable=False)
    offset = Column(DateTime, nullable=False)
    onset_sample = Column(Integer, nullable=False)
    offset_sample = Column(Integer, nullable=False)

    patient = relationship("Patient", back_populates="seizures")

    def __repr__(self):
        return (
            f"<Seizure(onset={self.onset}, "
            f"offset={self.offset}, "
            f"onset_sample={self.onset_sample}, "
            f"offset_sample={self.offset_sample}, "
            f"pat_id={self.pat_id})>"
        )
