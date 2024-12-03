from unittest.mock import patch

from tenacity import RetryCallState

from openhands.utils.tenacity_stop import stop_if_should_exit


def test_stop_if_should_exit_true():
    with patch('openhands.utils.tenacity_stop.should_exit', return_value=True):
        stopper = stop_if_should_exit()
        assert stopper(RetryCallState(None, None, None, kwargs={})) is True


def test_stop_if_should_exit_false():
    with patch('openhands.utils.tenacity_stop.should_exit', return_value=False):
        stopper = stop_if_should_exit()
        assert stopper(RetryCallState(None, None, None, kwargs={})) is False
