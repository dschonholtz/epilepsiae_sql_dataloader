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

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.sql import text


seizures = Table(
    "seizures",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("pat_id", Integer, ForeignKey("patients.id"), nullable=False),
    Column("onset", DateTime, nullable=False),
    Column("offset", DateTime, nullable=False),
    Column("onset_sample", Integer, nullable=False),
    Column("offset_sample", Integer, nullable=False),
)


def insert_seizure(connection, pat_id, onset, offset, onset_sample, offset_sample):
    insert_stmt = seizures.insert().values(
        pat_id=pat_id,
        onset=onset,
        offset=offset,
        onset_sample=onset_sample,
        offset_sample=offset_sample,
    )
    connection.execute(insert_stmt)
