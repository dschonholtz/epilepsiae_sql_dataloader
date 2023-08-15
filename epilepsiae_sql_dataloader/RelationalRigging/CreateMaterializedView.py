from sqlalchemy import create_engine, text
from epilepsiae_sql_dataloader.utils import ENGINE_STR


def create_materialized_view():
    engine = create_engine(ENGINE_STR)

    with engine.connect() as connection:
        # Create the materialized view
        connection.execute(
            text(
                """
            CREATE MATERIALIZED VIEW data_chunk_summary AS
            SELECT
                id,
                patient_id,
                data_type,
                seizure_state,
                COUNT(id) AS count
            FROM
                data_chunks
            GROUP BY
                patient_id, data_type, seizure_state
        """
            )
        )

        # Create an index to speed up queries
        connection.execute(
            text(
                "CREATE INDEX idx_data_chunk_summary_patient ON data_chunk_summary (patient_id)"
            )
        )


if __name__ == "__main__":
    create_materialized_view()
    print("Materialized view created successfully!")
