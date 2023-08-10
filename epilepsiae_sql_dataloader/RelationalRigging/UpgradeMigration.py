from alembic import op
import sqlalchemy as sa


def upgrade():
    # Add the index to the data_chunks table on patient_id, seizure_state, and data_type columns
    op.create_index(
        "idx_patient_seizure_data_type",
        "data_chunks",
        ["patient_id", "seizure_state", "data_type"],
    )


def downgrade():
    # Remove the index if we need to rollback the migration
    op.drop_index("idx_patient_seizure_data_type", table_name="data_chunks")
