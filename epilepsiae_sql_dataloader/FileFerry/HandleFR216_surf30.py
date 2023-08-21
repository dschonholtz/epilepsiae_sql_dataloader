"""
FR216 has a 503 when trying to load the seizure data. 
This assumes we don't use the onset/offset samples which is fine for now.

The following is from the website
#	classif.	onset	pattern	vigilance	origin
1:	SP	clin: 09.01.'04 18:03:19.792969		awake	FP1
2:	UC	clin: 11.01.'04 11:18:34.000000		awake	
3:	UC	eeg: 11.01.'04 17:10:26.742188	rhythmic beta waves	awake	SP1,FT9,FP1
4:	UC	eeg: 12.01.'04 02:27:22.507813	rhythmic theta waves	sleep stage II	SP1,FT9,SP2,FT10
5:	UC	eeg: 12.01.'04 15:18:09.542969	rhythmic beta waves	awake	SP1,FT9,T7
6:	UC	eeg: 13.01.'04 02:13:06.757813	rhythmic sharp waves	sleep stage II	FP1,F3,F7,FT9,SP1,T7,P7
7:	UC	eeg: 13.01.'04 11:28:03.410156	rhythmic beta waves	awake	F7,FT9,SP1,T7
8:	UC	clin: 13.01.'04 12:50:31.214844		awake	
9:	UC	eeg: 13.01.'04 13:24:22.390625	rhythmic alpha waves	awake	C3,F3,FP1
10:	UC	eeg: 14.01.'04 03:04:39.156250	rhythmic delta waves	REM	F7,FT9,SP1,T7
11:	UC	eeg: 14.01.'04 07:59:13.167969
"""

from PushSeizureListsToServer import username, server_ip, base_remote_dir

import os
import subprocess
from pathlib import Path

special_seizure_list = """
# onset	offset	onset_sample	offset_sample
2004-01-09 18:03:19	2004-01-09 18:03:37	0	1
2004-01-11 11:18:34	2004-01-11 11:19:24	0	1
2004-01-11 17:10:26	2004-01-11 17:11:02	0	1
2004-01-12 02:27:22	2004-01-12 02:28:30	0	1
2004-01-12 15:18:09	2004-01-12 15:18:55	0	1
2004-01-13 02:13:06	2004-01-13 02:13:53	0	1
2004-01-13 11:28:03	2004-01-13 11:28:53	0	1
2004-01-13 12:50:31	2004-01-13 12:51:12	0	1
2004-01-13 13:24:22	2004-01-13 13:25:01	0	1
2004-01-14 03:04:39	2004-01-14 03:05:16	0	1
2004-01-14 07:59:13	2004-01-14 07:59:55	0	1

"""


def main():
    global special_seizure_list
    # scp the above text file to the server
    # write the text to a file
    remote_dir = Path(base_remote_dir) / "surf30"
    remote_patient_dir = "pat_21602"

    # write the file locally
    with open("seizure_list", "w") as f:
        special_seizure_list = special_seizure_list.replace("\t", " ")
        f.write(special_seizure_list)

    remote_path = f"{username}@{server_ip}:{remote_dir}/{remote_patient_dir}"
    scp_command = ["scp", "seizure_list", remote_path]

    try:
        print(f"About to SCP: special_seizure_list to {remote_path}")
        subprocess.check_output(scp_command)
    except subprocess.CalledProcessError as e:
        print(
            f"Failed to SCP: {special_seizure_list} to {remote_path}. Error: {e.output.decode()}"
        )
    # clean up that file
    os.remove("seizure_list")


if __name__ == "__main__":
    main()
