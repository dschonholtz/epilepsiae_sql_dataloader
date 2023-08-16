"""partition datachunks

Revision ID: 8c5e76b665e8
Revises: 50c56b447bba
Create Date: 2023-08-16 14:44:44.794525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import BYTEA

# revision identifiers, used by Alembic.
revision: str = "8c5e76b665e8"
down_revision: Union[str, None] = "50c56b447bba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "data_chunks_partitioned",
        Column("id", Integer, primary_key=True),
        Column("patient_id", Integer, ForeignKey("patients.id")),
        Column("seizure_state", Integer),
        Column("data_type", SmallInteger),
        Column("data", BYTEA),
    )

    op.execute(
        "CREATE TABLE data_chunks_partitioned_0 PARTITION OF data_chunks_partitioned FOR VALUES IN (0);"
    )
    op.execute(
        "CREATE TABLE data_chunks_partitioned_1 PARTITION OF data_chunks_partitioned FOR VALUES IN (1);"
    )
    op.execute(
        "CREATE TABLE data_chunks_partitioned_2 PARTITION OF data_chunks_partitioned FOR VALUES IN (2);"
    )

    op.execute("INSERT INTO data_chunks_partitioned SELECT * FROM data_chunks;")

    op.rename_table("data_chunks", "data_chunks_old")
    op.rename_table("data_chunks_partitioned", "data_chunks")

    # Recreate indexes if necessary
    op.create_index(
        "idx_patient_seizure_data_type",
        "data_chunks",
        ["patient_id", "seizure_state", "data_type"],
    )


def downgrade():
    # Step 1: Rename tables
    op.execute(
        """
        ALTER TABLE data_chunks RENAME TO data_chunks_partitioned;
        ALTER TABLE data_chunks_old RENAME TO data_chunks;
    """
    )

    # Step 2: Drop the new partitioned table
    op.execute(
        """
        DROP TABLE data_chunks_partitioned;
    """
    )

    # Note: The individual partition tables will be automatically dropped
