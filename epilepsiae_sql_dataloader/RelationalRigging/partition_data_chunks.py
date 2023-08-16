from sqlalchemy import create_engine, text
from epilepsiae_sql_dataloader.utils import ENGINE_STR


def partition_data_chunks_table():
    engine = create_engine(ENGINE_STR)

    with engine.connect() as connection:
        # Convert the existing table to a partitioned table
        connection.execute(
            text(
                """
            ALTER TABLE data_chunks PARTITION BY LIST (data_type);
        """
            )
        )

        # Create partitions for specific values of data_type
        connection.execute(
            text(
                "CREATE TABLE data_chunks_ieeg PARTITION OF data_chunks FOR VALUES IN (0)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE data_chunks_ecg PARTITION OF data_chunks FOR VALUES IN (1)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE data_chunks_ekg PARTITION OF data_chunks FOR VALUES IN (2)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE data_chunks_eeg PARTITION OF data_chunks FOR VALUES IN (3)"
            )
        )

        # Create indexes for the individual partitions
        connection.execute(
            text(
                "CREATE INDEX idx_data_chunks_ieeg ON data_chunks_ieeg (patient_id, seizure_state, data_type)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX idx_data_chunks_ecg ON data_chunks_ecg (patient_id, seizure_state, data_type)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX idx_data_chunks_ekg ON data_chunks_ekg (patient_id, seizure_state, data_type)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX idx_data_chunks_eeg ON data_chunks_eeg (patient_id, seizure_state, data_type)"
            )
        )

        print("Partitioning applied successfully!")


if __name__ == "__main__":
    partition_data_chunks_table()
