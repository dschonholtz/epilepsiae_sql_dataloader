"""
We are going to dummy up and end to end pipeline to test the binary_to_sql pipeline.

seizurelist, .head files and corresponding .data files.

We then are going to use the MetaDataBuilder to create the metadata and then use the BinaryToSql to push the data to the database.

We are going to have three binary files.
1. A file with all non-seiz data.
2. A file where halfway through the data would qualify as pre-seiz
3. A file where there is a recording gap after the second file, then more pre-seiz data, then seizure data. This recording will also be shorter.

The binary will be organized such that a value of 0 will be used to represent non-seiz data, 
1 will be used to represent pre-seiz data, and 2 will be used to represent seizure data.

We will then check that the metadata split correctly identifies and splits the data into the correct categories.

On top of that, we need to split the binary data into chunks of 1 second each.

We then should end with a variety of queries to verify that the data was pushed correctly.

The split should be such that there is a single second sample that has both non-seiz and pre-seiz in it and that sample should be dropped
There also should be a sample that has seiz and non-seiz in it. That also should just be dropped entirely.
"""
import pytest
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta
from shutil import rmtree
from epilepsiae_sql_dataloader.RelationalRigging.MetaDataBuilder import MetaDataBuilder
from epilepsiae_sql_dataloader.RelationalRigging.PushBinaryToSql import BinaryToSql
from tests.utils import ENGINE_STR
from epilepsiae_sql_dataloader.models.Base import Base
from epilepsiae_sql_dataloader.models.Seizures import Seizure
from epilepsiae_sql_dataloader.models.LoaderTables import (
    DataChunk,
    object_as_dict,
    dict_with_attrs,
)
from sqlalchemy import create_engine
from epilepsiae_sql_dataloader.utils import session_scope

# Constants for different types of data
NON_SEIZURE_ECG = 0
PRE_SEIZURE_ECG = 1
SEIZURE_ECG = 2
NON_SEIZURE_IEEG = 3
PRE_SEIZURE_IEEG = 4
SEIZURE_IEEG = 5
NON_SEIZURE_EEG = 6
PRE_SEIZURE_EEG = 7
SEIZURE_EEG = 8

# ./test_data
test_data_path = Path(__file__).parent / "test_data"


# fixture for creating fake test data
@pytest.fixture(scope="function")
def create_test_data():
    # Create the test data
    try:
        _test_data_path = test_data_path / "binary_to_sql" / "inv"
        create_patient_data(_test_data_path)
        # Yield the patient path
        yield _test_data_path
    finally:
        # After the test, delete the test files
        rmtree(test_data_path / "binary_to_sql")
        # pass


def write_data_file(file_path, data):
    # Write the data to the .data file as uint16
    data.astype(np.uint16).tofile(file_path)


def write_seizurelist_file(file_path, onsets, offsets, onset_samples, offset_samples):
    # Generate the content for the seizurelist file
    content = "\n"
    for onset, offset, onset_sample, offset_sample in zip(
        onsets, offsets, onset_samples, offset_samples
    ):
        content += f"""{onset}\t{offset}\t{onset_sample}\t{offset_sample}\n"""
    # Write the content to the seizurelist file
    with open(file_path, "w") as f:
        f.write(content)


def write_head_file(
    file_path,
    start_time,
    num_samples,
    sample_freq,
    num_channels,
    electrode_names,
    pat_id,
    adm_id,
    rec_id,
    duration_in_sec,
):
    # Generate the content for the .head file
    content = f"""start_ts={start_time.strftime('%Y-%m-%d %H:%M:%S.%f')}
num_samples={num_samples}
sample_freq={sample_freq}
conversion_factor=0.179000
num_channels={num_channels}
elec_names={electrode_names}
pat_id={pat_id}
adm_id={adm_id}
rec_id={rec_id}
duration_in_sec={duration_in_sec}
sample_bytes=2
"""
    # Write the content to the .head file
    with open(file_path, "w") as f:
        f.write(content)


