import filecmp
import os
import shutil
import argparse
from time import sleep
from pathlib import Path

from dirhash import dirhash


def create_dir_if_not_existent(directory: str) -> str:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created '{directory}'")
    return os.path.realpath(directory)


def create_file_if_not_existent(path_to_file: str):
    if not path_to_file.endswith(".txt"):
        path_to_file += ".txt"
    path = Path(path_to_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
        print(f"Created '{path_to_file}'")
        return path_to_file


def get_dirs_and_files(root_dir):
    all_dirs = list()
    all_files = list()
    for (root, dirs, files) in os.walk(root_dir):
        for directory in dirs:
            all_dirs.append(os.path.join(root, directory))
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_dirs, all_files


def get_dir_hash(directory):
    if os.listdir(directory):
        return dirhash(directory, "md5")
    else:
        return "0"


if __name__ == '__main__':
    print("### PROGRAM STARTED ###\n")

    default_source = "Source"
    default_replica = "Replica"
    default_interval = 1
    default_log_path = "log.txt"

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source",
                        dest="source",
                        help=f"Source folder destination. If not existent it will be created. Default: '{default_source}'",
                        type=str,
                        default=default_source)
    parser.add_argument("-r", "--replica",
                        dest="replica",
                        help=f"Replica folder destination. If not existent it will be created. Default: '{default_replica}'",
                        type=str,
                        default=default_replica)
    parser.add_argument("-i", "--interval",
                        dest="interval",
                        help=f"Synchronization interval of folders in seconds. Default: '{default_interval}'",
                        type=int,
                        default=default_interval)
    parser.add_argument("-l", "--log_path",
                        dest="log",
                        help=f"Log file destination. Default: '{default_log_path}'",
                        type=str,
                        default=default_log_path)

    args = parser.parse_args()
    source_folder_path = create_dir_if_not_existent(args.source)
    replica_folder_path = create_dir_if_not_existent(args.replica)
    SYNCHRONIZATION_INTERVAL = args.interval
    log_file_path = create_file_if_not_existent(args.log)
    # TODO: logging mechanic. Append program run date, and then modifications of the contents of the source and replica folders

    while True:
        source_folder_hash = get_dir_hash(source_folder_path)
        replica_folder_hash = get_dir_hash(replica_folder_path)
        if source_folder_hash == replica_folder_hash:
            print("Folders are the same")
            sleep(SYNCHRONIZATION_INTERVAL)
            continue

        source_dirs, source_files = get_dirs_and_files(source_folder_path)

        for source_dir in source_dirs:
            replica_folder = source_dir.replace(source_folder_path, replica_folder_path)
            if not os.path.exists(replica_folder):
                os.makedirs(replica_folder)
                print(f"Created '{replica_folder}'")

        for source_file in source_files:
            replica_file = source_file.replace(source_folder_path, replica_folder_path)
            if not os.path.exists(replica_file):
                replica_dirs, replica_files = get_dirs_and_files(replica_folder_path)
                moved = False
                for other_replica_file in replica_files:
                    is_signature_the_same = filecmp.cmp(source_file, other_replica_file, shallow=False)
                    is_name_the_same = Path(str(source_file)).name == Path(str(other_replica_file)).name
                    if not is_signature_the_same or not is_name_the_same:
                        continue
                    shutil.move(other_replica_file, replica_file)
                    print(f"Moved '{other_replica_file}' to '{replica_file}'")
                    moved = True
                    break

                if not moved:
                    shutil.copy2(source_file, replica_file)
                    print(f"Copied '{source_file}'")
                    continue

            if not filecmp.cmp(source_file, replica_file, shallow=False):
                shutil.copy2(source_file, replica_file)
                print(f"Copied '{source_file}'")
                continue

        replica_dirs, replica_files = get_dirs_and_files(replica_folder_path)

        for replica_file in replica_files:
            source_file = replica_file.replace(replica_folder_path, source_folder_path)
            if not os.path.exists(source_file):
                os.remove(replica_file)
                print(f"Removed '{replica_file}'")

        for replica_dir in replica_dirs:
            source_folder = replica_dir.replace(replica_folder_path, source_folder_path)
            if not os.path.exists(source_folder):
                os.rmdir(replica_dir)
                print(f"Removed '{replica_dir}'")
