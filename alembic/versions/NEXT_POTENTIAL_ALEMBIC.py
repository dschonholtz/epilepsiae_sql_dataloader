"""Create new version of DataChunks table

Revision ID: <new_revision_id>
Revises: <previous_revision_id>
Create Date: <create_date>

o generate a new Alembic migration script, you can use the revision command. Here's how you can do it:

1. Navigate to the directory where your alembic.ini file is located. This is usually the root directory of your project.

2. Run the following command:
"

This will create a new script in your alembic/versions directory. The -m option allows you to add a message that describes the changes made in this revision.

3. Open the newly created script in your text editor. You'll see two functions: upgrade() and downgrade(). You should put the code to apply your changes in the upgrade() function, and the code to undo your changes in the downgrade() function.

4. After you've written your migration script, you can apply it with the upgrade command:
head

This will apply all migrations up to the "head" (the most recent one). If you want to apply only one migration, you can specify its revision number instead of head.

5. If you need to undo the changes made by a migration, you can use the downgrade command:
1

This will undo the last applied migration. If you want to undo all migrations, you can use alembic downgrade base.

Remember to test your migrations on a backup or a small subset of your data before applying them to the production database.


"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = "<new_revision_id>"
down_revision = "<previous_revision_id>"
branch_labels = None
depends_on = None


def upgrade():
    # Drop old table
    op.execute("DROP TABLE data_chunks;")

    # Create new table
    op.execute(
        """
    CREATE TABLE data_chunks (
        id INTEGER,
        patient_id INTEGER REFERENCES patients(id),
        seizure_state_15m INTEGER,
        seizure_state_30m INTEGER,
        seizure_state_45m INTEGER,
        seizure_state_60m INTEGER,
        seizure_state_75m INTEGER,
        seizure_state_90m INTEGER,
        seizure_state_105m INTEGER,
        seizure_state_120m INTEGER,
        data_type SMALLINT,
        data BYTEA,
        PRIMARY KEY (id, patient_id, data_type)
    ) PARTITION BY LIST (patient_id);
    """
    )

    # Get all patient_ids from the patient_ids table
    connection = op.get_bind()
    result = connection.execute(text("SELECT id FROM patients;"))
    patient_ids = [row[0] for row in result]

    # Create partitions for different patient_ids
    for pid in patient_ids:
        print("Creating partition for patient_id: ", pid)
        op.execute(
            f"""
        CREATE TABLE data_chunks_{pid} PARTITION OF data_chunks FOR VALUES IN ({pid})
        PARTITION BY LIST (data_type);
        """
        )

        # Create partitions for different data types
        for j in range(4):
            op.execute(
                f"""
            CREATE TABLE data_chunks_{pid}_{j} PARTITION OF data_chunks_{pid} FOR VALUES IN ({j});
            """
            )

    # Create new index for the new table
    # Index for patient_id
    op.create_index(
        "idx_patient_id",
        "data_chunks",
        ["patient_id"],
    )

    # Index for data_type
    op.create_index(
        "idx_data_type",
        "data_chunks",
        ["data_type"],
    )


def downgrade() -> None:
    # Drop new table
    op.execute("DROP TABLE data_chunks;")
