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
from tests.utils import ENGINE_STR
from epilepsiae_sql_dataloader.models.Base import Base
from sqlalchemy import create_engine

# Constants for different types of data
NON_SEIZURE = 0
PRE_SEIZURE = 1
SEIZURE = 2

# ./test_data
test_data_path = Path(__file__).parent / "test_data"


# fixture for creating fake test data
@pytest.fixture(scope="function")
def create_test_data():
    """
    test_data/
        binary_to_sql/
            pat_1/
                seizurelist
                adm_1/
                    rec_1/
                        1.head
                        1.data
                        2.head
                        2.data
                    rec_2/
                        3.head
                        3.data
    .data files are uint16 binary files which can be read into numpy arrays of size channels x length
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
    # Create the test data
    try:
        create_patient_data()
        # Yield the patient path
        yield test_data_path / "pat_1"
    finally:
        # After the test, delete the test files
        # rmtree(test_data_path)
        pass


def write_data_file(file_path, data):
    # Write the data to the .data file as uint16
    data.astype(np.uint16).tofile(file_path)


def write_seizurelist_file(file_path, onset, offset, onset_sample, offset_sample):
    # Generate the content for the seizurelist file
    content = f"""{onset}\t{offset}\t{onset_sample}\t{offset_sample}
"""
    # Write the content to the seizurelist file
    with open(file_path, "w") as f:
        f.write(content)


def write_head_file(
    file_path,
    start_time,
    num_samples,
    sample_freq,
    num_channels,
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
elec_names=[]
pat_id={pat_id}
adm_id={adm_id}
rec_id={rec_id}
duration_in_sec={duration_in_sec}
sample_bytes=2
"""
    # Write the content to the .head file
    with open(file_path, "w") as f:
        f.write(content)


def create_patient_data():
    # Ensure the test_data directory exists
    test_data_path.mkdir(parents=True, exist_ok=True)

    # Set the start time for the first file
    start_time = datetime(2008, 11, 3, 20, 34, 3)

    # Create the data and .head files for each recording
    for i in range(1, 3):
        rec_dir = test_data_path / f"pat_1/adm_1/rec_{i}"
        rec_dir.mkdir(parents=True, exist_ok=True)

        if i == 1:
            # All non-seizure data and half pre-seizure
            data1 = np.full((93, 1024 * 1800), NON_SEIZURE)
            data2 = np.full((93, 1024 * 1800), PRE_SEIZURE)
            data = np.concatenate((data1, data2), axis=1)

            write_head_file(
                rec_dir / "1.head",
                start_time,
                data1.shape[1],
                1024,
                data1.shape[0],
                1,
                1,
                i,
                data1.shape[1] // 1024,
            )
            write_data_file(rec_dir / "1.data", data1)

            start_time += timedelta(seconds=data1.shape[1] // 1024)

            write_head_file(
                rec_dir / "2.head",
                start_time,
                data2.shape[1],
                1024,
                data2.shape[0],
                1,
                1,
                i,
                data2.shape[1] // 1024,
            )
            write_data_file(rec_dir / "2.data", data2)

            start_time += timedelta(seconds=data2.shape[1] // 1024)

        elif i == 2:
            # Pre-seizure and seizure data with a gap in between
            data1 = np.full((93, 512 * 900), PRE_SEIZURE)
            data2 = np.full((93, 512 * 900), SEIZURE)
            data = np.concatenate((data1, data2), axis=1)

            write_head_file(
                rec_dir / "3.head",
                start_time,
                data1.shape[1],
                512,
                data1.shape[0],
                1,
                1,
                i,
                data1.shape[1] // 512,
            )
            write_data_file(rec_dir / "3.data", data1)

            start_time += timedelta(seconds=data1.shape[1] // 512)

            # Create a seizurelist file for the seizure in the second recording
            seizurelist_file = test_data_path / "pat_1/seizurelist"
            onset = start_time - timedelta(seconds=data2.shape[1] // 512)
            offset = start_time
            onset_sample = data1.shape[1]
            offset_sample = data1.shape[1] + data2.shape[1]
            write_seizurelist_file(
                seizurelist_file, onset, offset, onset_sample, offset_sample
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
    data = np.full((93, 1024 * 1800), NON_SEIZURE)

    write_data_file(file_path, data)

    assert np.array_equal(np.fromfile(file_path, dtype=np.uint16), data.flatten())


def test_write_seizurelist_file(tmp_path):
    file_path = tmp_path / "seizurelist"
    onset = datetime(2008, 11, 3, 21, 34, 3)
    offset = datetime(2008, 11, 3, 21, 34, 13)
    onset_sample = 1024 * 3600
    offset_sample = 1024 * 3600 + 1024 * 10

    write_seizurelist_file(file_path, onset, offset, onset_sample, offset_sample)

    with open(file_path, "r") as f:
        lines = f.read().split("\n")
        assert lines[0] == f"{onset}\t{offset}\t{onset_sample}\t{offset_sample}"


#################################################3
# Tests below here test the binary_to_sql pipeline using the above fixture
#################################################3


@pytest.fixture(scope="function", autouse=True)
def metadata_tables(create_test_data):
    # setup
    engine = create_engine(ENGINE_STR)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    builder = MetaDataBuilder(engine_str=ENGINE_STR)
    builder.start(create_test_data)

    yield None

    # teardown
    Base.metadata.drop_all(engine)


def check_data_1_all
