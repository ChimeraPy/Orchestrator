from pathlib import Path


def get_test_file_path(file_name: str) -> Path:
    """Get the path to a test file"""
    return Path(__file__).parent / "data" / file_name
