import filecmp
import os
import shutil
from time import sleep
from pathlib import Path

from dirhash import dirhash


def create_dir_if_not_existent(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created {directory}")
    return os.path.realpath(directory)


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

    SYNCING_PERIOD_IN_SECONDS = 1
    source_folder_path = create_dir_if_not_existent("Source")
    replica_folder_path = create_dir_if_not_existent("Replica")

    while True:
        source_folder_hash = get_dir_hash(source_folder_path)
        replica_folder_hash = get_dir_hash(replica_folder_path)
        if source_folder_hash == replica_folder_hash:
            print("Folders are the same")
            sleep(SYNCING_PERIOD_IN_SECONDS)
            continue

        source_dirs, source_files = get_dirs_and_files(source_folder_path)

        for source_dir in source_dirs:
            replica_folder = source_dir.replace(source_folder_path, replica_folder_path)
            if not os.path.exists(replica_folder):
                os.makedirs(replica_folder)
                print(f"Created {replica_folder}")

        for source_file in source_files:
            replica_file = source_file.replace(source_folder_path, replica_folder_path)
            if not os.path.exists(replica_file):
                replica_dirs, replica_files = get_dirs_and_files(replica_folder_path)
                moved = False
                for other_replica_file in replica_files:  # TODO: think about moving mechanic - fix it or remove it
                    x = not filecmp.cmp(source_file, other_replica_file, shallow=False)
                    y = not Path(str(source_file)).name == Path(str(other_replica_file)).name
                    if x and y:
                        continue
                    shutil.move(other_replica_file, replica_file)
                    print(f"Moved {other_replica_file} to {replica_file}")
                    moved = True

                if not moved:
                    shutil.copy2(source_file, replica_file)
                    print(f"Copied {source_file}")
                    continue

            if not filecmp.cmp(source_file, replica_file, shallow=False):
                shutil.copy2(source_file, replica_file)
                print(f"Copied {source_file}")
                continue

        replica_dirs, replica_files = get_dirs_and_files(replica_folder_path)

        for replica_file in replica_files:
            source_file = replica_file.replace(replica_folder_path, source_folder_path)
            if not os.path.exists(source_file):
                os.remove(replica_file)
                print(f"Removed {replica_file}")

        for replica_dir in replica_dirs:
            source_folder = replica_dir.replace(replica_folder_path, source_folder_path)
            if not os.path.exists(source_folder):
                os.rmdir(replica_dir)
                print(f"Removed {replica_dir}")
