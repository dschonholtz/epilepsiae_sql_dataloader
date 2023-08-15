from sqlalchemy import create_engine, text
from epilepsiae_sql_dataloader.utils import ENGINE_STR


def refresh_materialized_view():
    engine = create_engine(ENGINE_STR)

    with engine.connect() as connection:
        # Refresh the materialized view
        connection.execute(text("REFRESH MATERIALIZED VIEW data_chunk_summary"))


if __name__ == "__main__":
    refresh_materialized_view()
    print("Materialized view refreshed successfully!")