DATA_TYPES = {
    "ECG": {
        "NON_SEIZURE": NON_SEIZURE_ECG,
        "PRE_SEIZURE": PRE_SEIZURE_ECG,
        "SEIZURE": SEIZURE_ECG,
    },
    "EEG": {
        "NON_SEIZURE": NON_SEIZURE_EEG,
        "PRE_SEIZURE": PRE_SEIZURE_EEG,
        "SEIZURE": SEIZURE_EEG,
    },
    "IEEG": {
        "NON_SEIZURE": NON_SEIZURE_IEEG,
        "PRE_SEIZURE": PRE_SEIZURE_IEEG,
        "SEIZURE": SEIZURE_IEEG,
    },
}

DEFAULT_ELECTRODES = [
    "GA1",
    "GA2",
    "GA3",
    "GA4",
    "GA5",
    "GA6",
    "GA7",
    "GA8",
    "GB1",
    "GB2",
    "GB3",
    "GB4",
    "GB5",
    "GB6",
    "GB7",
    "GB8",
    "GC1",
    "GC2",
    "GC3",
    "GC4",
    "GC5",
    "GC6",
    "GC7",
    "GC8",
    "GD1",
    "GD2",
    "GD3",
    "GD4",
    "GD5",
    "GD6",
    "GD7",
    "GD8",
    "GE1",
    "GE2",
    "GE3",
    "GE4",
    "GE5",
    "GE6",
    "GE7",
    "GE8",
    "GF1",
    "GF2",
    "GF3",
    "GF4",
    "GF5",
    "GF6",
    "GF7",
    "GF8",
    "GG1",
    "GG2",
    "GG3",
    "GG4",
    "GG5",
    "GG6",
    "GG7",
    "GG8",
    "GH1",
    "GH2",
    "GH3",
    "GH4",
    "GH5",
    "GH6",
    "GH7",
    "GH8",
    "M1",
    "M2",
    "M3",
    "M4",
    "M5",
    "M6",
    "M7",
    "M8",
    "IHA1",
    "IHA2",
    "IHA3",
    "IHA4",
    "IHB1",
    "IHB2",
    "IHB3",
    "IHB4",
    "IHC1",
    "IHC2",
    "IHC3",
    "IHC4",
    "IHD1",
    "IHD2",
    "IHD3",
    "IHD4",
    "FL1",
    "FL2",
    "N",  # surface electrode eeg
    "FP",  # surface electrode eeg
    "ECG",  # ECG
]


def get_electrode_type(electrode) -> int:
    # this only matches the inv dataset.
    if electrode in {"ECG", "EKG"}:
        return electrode
    elif electrode in {
        "N",
        "FP",
        "AF",
        "F",
        "FT",
        "FC",
        "A",
        "T",
        "C",
        "TP",
        "CP",
        "P",
        "PO",
        "O",
        "I",
        "EMG",
        "EOG",
        "PHO",
    }:
        return "EEG"
    else:
        return "IEEG"


