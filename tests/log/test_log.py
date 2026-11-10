import logging
from unittest.mock import MagicMock, patch

from pyrmalib.log import Log


@patch('pyrmalib.log.handlers.RotatingFileHandler')
def test_log_class(mock_handler_cls):
    mock_handler = MagicMock()
    mock_handler.level = logging.DEBUG
    mock_handler_cls.return_value = mock_handler

    logger = Log('test_logger', level='DEBUG', filename='test.log')
    assert logger.log is not None

    logger.error("error message", pr=True)
    logger.info("info message")
    logger.warning("warning message")
    logger.debug("debug message")
    logger.critical("critical message")
    logger.exception()
