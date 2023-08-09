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
    def __init__(
        self,
        session: Session,
        data_type=None,
        seizure_state=None,
        dataset_id=None,
        patient_id=None,
        transform=None,
    ):
        self.session = session
        self.transform = transform

        query = session.query(DataChunk)

        if data_type is not None:
            query = query.filter(DataChunk.data_type == data_type)

        if seizure_state is not None:
            query = query.filter(DataChunk.seizure_state == seizure_state)

        if dataset_id is not None:
            query = query.join(Dataset).filter(Dataset.id == dataset_id)

        if patient_id is not None:
            query = query.join(Patient).filter(Patient.id == patient_id)

        self.data_chunks = query.all()

    def __len__(self):
        return len(self.data_chunks)

    def __getitem__(self, idx):
        data_chunk = self.data_chunks[idx]
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