def create_patient_data(_test_data_path: Path):
    """
    test_data/
        binary_to_sqlELECTRODE_TYPES/
            inv/
                pat_1/
                    seizurelist
                    adm_1/
                        rec_1/
                            1.head
                            1.data # all non-seizure
                            2.head
                            2.data # 35 minutes non-seizure, 25 minutes pre-seizure, 5 minute gap between this and next recording
                        rec_2/
                            3.head
                            3.data # 30 minutes pre-seizure, 5 minutes seizure, 15 minutes non-seizure, 10 minutes pre-seizure
    .data files are uint16 binary files which can be read into numpy arrays of size length x channels
    .head files are text files with the following format:

    ```1.head
    start_ts=2008-11-03 20:34:03.000
    num_samples=3686400
    sample_freq=1024
    conversion_factor=0.179000
    num_channels=93
    elec_names=[]
    pat_id=1
    adm_id=1
    rec_id=1
    duration_in_sec=3600
    sample_bytes=2
    ```

    """
    # if the data is already there, remove it
    if _test_data_path.exists():
        rmtree(_test_data_path)
    # Ensure the test_data directory exists
    _test_data_path.mkdir(parents=True, exist_ok=True)

    # Set the start time for the first file
    initial_start_time = datetime(2008, 11, 3, 20, 34, 3)
    start_time = initial_start_time
    sample_freq1 = 1024
    sample_freq2 = 1024
    sample_freq3 = 512
    one_hour = 3600
    five_min = 60 * 5
    # Create the data and .head files for each recording
    for i in range(1, 3):
        rec_dir = _test_data_path / f"pat_1/adm_1/rec_{i}"
        rec_dir.mkdir(parents=True, exist_ok=True)

        if i == 1:
            data1 = []
            data2_non = []
            data2_pre = []
            for electrode in DEFAULT_ELECTRODES:
                electrode_type = get_electrode_type(electrode)
                data1.append(
                    np.full(
                        (sample_freq1 * one_hour, 1),
                        DATA_TYPES[electrode_type]["NON_SEIZURE"],
                    )
                )
                data2_non.append(
                    np.full(
                        (sample_freq2 * one_hour // 2 + five_min, 1),
                        DATA_TYPES[electrode_type]["NON_SEIZURE"],
                    )
                )
                data2_pre.append(
                    np.full(
                        (sample_freq2 * one_hour // 2 - five_min * 2, 1),
                        DATA_TYPES[electrode_type]["PRE_SEIZURE"],
                    )
                )
            data1 = np.concatenate(data1, axis=1)
            data2_non = np.concatenate(data2_non, axis=1)
            data2_pre = np.concatenate(data2_pre, axis=1)
            data2 = np.concatenate((data2_non, data2_pre), axis=0)
            write_head_file(
                rec_dir / "1.head",
                start_time,
                data1.shape[0],
                sample_freq1,
                data1.shape[1],
                DEFAULT_ELECTRODES,
                1,
                1,
                i,
                data1.shape[0] // sample_freq1,
            )
            write_data_file(rec_dir / "1.data", data1)
            start_time = initial_start_time + timedelta(
                seconds=data1.shape[0] // sample_freq1
            )

            write_head_file(
                rec_dir / "2.head",
                start_time,
                data2.shape[0],
                sample_freq2,
                data2.shape[1],
                DEFAULT_ELECTRODES,
                1,
                1,
                i,
                data2.shape[0] // sample_freq2,
            )
            write_data_file(rec_dir / "2.data", data2)

            # five minute gap between rec 1 and 2
            start_time += timedelta(seconds=data2.shape[0] // sample_freq2 + five_min)

        elif i == 2:
            data3_pre = []
            data3_seiz = []
            data3_non = []
            data3_pre2 = []
            for electrode in DEFAULT_ELECTRODES:
                electrode_type = get_electrode_type(electrode)
                data3_pre.append(
                    np.full(
                        (sample_freq3 * one_hour // 2, 1),
                        DATA_TYPES[electrode_type]["PRE_SEIZURE"],
                    )
                )
                data3_seiz.append(
                    np.full(
                        (sample_freq3 * five_min, 1),
                        DATA_TYPES[electrode_type]["SEIZURE"],
                    )
                )
                data3_non.append(
                    np.full(
                        (sample_freq3 * 15 * 60, 1),
                        DATA_TYPES[electrode_type]["NON_SEIZURE"],
                    )
                )
                data3_pre2.append(
                    np.full(
                        (sample_freq3 * five_min * 2, 1),
                        DATA_TYPES[electrode_type]["PRE_SEIZURE"],
                    )
                )
            data3_pre = np.concatenate(data3_pre, axis=1)
            data3_seiz = np.concatenate(data3_seiz, axis=1)
            data3_non = np.concatenate(data3_non, axis=1)
            data3_pre2 = np.concatenate(data3_pre2, axis=1)
            data3 = np.concatenate(
                (data3_pre, data3_seiz, data3_non, data3_pre2), axis=0
            )

            write_head_file(
                rec_dir / "3.head",
                start_time,
                data3.shape[0],
                sample_freq3,
                data3.shape[1],
                DEFAULT_ELECTRODES,
                1,
                1,
                i,
                data3.shape[0] // sample_freq3,
            )
            write_data_file(rec_dir / "3.data", data3)

    # Create a seizurelist file for the seizure in the second recording
    seizurelist_file = _test_data_path / "pat_1/seizurelist"
    # first seizure is 5 minutes long and starts 30 minutes into the last recording
    # there also is a five minute gap between sample 2 and 3
    onset1 = initial_start_time + timedelta(seconds=3600 * 2 + 30 * 60 + 5 * 60)
    offset1 = onset1 + timedelta(seconds=5 * 60)
    onset_sample1 = sample_freq1 * 3600 + sample_freq2 * 3600 + 30 * 60 * sample_freq3
    offset_sample1 = onset_sample1 + 5 * 60 * sample_freq3

    # second seizure starts 50 minutes after the end of the last recording
    onset2 = initial_start_time + timedelta(seconds=3600 * 3 + 5 * 60 + 50 * 60)
    # length of this seizure is inconsequential
    offset2 = onset2 + timedelta(seconds=5 * 60)
    # past end of final sample
    onset_sample2 = (
        sample_freq1 * 3600 + sample_freq2 * 3600 + 3600 * sample_freq3 + 100
    )
    offset_sample2 = onset_sample2 + 5 * 60 * sample_freq3

    write_seizurelist_file(
        seizurelist_file,
        [onset1, onset2],
        [offset1, offset2],
        [onset_sample1, onset_sample2],
        [offset_sample1, offset_sample2],
    )


def test_write_head_file(tmp_path):
    file_path = tmp_path / "test.head"
    start_time = datetime(2008, 11, 3, 20, 34, 3)
    num_samples = 1024 * 1800
    sample_freq = 1024
    num_channels = 93
    pat_id = 1
    adm_id = 1
    rec_id = 1
    duration_in_sec = num_samples // sample_freq

    write_head_file(
        file_path,
        start_time,
        num_samples,
        sample_freq,
        num_channels,
        DEFAULT_ELECTRODES,
        pat_id,
        adm_id,
        rec_id,
        duration_in_sec,
    )

    with open(file_path, "r") as f:
        lines = f.read().split("\n")
        assert lines[0] == f"start_ts={start_time.strftime('%Y-%m-%d %H:%M:%S.%f')}"
        assert lines[1] == f"num_samples={num_samples}"
        assert lines[2] == f"sample_freq={sample_freq}"
        assert lines[4] == f"num_channels={num_channels}"
        assert lines[6] == f"pat_id={pat_id}"
        assert lines[7] == f"adm_id={adm_id}"
        assert lines[8] == f"rec_id={rec_id}"
        assert lines[9] == f"duration_in_sec={duration_in_sec}"


def test_write_data_file(tmp_path):
    file_path = tmp_path / "test.data"
    data = np.full((1024 * 1800, 93), NON_SEIZURE_ECG)

    write_data_file(file_path, data)

    assert np.array_equal(np.fromfile(file_path, dtype=np.uint16), data.flatten())


def test_write_seizurelist_file(tmp_path):
    file_path = tmp_path / "seizurelist"
    onset = datetime(2008, 11, 3, 21, 34, 3)
    offset = datetime(2008, 11, 3, 21, 34, 13)
    onset_sample = 1024 * 3600
    offset_sample = 1024 * 3600 + 1024 * 10

    write_seizurelist_file(
        file_path, [onset], [offset], [onset_sample], [offset_sample]
    )

    with open(file_path, "r") as f:
        lines = f.read().strip().split("\n")
        assert lines[0] == f"{onset}\t{offset}\t{onset_sample}\t{offset_sample}"


# Generated by CodiumAI

import pytest


class TestGetSeizureState:
    # Tests that the method returns 2 when seizure onset is exactly pre_seizure_time seconds before chunk end timestamp
    def test_seizure_onset_pre_seizure_time(self):
        builder = BinaryToSql(engine_str=ENGINE_STR)
        seizures = [
            Seizure(
                onset=datetime(2022, 1, 1, 0, 59, 0),
                offset=datetime(2022, 1, 1, 1, 0, 10),
            )
        ]
        chunk_start_ts = datetime(2022, 1, 1, 0, 0, 0)
        chunk_end_ts = datetime(2022, 1, 1, 0, 0, 0)
        assert (
            builder.get_seizure_state(
                seizures, chunk_start_ts, chunk_end_ts, pre_seizure_time=3600
            )
            == 2
        )

    # Tests that the method returns 0 when seizure onset and offset are outside chunk start and end timestamps
    def test_seizure_outside_chunk(self):
        builder = BinaryToSql(engine_str=ENGINE_STR)
        seizures = [
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 10),
                offset=datetime(2022, 1, 1, 0, 0, 20),
            )
        ]
        chunk_start_ts = datetime(2022, 1, 1, 0, 0, 0)
        chunk_end_ts = datetime(2022, 1, 1, 0, 0, 5)
        assert builder.get_seizure_state(seizures, chunk_start_ts, chunk_end_ts) == 2

    # Tests that the method correctly identifies a seizure during the chunk
    def test_seizure_during_chunk(self):
        builder = BinaryToSql(engine_str=ENGINE_STR)
        seizures = [
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 0),
                offset=datetime(2022, 1, 1, 0, 0, 10),
            ),
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 20),
                offset=datetime(2022, 1, 1, 0, 0, 30),
            ),
        ]
        chunk_start_ts = datetime(2022, 1, 1, 0, 0, 5)
        chunk_end_ts = datetime(2022, 1, 1, 0, 0, 15)
        assert builder.get_seizure_state(seizures, chunk_start_ts, chunk_end_ts) == 1

    # Tests that the method correctly identifies a seizure that starts at the beginning of the chunk
    def test_seizure_starts_at_chunk_start(self):
        builder = BinaryToSql(engine_str=ENGINE_STR)
        seizures = [
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 0),
                offset=datetime(2022, 1, 1, 0, 0, 10),
            ),
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 20),
                offset=datetime(2022, 1, 1, 0, 0, 30),
            ),
        ]
        chunk_start_ts = datetime(2022, 1, 1, 0, 0, 0)
        chunk_end_ts = datetime(2022, 1, 1, 0, 0, 5)
        assert builder.get_seizure_state(seizures, chunk_start_ts, chunk_end_ts) == 1

    # Tests that the method correctly identifies a seizure that ends at the end of the chunk
    def test_seizure_ends_at_chunk_end(self):
        builder = BinaryToSql(engine_str=ENGINE_STR)
        seizures = [
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 0),
                offset=datetime(2022, 1, 1, 0, 0, 10),
            ),
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 20),
                offset=datetime(2022, 1, 1, 0, 0, 30),
            ),
        ]
        chunk_start_ts = datetime(2022, 1, 1, 0, 0, 25)
        chunk_end_ts = datetime(2022, 1, 1, 0, 0, 30)
        assert builder.get_seizure_state(seizures, chunk_start_ts, chunk_end_ts) == 1

    # Tests that the method correctly identifies a seizure that starts before the end of the chunk
    def test_seizure_starts_before_chunk_end(self):
        builder = BinaryToSql(engine_str=ENGINE_STR)
        seizures = [
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 0),
                offset=datetime(2022, 1, 1, 0, 0, 10),
            ),
            Seizure(
                onset=datetime(2022, 1, 1, 0, 0, 20),
                offset=datetime(2022, 1, 1, 0, 0, 30),
            ),
        ]
        chunk_start_ts = datetime(2022, 1, 1, 0, 0, 15)
        chunk_end_ts = datetime(2022, 1, 1, 0, 0, 25)
        assert builder.get_seizure_state(seizures, chunk_start_ts, chunk_end_ts) == 1


