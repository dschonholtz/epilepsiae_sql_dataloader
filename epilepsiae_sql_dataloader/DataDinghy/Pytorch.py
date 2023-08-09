from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from torch.utils.data import Dataset, DataLoader
from epilepsiae_sql_dataloader.models.LoaderTables import (
    DataChunk,
    Dataset as DBDataset,
    Patient,
)


class SeizureDataset(Dataset):
    def __init__(self, session: Session, batch_size=1000, transform=None):
        self.session = session
        self.transform = transform
        self.batch_size = batch_size
        self.data_chunk_ids = session.query(DataChunk.id).all()
        self.total_chunks = len(self.data_chunk_ids)

    def __len__(self):
        return self.total_chunks

    def __getitem__(self, idx):
        # Fetch the primary key for the desired index
        data_chunk_id = self.data_chunk_ids[idx]

        # Query the corresponding data chunk by primary key
        data_chunk = self.session.query(DataChunk).get(data_chunk_id)

        sample_data = {
            "data": data_chunk.data,
            "seizure_state": data_chunk.seizure_state,
            "data_type": data_chunk.data_type,
        }

        if self.transform:
            sample_data = self.transform(sample_data)

        return sample_data


def get_data_loader(dataset, batch_size=1, shuffle=False, num_workers=0):
    return DataLoader(
        dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers
    )
