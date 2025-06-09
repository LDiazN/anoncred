from anoncred.protocol import Issuance
from anoncred.probe import Probe
from anoncred.models import SigningKeyPair
from anoncred.main import Measurement
from sqlmodel import Session
from pprint import pprint


def test_manifest(client):
    r = client.get("/manifest")
    assert r.status_code == 200, r.json()
    pprint(r.json())

def test_workflow(client):
    probe = Probe(client)

    # 1. Step 1: manifest
    probe.get_manifest()

    # Try to get manifest
    probe.register()