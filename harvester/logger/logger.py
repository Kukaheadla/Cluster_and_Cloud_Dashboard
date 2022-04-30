"""
Contains simple logging functions.

Author: Alex
"""


def log(message: str, debug: bool):
    """
    Logs a message if debug flag is True.
    """
    if debug:
        print(message)
