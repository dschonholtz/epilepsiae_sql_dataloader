"""add datachunk index

Revision ID: 50c56b447bba
Revises: 
Create Date: 2023-08-10 09:50:06.667561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "50c56b447bba"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_patient_seizure_data_type",
        "data_chunks",
        ["patient_id", "seizure_state", "data_type"],
    )


def downgrade() -> None:
    op.drop_index("idx_patient_seizure_data_type", table_name="data_chunks")
