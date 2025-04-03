import filecmp
import os


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


if __name__ == '__main__':
    print("### PROGRAM STARTED ###\n")
    source_folder_path = create_dir_if_not_existent("Source")
    replica_folder_path = create_dir_if_not_existent("Replica")
    source_dirs, source_files = get_dirs_and_files(source_folder_path)
    for source_file in source_files:
        # TODO: implement check if the replica file exists
        replica_file = source_file.replace(source_folder_path, replica_folder_path)
        if filecmp.cmp(source_file, replica_file, shallow=False):
            print("Equal")
        else:
            print("Different")
