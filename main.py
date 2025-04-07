import filecmp
import os
import shutil
import argparse
import sys
from time import sleep
from pathlib import Path
from datetime import datetime
from dirhash import dirhash

SOURCE_FOLDER_PATH = ""
REPLICA_FOLDER_PATH = ""
SYNCHRONIZATION_INTERVAL = 1
LOG_FILE_PATH = ""


def prepare_arguments():
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
    return parser.parse_args()


def create_dir_if_not_existent(directory: str) -> str:
    if not os.path.exists(directory):
        os.makedirs(directory)
        log(f"Created '{directory}'")
    return os.path.realpath(directory)


def create_file_if_not_existent(path_to_file: str) -> str:
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
    def is_dir_without_files():
        for _, _, files in os.walk(directory):
            if files:
                return False
        return True

    if not os.path.exists(directory) or is_dir_without_files():
        return "0"
    else:
        return dirhash(directory, "md5")


def log(message: str, with_date: bool = False):
    date_format = "%Y-%m-%d %H:%M:%S" if with_date else "%H:%M:%S"
    now = datetime.now().strftime(date_format)
    ready_message = f"[{now}] {message}"
    print(ready_message)
    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
        log_file.write(ready_message + "\n")


def count_file_occurences(file, files_list):
    counter = 0
    for other_file in files_list:
        is_signature_the_same = filecmp.cmp(file, other_file, shallow=False)
        is_name_the_same = Path(str(file)).name == Path(str(other_file)).name
        if is_signature_the_same and is_name_the_same:
            counter += 1
    return counter


def is_source_and_replica_the_same() -> bool:
    source_folder_hash = get_dir_hash(SOURCE_FOLDER_PATH)
    replica_folder_hash = get_dir_hash(REPLICA_FOLDER_PATH)
    return source_folder_hash == replica_folder_hash


def create_directories_if_not_existent(source_dirs):
    for source_dir in source_dirs:
        replica_folder = source_dir.replace(SOURCE_FOLDER_PATH, REPLICA_FOLDER_PATH)
        if not os.path.exists(replica_folder):
            os.makedirs(replica_folder)
            log(f"Created '{replica_folder}'")


def handle_files_if_not_existent(source_files, replica_files):
    def is_moved() -> bool:
        source_file_occurences = count_file_occurences(source_file, source_files)
        for other_replica_file in replica_files:
            is_signature_the_same = filecmp.cmp(source_file, other_replica_file, shallow=False)
            is_name_the_same = Path(str(source_file)).name == Path(str(other_replica_file)).name
            if not is_signature_the_same or not is_name_the_same:
                continue
            other_replica_file_occurences = count_file_occurences(other_replica_file, replica_files)
            if source_file_occurences > other_replica_file_occurences:
                return False
            shutil.move(other_replica_file, replica_file_to_check)
            log(f"Moved '{other_replica_file}' to '{replica_file_to_check}'")
            return True
        return False

    for source_file in source_files:
        replica_file_to_check = source_file.replace(SOURCE_FOLDER_PATH, REPLICA_FOLDER_PATH)

        if not os.path.exists(replica_file_to_check):
            if is_moved():
                continue
            shutil.copy2(source_file, replica_file_to_check)
            log(f"Copied '{source_file}'")
            continue

        elif not filecmp.cmp(source_file, replica_file_to_check, shallow=False):
            shutil.copy2(source_file, replica_file_to_check)
            log(f"Copied '{source_file}'")
            continue


def handle_extra_files(replica_files):
    for replica_file in replica_files:
        source_file = replica_file.replace(REPLICA_FOLDER_PATH, SOURCE_FOLDER_PATH)
        if not os.path.exists(source_file):
            os.remove(replica_file)
            log(f"Removed '{replica_file}'")


def handle_extra_directories(replica_dirs):
    replica_dirs.sort(key=len, reverse=True)
    for replica_dir in replica_dirs:
        source_folder = replica_dir.replace(REPLICA_FOLDER_PATH, SOURCE_FOLDER_PATH)
        if not os.path.exists(source_folder):
            shutil.rmtree(replica_dir)
            log(f"Removed '{replica_dir}'")


if __name__ == '__main__':
    args = prepare_arguments()
    LOG_FILE_PATH = create_file_if_not_existent(args.log)
    SOURCE_FOLDER_PATH = create_dir_if_not_existent(args.source)
    REPLICA_FOLDER_PATH = create_dir_if_not_existent(args.replica)
    SYNCHRONIZATION_INTERVAL = args.interval

    with open(LOG_FILE_PATH, 'a', encoding='utf-8') as log_file:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"\n\n[{now}] Program started\n\n"
        log_file.write(message)
        print(message)

    counter = 0
    while True:
        if is_source_and_replica_the_same():
            counter += 1
            counter %= 4
            message = "." * counter
            sys.stdout.write(f"\r{message}")
            sys.stdout.flush()
            sleep(SYNCHRONIZATION_INTERVAL)
            continue

        sys.stdout.write("\r")
        sys.stdout.flush()

        source_dirs, source_files = get_dirs_and_files(SOURCE_FOLDER_PATH)
        replica_dirs, replica_files = get_dirs_and_files(REPLICA_FOLDER_PATH)

        create_directories_if_not_existent(source_dirs)
        handle_files_if_not_existent(source_files, replica_files)
        handle_extra_files(replica_files)
        handle_extra_directories(replica_dirs)
