from epilepsiae_sql_dataloader.models.LoaderTables import (
    DataChunk,
    Dataset as DBDataset,
    Patient,
)
from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure

from epilepsiae_sql_dataloader.utils import ENGINE_STR
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from torch.utils.data import Dataset
import torch
from sqlalchemy.orm import Session
import torch.nn as nn
from torch.utils.data import DataLoader


DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class SeizureDataset(Dataset):
    def __init__(
        self,
        session: Session,
        patient_id: int,
        seizure_states=[0, 2],
        data_types=None,
        batch_size=1000,
        transform=None,
    ):
        self.session = session
        self.seizure_states = seizure_states
        self.data_types = data_types
        self.transform = transform
        self.batch_size = batch_size
        self.buffer = []
        self.buffer_index = 0
        print(
            "About to do query. (This part takes a couple minutes then we can move at light speed)"
        )

        # Construct the query for fetching the IDs
        query = session.query(DataChunk.id)

        # Apply patient filter
        query = query.filter(DataChunk.patient_id == patient_id)

        # Apply seizure state filter if specified
        if self.seizure_states is not None:
            query = query.filter(DataChunk.seizure_state.in_(self.seizure_states))

        # Apply data type filter if specified
        if self.data_types is not None:
            query = query.filter(DataChunk.data_type.in_(self.data_types))

        self.data_chunk_ids = query.all()
        print("query done.")
        self.total_chunks = len(self.data_chunk_ids)
        print(f"total chunks: {self.total_chunks}   ")

    def __len__(self):
        return self.total_chunks

    def _fetch_next_batch(self):
        print("Fetching next batch")
        start_idx = self.buffer_index
        end_idx = min(start_idx + self.batch_size, self.total_chunks)

        batch_ids = [id_[0] for id_ in self.data_chunk_ids[start_idx:end_idx]]
        self.buffer = (
            self.session.query(DataChunk).filter(DataChunk.id.in_(batch_ids)).all()
        )

        self.buffer_index += self.batch_size
        print("Done fetching next batch")

    def __getitem__(self, idx):
        # If buffer is empty or index out of range, fetch the next batch
        if not self.buffer or idx >= self.buffer_index:
            self._fetch_next_batch()

        # Get the data chunk from the buffer
        data_chunk = self.buffer[idx % self.batch_size]

        sample_data = {
            "data": data_chunk.data,
            "seizure_state": data_chunk.seizure_state,
            "data_type": data_chunk.data_type,
        }

        if self.transform:
            sample_data = self.transform(sample_data)

        return sample_data


def train_torch_seizure_model(
    session: Session, seizure_states=[0, 2], data_types=None, batch_size=128, epochs=10
):
    # Create the seizure dataset
    seizure_dataset = SeizureDataset(
        session, 81802, seizure_states=seizure_states, data_types=data_types
    )
    data_loader = DataLoader(seizure_dataset, batch_size=batch_size, shuffle=True)

    # Define a simple LSTM model
    # class SeizureClassifier(nn.Module):
    #     def __init__(self, input_dim, hidden_dim):
    #         super(SeizureClassifier, self).__init__()
    #         self.embedding = nn.Embedding(input_dim, 16)
    #         self.lstm = nn.LSTM(16, hidden_dim, batch_first=True)
    #         self.fc = nn.Linear(hidden_dim, 1)
    #         self.sigmoid = nn.Sigmoid()

    #     def forward(self, x):
    #         x = self.embedding(x)
    #         x, _ = self.lstm(x)
    #         x = self.fc(x[:, -1, :])
    #         x = self.sigmoid(x)
    #         return x

    # # Assuming data is represented by integers in the range [0, 255]
    # model = SeizureClassifier(input_dim=256, hidden_dim=32)
    # model.to(DEVICE)

    # # Loss and optimizer
    # criterion = nn.BCELoss()
    # optimizer = torch.optim.Adam(model.parameters())

    # Training loop
    for epoch in range(epochs):
        print(f"epoch {epoch}")
        i = 0
        for batch_data in data_loader:
            i += 1
            if i % 100 == 0:
                print(f"batch {i}")
            # data = torch.tensor(batch_data["data"], dtype=torch.long).to(DEVICE)
            # target = (
            #     batch_data["seizure_state"]
            #     .clone()
            #     .detach()
            #     .view(-1, 1)
            #     .float()
            #     .to(DEVICE)
            # )

            # Forward pass
            # outputs = model(data)
            # loss = criterion(outputs, target)

            # # Backward pass and optimization
            # optimizer.zero_grad()
            # loss.backward()
            # optimizer.step()

        print(f"Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}")

    return model


if __name__ == "__main__":
    # Create a database engine
    engine = create_engine(ENGINE_STR)

    # Create a session
    Session = sessionmaker(bind=engine)
    with Session() as session:
        # Datatypes:
        # 0: ieeg
        # 1: ecg
        # 2: ekg
        # 3: surface eeg

        # Train a seizure model
        model = train_torch_seizure_model(session, epochs=1, data_types=[1])
