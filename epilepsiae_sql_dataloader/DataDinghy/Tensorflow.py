import tensorflow as tf
from sqlalchemy.orm import Session
from epilepsiae_sql_dataloader.models.LoaderTables import (
    DataChunk,
    Dataset as DBDataset,
    Patient,
)


class SeizureDataGenerator(tf.keras.utils.Sequence):
    def __init__(
        self,
        session: Session,
        data_type=None,
        seizure_state=None,
        dataset_id=None,
        patient_id=None,
        batch_size=32,
        shuffle=True,
    ):
        self.session = session
        self.batch_size = batch_size
        self.shuffle = shuffle

        query = session.query(DataChunk)

        if data_type is not None:
            query = query.filter(DataChunk.data_type == data_type)

        if seizure_state is not None:
            query = query.filter(DataChunk.seizure_state == seizure_state)

        if dataset_id is not None:
            query = query.join(DBDataset).filter(DBDataset.id == dataset_id)

        if patient_id is not None:
            query = query.join(Patient).filter(Patient.id == patient_id)

        self.data_chunks = query.all()
        self.indices = list(range(len(self.data_chunks)))
        self.on_epoch_end()

    def __len__(self):
        return int(len(self.data_chunks) / self.batch_size)

    def __getitem__(self, idx):
        indices_batch = self.indices[
            idx * self.batch_size : (idx + 1) * self.batch_size
        ]
        data_chunk_batch = [self.data_chunks[i] for i in indices_batch]

        X = []
        y = []
        for data_chunk in data_chunk_batch:
            X.append(data_chunk.data)
            y.append(data_chunk.seizure_state)

        return tf.convert_to_tensor(X, dtype=tf.float32), tf.convert_to_tensor(
            y, dtype=tf.int32
        )

    def on_epoch_end(self):
        if self.shuffle:
            tf.random.shuffle(self.indices)
