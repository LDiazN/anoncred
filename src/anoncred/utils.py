import base64
from fastapi import HTTPException, status
from ooniauth_py import ProtocolError, CredentialError, DeserializationFailed


def to_str(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")


def to_bin(s: str) -> bytes:
    # Assume s is a base 64 encoded binary array
    return base64.b64decode(s)


def to_http_excepion(error: ProtocolError | CredentialError | DeserializationFailed):
    if isinstance(error, ProtocolError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(error)}
        )
    if isinstance(error, CredentialError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"error": str(error)}
        )
    if isinstance(error, DeserializationFailed):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": str(error)}
        )
