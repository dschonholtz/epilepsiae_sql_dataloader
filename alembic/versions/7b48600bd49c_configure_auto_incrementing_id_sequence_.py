"""Configure auto-incrementing ID sequence for data_chunks

Revision ID: 7b48600bd49c
Revises: dabdda1fb359
Create Date: 2023-08-21 11:03:06.208588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = "7b48600bd49c"
down_revision: Union[str, None] = "dabdda1fb359"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create a sequence for the ID field
    op.execute("CREATE SEQUENCE data_chunks_id_seq;")

    # Alter the main table to use the sequence for the ID field
    op.execute(
        """
        ALTER TABLE data_chunks
        ALTER COLUMN id SET DEFAULT nextval('data_chunks_id_seq');
    """
    )

    op.create_index(
        "idx_data_chunks_id",
        "data_chunks",
        ["id"],
    )

    # Get all patient_ids from the patients table
    connection = op.get_bind()
    result = connection.execute(text("SELECT id FROM patients;"))
    patient_ids = [row[0] for row in result]

    # Alter each partition to use the sequence for the ID field
    for pid in patient_ids:
        for i in range(3):
            for j in range(4):
                partition_name = f"data_chunks_new_{pid}_{i}_{j}"
                op.execute(
                    f"""
                    ALTER TABLE {partition_name}
                    ALTER COLUMN id SET DEFAULT nextval('data_chunks_id_seq');
                """
                )

    # Optionally, you may want to set the sequence's current value if there are already rows in the table
    op.execute(
        "SELECT setval('data_chunks_id_seq', (SELECT MAX(id) FROM data_chunks));"
    )


def downgrade() -> None:
    pass
