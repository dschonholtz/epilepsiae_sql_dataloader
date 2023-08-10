"""
I created this, but the tensorflow install docs are intimidating.
I have not installed tensorflow bundled in this repo. 
if you install tensorflow in the venv, you should still be able to run this script.
"""

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


def seizure_data_generator(session: Session, seizure_states=[0, 2], data_types=None):
    # Construct the query for fetching the IDs
    query = session.query(DataChunk.id)

    # Apply seizure state filter if specified
    if seizure_states is not None:
        query = query.filter(DataChunk.seizure_state.in_(seizure_states))

    # Apply data type filter if specified
    if data_types is not None:
        query = query.filter(DataChunk.data_type.in_(data_types))

    data_chunk_ids = query.all()
    total_chunks = len(data_chunk_ids)

    for idx in range(total_chunks):
        data_chunk_id = data_chunk_ids[idx]
        data_chunk = session.query(DataChunk).get(data_chunk_id)

        # Assuming data is stored as a sequence of integers
        data = [int(byte) for byte in data_chunk.data]
        seizure_state = data_chunk.seizure_state

        yield data, seizure_state


def get_seizure_dataset(
    session: Session, seizure_states=[0, 2], data_types=None, batch_size=32
):
    # Define the generator function and output data types
    data_gen = lambda: seizure_data_generator(
        session, seizure_states=seizure_states, data_types=data_types
    )
    output_signature = (
        tf.TensorSpec(shape=(None,), dtype=tf.int32),
        tf.TensorSpec(shape=(), dtype=tf.int32),
    )

    # Create a tf.data.Dataset from the generator
    dataset = tf.data.Dataset.from_generator(
        data_gen, output_signature=output_signature
    )

    return dataset.batch(batch_size)


def train_seizure_model(
    session: Session, seizure_states=[0, 2], data_types=None, batch_size=32, epochs=10
):
    # Create the dataset
    dataset = get_seizure_dataset(
        session,
        seizure_states=seizure_states,
        data_types=data_types,
        batch_size=batch_size,
    )

    # Determine the input shape from the dataset
    for data, _ in dataset.take(1):
        input_shape = data.shape[1:]

    # Define a simple LSTM-based model for binary classification
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Embedding(
                input_dim=256, output_dim=16, input_shape=input_shape
            ),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )

    # Compile the model
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

    # Train the model
    history = model.fit(dataset, epochs=epochs)

    return model, history
