from src.archi.consumer import Consumer

def test_consumer_uuid_autogen():
    c = Consumer()
    assert isinstance(c.uuid, str)
    assert len(c.uuid) > 0