#################################################3
# Tests below here test the binary_to_sql pipeline using the above fixture
#################################################3


@pytest.fixture(scope="function")
def metadata_tables(create_test_data):
    # setup
    engine = create_engine(ENGINE_STR)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    builder = MetaDataBuilder(engine_str=ENGINE_STR)
    builder.start([create_test_data])

    yield None

    # teardown
    Base.metadata.drop_all(engine)


def test_e2e(metadata_tables):
    """
    This checks if we get the binary in the right splits given the test data

    """
    # 2 surface EEG channels
    # 1 ECG channel
    # 90 IEEG channels
    # 3 hours of data
    # 1 hour of non-seiz
    # 35 minutes of non-seiz
    # 25 minutes of pre-seiz
    # 5 minute gap
    # 30 minutes of pre-seiz
    # 5 minutes of seiz
    # 15 minutes of non-seiz
    # 10 minutes of pre-seiz

    # binary_to_sql = BinaryToSql(ENGINE_STR)
    # binary_to_sql.load_patient(1)
    # Correct # of seizure chunks: 5 * 60 * 93
    # Correct # Pre-Seiz chunks: 55 * 60 * 93
    # correct # non-seiz chunks: 65 * 60 * 93
    # correct # of chunks: 3 * 60 * 93

    # correct # pre-seiz ecg chunks: 55 * 60
    # correct # non-seiz ecg chunks: 65 * 60
    # correct # seiz ecg chunks: 5 * 60

    # correct # pre-seiz ieeg chunks: 55 * 60 * 90
    # correct # non-seiz ieeg chunks: 65 * 60 * 90
    # correct # seiz ieeg chunks:   5 * 60 * 90

    # correct # pre-seiz eeeg chunks: 55 * 60 * 2
    # correct # non-seiz eeeg chunks:   65 * 60 * 2
    # correct # seiz eeeg chunks:  5 * 60 * 2

    # query all of the datachunks that are pre-seiz and ECG

    # Define the expected number of chunks for each data type and seizure state
    print("starting e2e test")
    binary_inserter = BinaryToSql(ENGINE_STR)
    binary_inserter.load_patient(1)
    expected_counts = {
        NON_SEIZURE_ECG: (60 + 35 + 15) * 60,
        PRE_SEIZURE_ECG: 65 * 60,
        SEIZURE_ECG: 5 * 60,
        NON_SEIZURE_IEEG: (60 + 35 + 15) * 60 * 90,
        PRE_SEIZURE_IEEG: 65 * 60 * 90,
        SEIZURE_IEEG: 5 * 60 * 90,
        NON_SEIZURE_EEG: (60 + 35 + 15) * 60 * 2,
        PRE_SEIZURE_EEG: 65 * 60 * 2,
        SEIZURE_EEG: 5 * 60 * 2,
    }

    # Create a dictionary to map seizure_state and data_type to binary values
    binary_values = {
        (0, 1): NON_SEIZURE_ECG,
        (2, 1): SEIZURE_ECG,
        (1, 1): PRE_SEIZURE_ECG,
        (0, 0): NON_SEIZURE_IEEG,
        (2, 0): SEIZURE_IEEG,
        (1, 0): PRE_SEIZURE_IEEG,
        (0, 2): NON_SEIZURE_EEG,
        (2, 2): SEIZURE_EEG,
        (1, 2): PRE_SEIZURE_EEG,
    }
    counts = {}

    # Check if the actual counts match the expected counts
    with session_scope(ENGINE_STR) as session:
        for data_type, expected_count in expected_counts.items():
            seizure_state = data_type // 3  # Get the seizure_state from the data_type
            actual_chunks = (
                session.query(DataChunk)
                .filter(
                    DataChunk.seizure_state == seizure_state,
                    DataChunk.data_type == data_type % 3,
                )
                .all()
            )
            print_data_seizure_info(data_type, seizure_state)
            print("actual_chunks", len(actual_chunks))

            counts[(seizure_state, data_type)] = len(actual_chunks)

    for count_key, count_value in counts.items():
        print(count_key, count_value)
        print_data_seizure_info(count_key[1], count_key[0])
        assert (
            count_value == expected_count
        ), f"Data type {data_type} has {count_value} chunks, expected {expected_count}."

        # Check if the binary data is correct
        # expected_binary_value = binary_values[(seizure_state, data_type % 3)]
        # for chunk in actual_chunks:
        #     binary_data = chunk.data
        #     assert all(
        #         value == expected_binary_value for value in binary_data
        #     ), f"Incorrect binary data for chunk id {chunk.id}"


def print_data_seizure_info(data_type: int, seizure_state: int) -> None:
    print(f"actual datatype: {data_type}, actual seizure state: {seizure_state}")
    data_type = data_type % 3
    if data_type == 0:
        print("DataType for IEEG")
    elif data_type == 1:
        print("DataType for ECG")
    elif data_type == 2:
        print("DataType for EKG")
    elif data_type == 3:
        print("DataType for EEG")

    if seizure_state == 0:
        print("Seizure State for non-seizure")
    elif seizure_state == 1:
        print("Seizure State for seizure")
    elif seizure_state == 2:
        print("Seizure State for pre-seizure")
