"""patient_id partitions for data_chunks

Revision ID: dabdda1fb359
Revises: 8c5e76b665e8
Create Date: 2023-08-18 10:52:17.327789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = "dabdda1fb359"
down_revision: Union[str, None] = "8c5e76b665e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create new partitioned table
    op.execute(
        """
    CREATE TABLE data_chunks_new (
        id INTEGER,
        patient_id INTEGER REFERENCES patients(id),
        seizure_state INTEGER,
        data_type SMALLINT,
        data BYTEA,
        PRIMARY KEY (id, patient_id, seizure_state, data_type)
    ) PARTITION BY LIST (patient_id);
    """
    )

    # Get all patient_ids from the patient_ids table
    connection = op.get_bind()
    result = connection.execute(text("SELECT id FROM patients;"))
    for row in result:
        print(row)
        break
    patient_ids = [row["id"] for row in result]

    # Create first-level partitions for different patient_ids
    for pid in patient_ids:
        print("Creating partition for patient_id: ", pid)
        op.execute(
            f"""
        CREATE TABLE data_chunks_new_{pid} PARTITION OF data_chunks_new FOR VALUES IN ({pid})
        PARTITION BY LIST (seizure_state);
        """
        )

        # Create second-level partitions for different seizure states
        for i in range(3):
            op.execute(
                f"""
            CREATE TABLE data_chunks_new_{pid}_{i} PARTITION OF data_chunks_new_{pid} FOR VALUES IN ({i})
            PARTITION BY LIST (data_type);
            """
            )

            # Create third-level partitions for different data types
            for j in range(4):
                op.execute(
                    f"""
                CREATE TABLE data_chunks_new_{pid}_{i}_{j} PARTITION OF data_chunks_new_{pid}_{i} FOR VALUES IN ({j});
                """
                )

    # Migrate data from the original table to the new partitioned table
    op.execute("INSERT INTO data_chunks_new SELECT * FROM data_chunks;")

    # Rename original and new tables
    op.rename_table("data_chunks", "data_chunks_old")
    op.rename_table("data_chunks_new", "data_chunks")

    # Drop the old index
    op.drop_index("idx_patient_seizure_data_type", table_name="data_chunks_old")

    # Create new index for the new table
    # Index for patient_id
    op.create_index(
        "idx_patient_id",
        "data_chunks",
        ["patient_id"],
    )

    # Index for seizure_state
    op.create_index(
        "idx_seizure_state",
        "data_chunks",
        ["seizure_state"],
    )

    # Index for data_type
    op.create_index(
        "idx_data_type",
        "data_chunks",
        ["data_type"],
    )

    # Drop old table
    op.execute("DROP TABLE data_chunks_old;")


def downgrade() -> None:
    pass
