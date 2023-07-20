"""
This is a CLI tool that allows you to load data from the https://epilepsiae.uniklinik-freiburg.de/ 
dataset into a SQL database.
It is pointed at a database that has already been configured with the tables from 
epilepsiae_sql_dataloader/models/LoaderTables.py
Then it is pointed at a directory with .head and .data files along
"""

from epilepsiae_sql_dataloader.utils import session_scope
from epilepsiae_sql_dataloader.models.LoaderTables import (
    Patient,
    Dataset,
    SeizureState,
    DataChunk,
)

from epilepsiae_sql_dataloader.models.Sample import Sample
from epilepsiae_sql_dataloader.models.Seizures import Seizure


class MetaDataBuilder:
    def __init__(self, engine_str):
        """
        Initializes a new instance of the MetaDataBuilder class.

        Args:
        engine_str (str): A string representing the SQLAlchemy engine connection string.
        """
        self.engine_str = engine_str

    def get_seizures(self):
        """
        Retrieves all seizures from the 'seizures' table in the database.

        Returns:
        list[Seizure]: A list of all Seizure instances in the database.
        """
        with session_scope(self.engine_str) as session:
            return session.query(Seizure).all()

    def populate_patients_table(self, patient_ids, patient_infos):
        """
        Populates the 'patients' table with the given data.

        Args:
        patient_ids (list[int]): A list of patient IDs to add.
        patient_infos (list[str]): A list of the corresponding patient information to add.
        """
        with session_scope(self.engine_str) as session:
            for patient_id, patient_info in zip(patient_ids, patient_infos):
                # Check if a patient with the given ID already exists
                patient = session.query(Patient).filter_by(id=patient_id).first()
                if patient is not None:
                    # If the patient exists, update their info
                    patient.info = patient_info
                else:
                    # If the patient does not exist, create a new Patient instance
                    patient = Patient(id=patient_id, info=patient_info)
                    session.add(patient)

    def populate_datasets_table(self, dataset_ids, dataset_names):
        """
        Populates the 'datasets' table with the given data.

        Args:
        dataset_ids (list[int]): A list of dataset IDs to add.
        dataset_names (list[str]): A list of the corresponding dataset names to add.
        """
        with session_scope(self.engine_str) as session:
            for dataset_id, dataset_name in zip(dataset_ids, dataset_names):
                # Check if a dataset with the given ID already exists
                dataset = session.query(Dataset).filter_by(id=dataset_id).first()
                if dataset is not None:
                    # If the dataset exists, update its name
                    dataset.name = dataset_name
                else:
                    # If the dataset does not exist, create a new Dataset instance
                    dataset = Dataset(id=dataset_id, name=dataset_name)
                    session.add(dataset)

    def populate_seizure_states_table(self, state_ids, state_names):
        """
        Populates the 'seizure_states' table with the given data.

        Args:
        state_ids (list[int]): A list of seizure state IDs to add.
        state_names (list[str]): A list of the corresponding seizure state names to add.
        """
        with session_scope(self.engine_str) as session:
            for state_id, state_name in zip(state_ids, state_names):
                # Check if a seizure state with the given ID already exists
                seizure_state = (
                    session.query(SeizureState).filter_by(id=state_id).first()
                )
                if seizure_state is not None:
                    # If the seizure state exists, update its state
                    seizure_state.state = state_name
                else:
                    # If the seizure state does not exist, create a new SeizureState instance
                    seizure_state = SeizureState(id=state_id, state=state_name)
                    session.add(seizure_state)

    def populate_data_chunks_table(
        self, chunk_ids, patient_ids, dataset_ids, state_ids, chunk_data
    ):
        """
        Populates the 'data_chunks' table with the given data.

        Args:
        chunk_ids (list[int]): A list of data chunk IDs to add.
        patient_ids (list[int]): A list of the corresponding patient IDs.
        dataset_ids (list[int]): A list of the corresponding dataset IDs.
        state_ids (list[int]): A list of the corresponding seizure state IDs.
        chunk_data (list[bytes]): A list of the corresponding data chunks.
        """
        with session_scope(self.engine_str) as session:
            for chunk_id, patient_id, dataset_id, state_id, data in zip(
                chunk_ids, patient_ids, dataset_ids, state_ids, chunk_data
            ):
                # Check if a data chunk with the given ID already exists
                data_chunk = session.query(DataChunk).filter_by(id=chunk_id).first()
                if data_chunk is not None:
                    # If the data chunk exists, update its fields
                    data_chunk.patient_id = patient_id
                    data_chunk.dataset_id = dataset_id
                    data_chunk.state_id = state_id
                    data_chunk.data = data
                else:
                    # If the data chunk does not exist, create a new DataChunk instance
                    data_chunk = DataChunk(
                        id=chunk_id,
                        patient_id=patient_id,
                        dataset_id=dataset_id,
                        state_id=state_id,
                        data=data,
                    )
                    session.add(data_chunk)

    def process_samples(self):
        """
        Processes the 'samples' table and populates the 'data_chunks' table based on its data.
        """
        # Retrieve all samples
        samples = self.get_samples()
        for sample in samples:
            # Break each sample into one-second chunks
            chunks = self.break_into_chunks(sample.data, sample.sample_freq)
            # Determine the corresponding patient, dataset, and seizure state for each chunk
            patient_id = sample.pat_id
            dataset_id = (
                self.get_dataset_id()  # Assumes that we have a method to get the dataset_id
            )
            state_id = self.determine_state_id(
                sample
            )  # Our helper function to get the state_id
            # Add the chunks to the 'data_chunks' table
            self.populate_data_chunks_table(
                chunk_ids=range(sample.id * 1000, sample.id * 1000 + len(chunks)),
                patient_ids=[patient_id] * len(chunks),
                dataset_ids=[dataset_id] * len(chunks),
                state_ids=[state_id] * len(chunks),
                chunk_data=chunks,
            )

    def process_seizures(self):
        """
        Processes the 'seizures' table and updates the 'data_chunks' table based on its data.
        """
        # Retrieve all seizures
        seizures = self.get_seizures()
        for seizure in seizures:
            # Find the corresponding chunks in the 'data_chunks' table
            chunk_ids = self.find_corresponding_chunks(seizure)
            # Update the seizure state of those chunks to 'seizure'
            with session_scope(self.engine_str) as session:
                chunks = (
                    session.query(DataChunk).filter(DataChunk.id.in_(chunk_ids)).all()
                )
                for chunk in chunks:
                    chunk.state_id = self.get_seizure_state_id(
                        "seizure"
                    )  # Use a method to get the state_id for 'seizure'

    def break_into_chunks(self, data, sample_freq):
        """
        Breaks the given data into one-second chunks based on the sample frequency.

        Args:
        data (list[int]): The data to be broken into chunks.
        sample_freq (int): The sample frequency, i.e., the number of data points per second.

        Returns:
        list[list[int]]: The data broken into one-second chunks.
        """
        # Determine the number of chunks
        num_chunks = len(data) // sample_freq

        # Break the data into chunks
        chunks = [
            data[i * sample_freq : (i + 1) * sample_freq] for i in range(num_chunks)
        ]

        return chunks

    def get_dataset_id(self, dataset_name):
        """
        Retrieves the ID for the given dataset name.

        Args:
        dataset_name (str): The name of the dataset.

        Returns:
        int: The ID of the dataset.
        """
        with session_scope(self.engine_str) as session:
            dataset = session.query(Dataset).filter(Dataset.name == dataset_name).one()
            return dataset.id

    def get_seizure_state_id(self, seizure_state):
        """
        Retrieves the ID for the given seizure state.

        Args:
        seizure_state (str): The seizure state.

        Returns:
        int: The ID of the seizure state.
        """
        with session_scope(self.engine_str) as session:
            state = (
                session.query(SeizureState)
                .filter(SeizureState.state == seizure_state)
                .one()
            )
            return state.id
