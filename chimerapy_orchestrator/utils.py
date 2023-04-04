from uuid import uuid4


def uuid() -> str:
    """Generates a UUID."""
    return "#" + str(uuid4())
