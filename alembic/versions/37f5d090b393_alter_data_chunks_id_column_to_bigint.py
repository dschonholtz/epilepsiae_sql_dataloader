"""Alter data_chunks id column to BIGINT

Revision ID: 37f5d090b393
Revises: 7b48600bd49c
Create Date: 2023-08-22 10:02:49.186573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = "37f5d090b393"
down_revision: Union[str, None] = "7b48600bd49c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Alter the main table column type to BIGINT
    op.alter_column("data_chunks", "id", type_=sa.BigInteger())

    # Adjust the sequence to return BIGINT values
    op.execute("ALTER SEQUENCE data_chunks_id_seq AS BIGINT;")


def downgrade():
    pass
