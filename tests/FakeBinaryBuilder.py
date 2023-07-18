"""
In the same dir there is a file:
 test_data/head_files/good.head 
 It has contents in the below format:

start_ts=2008-11-03 20:34:03.000
num_samples=3686400
sample_freq=1024
conversion_factor=0.179000
num_channels=93
elec_names=[GA1,GA2,GA3,GA4,GA5,GA6,GA7,GA8,GB1,GB2,GB3,GB4,GB5,GB6,GB7,GB8,GC1,GC2,GC3,GC4,GC5,GC6,GC7,GC8,GD1,GD2,GD3,GD4,GD5,GD6,GD7,GD8,GE1,GE2,GE3,GE4,GE5,GE6,GE7,GE8,GF1,GF2,GF3,GF4,GF5,GF6,GF7,GF8,GG1,GG2,GG3,GG4,GG5,GG6,GG7,GG8,GH1,GH2,GH3,GH4,GH5,GH6,GH7,GH8,M1,M2,M3,M4,M5,M6,M7,M8,IHA1,IHA2,IHA3,IHA4,IHB1,IHB2,IHB3,IHB4,IHC1,IHC2,IHC3,IHC4,IHD1,IHD2,IHD3,IHD4,FL1,FL2,FL3,FL4,ECG]
pat_id=108402
adm_id=1084102
rec_id=108400102
duration_in_sec=3600
sample_bytes=2


 This file will generate a binary file that corresponds to that data called test_data/binary_ex.data
 If we used the data  will be a numpy array of shape (3686400, 93) with dtype uint16 (2 bytes per sample) 1 byte per sample would be uint8
 This is because the num samples is 3686400 and the num channels is 93 and the sample_bytes is 2.
 Below is a function that generates that file.
"""

from pathlib import Path
import numpy as np


def generate_binary_file():
    # Set file paths
    # Get the current file path
    current_file_path = Path(__file__).resolve()

    # Build the head_file_path and binary_file_path relative to the current file path
    head_file_path = current_file_path.parent / "test_data" / "head_files" / "good.head"
    binary_file_path = current_file_path.parent / "test_data" / "binary_ex.data"

    # Read data from the head file
    with open(head_file_path, "r") as f:
        head_data = f.read()

    # Extract num_samples and num_channels from the head data
    num_samples = int(head_data.split("num_samples=")[1].split("\n")[0])
    num_channels = int(head_data.split("num_channels=")[1].split("\n")[0])
    sample_bytes = int(head_data.split("sample_bytes=")[1].split("\n")[0])
    if sample_bytes == 1:
        dtype = "uint8"
    elif sample_bytes == 2:
        dtype = "uint16"

    # Generate data based on the num_samples and num_channels
    # Using dtype uint16 since 2 bytes per sample
    # For 1 byte per sample, we would use uint8
    data = np.random.randint(
        0, high=2**16, size=(num_samples, num_channels), dtype=dtype
    )

    # Write data to the binary file
    data.tofile(binary_file_path)


# Call the function
generate_binary_file()
