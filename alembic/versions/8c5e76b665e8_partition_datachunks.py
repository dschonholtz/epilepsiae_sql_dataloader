"""partition datachunks

Revision ID: 8c5e76b665e8
Revises: 50c56b447bba
Create Date: 2023-08-16 14:44:44.794525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8c5e76b665e8"
down_revision: Union[str, None] = "50c56b447bba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Step 1: Create the new partitioned table
    op.execute(
        """
        CREATE TABLE data_chunks_partitioned LIKE data_chunks INCLUDING ALL
        PARTITION BY LIST (data_type, seizure_state);
    """
    )

    # Step 2: Create the partitions
    data_types = [0, 1, 2, 3]
    seizure_states = [0, 1, 2]
    for dt in data_types:
        for ss in seizure_states:
            op.execute(
                f"""
                CREATE TABLE data_chunks_{dt}_{ss} PARTITION OF data_chunks_partitioned
                FOR VALUES IN ({dt}, {ss});
            """
            )

    # Step 3: Copy data from old table to new partitioned table
    op.execute(
        """
        INSERT INTO data_chunks_partitioned SELECT * FROM data_chunks;
    """
    )

    # Step 4: Rename tables
    op.execute(
        """
        ALTER TABLE data_chunks RENAME TO data_chunks_old;
        ALTER TABLE data_chunks_partitioned RENAME TO data_chunks;
    """
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
