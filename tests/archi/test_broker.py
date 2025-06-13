from src.archi.broker import Broker # pyrefly: ignore
from unittest.mock import patch

def test_receiveEmit_logs_error_when_pass_unregistered_uuid():
    broker = Broker()

    with patch("src.archi.broker.logger") as mocked_logger:
        broker.receiveEmit("abc 123")
        mocked_logger.error.assert_called_once_with("abc 123 is not registered.")

