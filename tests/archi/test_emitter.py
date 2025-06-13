from src.archi.emitter import Emitter # pyrefly: ignore

def test_uuid_is_generated_when_none():
    emitter: Emitter = Emitter(None)
    assert len(emitter.uuid) > 0

def test_uuid_is_generated_when_empty():
    emitter: Emitter = Emitter("")
    assert len(emitter.uuid) > 0

def test_uuid_is_preserved_if_given():
    emitter: Emitter = Emitter("testing uuid")
    assert emitter.uuid == "testing uuid"

