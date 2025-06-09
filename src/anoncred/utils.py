import base64


def to_str(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")

def to_bin(s: str) -> bytes:
    # Assume s is a base 64 encoded binary array
    return base64.b64decode(s)