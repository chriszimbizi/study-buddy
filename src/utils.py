import os


def has_files(directory):
    """
    Check if a directory contains any files.

    Parameters:
    - directory (str): The directory to check.

    Returns:
    - bool: True if the directory contains any files, False otherwise.
    """
    return any(
        os.path.isfile(os.path.join(directory, f)) for f in os.listdir(directory)
    )
