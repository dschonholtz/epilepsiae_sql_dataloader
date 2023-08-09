import tensorflow as tf
from sqlalchemy.orm import Session
from epilepsiae_sql_dataloader.models.LoaderTables import (
    DataChunk,
    Dataset as DBDataset,
    Patient,
)
from epilepsiae_sql_dataloader.utils import ENGINE_STR
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def seizure_data_generator(session: Session):
    data_chunk_ids = session.query(DataChunk.id).all()
    total_chunks = len(data_chunk_ids)

    for idx in range(total_chunks):
        data_chunk_id = data_chunk_ids[idx]
        data_chunk = session.query(DataChunk).get(data_chunk_id)

        # Assuming data is stored as a sequence of integers
        data = [int(byte) for byte in data_chunk.data]
        seizure_state = data_chunk.seizure_state

        yield data, seizure_state


def get_seizure_dataset(session: Session, batch_size=32):
    # Define the generator function and output data types
    data_gen = lambda: seizure_data_generator(session)
    output_signature = (
        tf.TensorSpec(shape=(None,), dtype=tf.int32),
        tf.TensorSpec(shape=(), dtype=tf.int32),
    )

    # Create a tf.data.Dataset from the generator
    dataset = tf.data.Dataset.from_generator(
        data_gen, output_signature=output_signature
    )

    return dataset.batch(batch_size)


# Define a simple model
def build_model(input_shape):
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Embedding(
                input_dim=256, output_dim=16, input_shape=input_shape
            ),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )

    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model


# Create a session
engine = create_engine(ENGINE_STR)
Session = sessionmaker(bind=engine)
session = Session()

# Create the dataset
dataset = get_seizure_dataset(session)
input_shape = dataset.element_spec[0].shape[1:]

# Build the model
model = build_model(input_shape)

# Train the model
model.fit(dataset, epochs=10)
