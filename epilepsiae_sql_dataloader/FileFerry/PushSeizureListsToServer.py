import os
import subprocess
from pathlib import Path

# specify your username, server IP, and the base remote directory path
username = "schonholtzd"
server_ip = "10.75.9.71"
base_remote_dir = "/mnt/external1/raw"


def scp_to_server(sub_dir):
    # specify the remote directory path based on the sub_dir
    remote_dir = os.path.join(base_remote_dir, sub_dir)
    if sub_dir == "inv_30":
        remote_dir = remote_dir.replace("inv_30", "inv")
    # specify the local directory path
    local_base_dir = "seizurelists"
    local_dir = os.path.join(local_base_dir, sub_dir)
    # the local dir is one dir up from this file:
    local_dir = Path(__file__).parent.parent.parent / local_dir
    local_dirs = os.listdir(local_dir)

    # iterate over each local directory
    for a_dir in local_dirs:
        # extract the patient number from the directory name
        patient_number = a_dir.split("_")[1]

        # construct the remote directory names
        remote_patient_dirs = [f"pat_{patient_number}02", f"pat_{patient_number}03"]

        # construct the full local path
        local_path = os.path.join(local_dir, a_dir, "seizure_list")

        # try to scp to each remote directory
        for remote_patient_dir in remote_patient_dirs:
            remote_path = f"{username}@{server_ip}:{remote_dir}/{remote_patient_dir}"
            scp_command = ["scp", local_path, remote_path]

            try:
                print(f"About to SCP: {local_path} to {remote_path}")
                subprocess.check_output(scp_command)
                break  # if scp is successful, break the loop
            except subprocess.CalledProcessError as e:
                print(
                    f"Failed to SCP: {local_path} to {remote_path}. Error: {e.output.decode()}"
                )


if __name__ == "__main__":
    # call the function with 'surf_30' or 'inv_30'
    # scp_to_server("surf_30")
    scp_to_server("inv_30")
