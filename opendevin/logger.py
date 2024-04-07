import logging
import os
import sys
import traceback
from datetime import datetime
from opendevin import config
from typing import Literal, Mapping, Any
from termcolor import colored

DISABLE_COLOR_PRINTING = (
    config.get_or_default('DISABLE_COLOR', 'false').lower() == 'true'
)

ColorType = Literal[
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'light_grey',
    'dark_grey',
    'light_red',
    'light_green',
    'light_yellow',
    'light_blue',
    'light_magenta',
    'light_cyan',
    'white',
]

LOG_COLORS: Mapping[str, ColorType] = {
    'BACKGROUND LOG': 'blue',
    'ACTION': 'green',
    'OBSERVATION': 'yellow',
    'INFO': 'cyan',
    'ERROR': 'red',
    'PLAN': 'light_magenta',
}

def print_with_color(text: Any, print_type: str = 'INFO'):
    color = LOG_COLORS.get(print_type.upper(), LOG_COLORS['INFO'])
    if DISABLE_COLOR_PRINTING:
        print(f"\n{print_type.upper()}:\n{str(text)}", flush=True)
    else:
        print(
            colored(f"\n{print_type.upper()}:\n", color, attrs=['bold'])
            + colored(str(text), color),
            flush=True,
        )


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        msg_type = record.__dict__.get('msg_type', 'INFO')
        if msg_type in LOG_COLORS and not DISABLE_COLOR_PRINTING:
            msg_type_color = colored(msg_type, LOG_COLORS[msg_type])
            record.msg_type = msg_type_color
        return super().format(record)

console_formatter = ColoredFormatter(
    '\033[92m%(asctime)s - %(name)s:%(levelname)s\033[0m: %(filename)s:%(lineno)s - %(msg_type)s - %(message)s',
    datefmt='%H:%M:%S',
)

file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s:%(levelname)s: %(filename)s:%(lineno)s - %(message)s',
    datefmt='%H:%M:%S',
)
llm_formatter = logging.Formatter(
    '%(message)s'
)


def get_console_handler():
    """
    Returns a console handler for logging.
    """
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    return console_handler


def get_file_handler():
    """
    Returns a file handler for logging.
    """
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f"opendevin_{timestamp}.log"
    file_handler = logging.FileHandler(os.path.join(log_dir, file_name))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    return file_handler


# Set up logging
logging.basicConfig(level=logging.ERROR)


def log_uncaught_exceptions(ex_cls, ex, tb):
    """
    Logs uncaught exceptions along with the traceback.

    Args:
        ex_cls (type): The type of the exception.
        ex (Exception): The exception instance.
        tb (traceback): The traceback object.

    Returns:
        None
    """
    logging.error(''.join(traceback.format_tb(tb)))
    logging.error('{0}: {1}'.format(ex_cls, ex))


sys.excepthook = log_uncaught_exceptions

opendevin_logger = logging.getLogger('opendevin')
opendevin_logger.setLevel(logging.INFO)
opendevin_logger.addHandler(get_console_handler())
opendevin_logger.addHandler(get_file_handler())
opendevin_logger.propagate = False
opendevin_logger.debug('Logging initialized')
opendevin_logger.debug('Logging to %s', os.path.join(
    os.getcwd(), 'logs', 'opendevin.log'))

# Exclude LiteLLM from logging output
logging.getLogger('LiteLLM').disabled = True
logging.getLogger('LiteLLM Router').disabled = True
logging.getLogger('LiteLLM Proxy').disabled = True

# LLM prompt and response logging


class LlmFileHandler(logging.FileHandler):

    def __init__(self, filename, mode='a', encoding=None, delay=False):
        """
        Initializes an instance of LlmFileHandler.

        Args:
            filename (str): The name of the log file.
            mode (str, optional): The file mode. Defaults to 'a'.
            encoding (str, optional): The file encoding. Defaults to None.
            delay (bool, optional): Whether to delay file opening. Defaults to False.
        """
        self.filename = filename
        self.message_counter = 1
        self.session = datetime.now().strftime('%y-%m-%d_%H-%M-%S')
        self.log_directory = os.path.join(
            os.getcwd(), 'logs', 'llm', self.session)
        os.makedirs(self.log_directory, exist_ok=True)
        self.baseFilename = os.path.join(self.log_directory, f"{self.filename}_{self.message_counter:03}.log")
        super().__init__(self.baseFilename, mode, encoding, delay)

    def emit(self, record):
        """
        Emits a log record.

        Args:
            record (logging.LogRecord): The log record to emit.
        """
        self.baseFilename = os.path.join(self.log_directory, f"{self.filename}_{self.message_counter:03}.log")
        self.stream = self._open()
        super().emit(record)
        self.stream.close
        opendevin_logger.debug('Logging to %s', self.baseFilename)
        self.message_counter += 1


def get_llm_prompt_file_handler():
    """
    Returns a file handler for LLM prompt logging.
    """
    llm_prompt_file_handler = LlmFileHandler('prompt')
    llm_prompt_file_handler.setFormatter(llm_formatter)
    llm_prompt_file_handler.setLevel(logging.INFO)
    if os.getenv('DEBUG'):
        llm_prompt_file_handler.setLevel(logging.DEBUG)
    return llm_prompt_file_handler


def get_llm_response_file_handler():
    """
    Returns a file handler for LLM response logging.
    """
    llm_response_file_handler = LlmFileHandler('response')
    llm_response_file_handler.setFormatter(llm_formatter)
    llm_response_file_handler.setLevel(logging.INFO)
    if os.getenv('DEBUG'):
        llm_response_file_handler.setLevel(logging.DEBUG)
    return llm_response_file_handler


llm_prompt_logger = logging.getLogger('prompt')
llm_prompt_logger.propagate = False
llm_prompt_logger.addHandler(get_llm_prompt_file_handler())

llm_response_logger = logging.getLogger('response')
llm_response_logger.propagate = False
llm_response_logger.addHandler(get_llm_response_file_handler())

# LLM initialization exception, wrapping errors from LiteLLM during LLM initialization
class LlmInitializationException(Exception):
    def __init__(self, message):
        """
        Initializes an instance of LlmInitializationException.

        Args:
            message (str): The error message.
        """
        super().__init__(message)

    def __str__(self):
        """
        Returns a string representation of the exception.

        Returns:
            str: The string representation of the exception.
        """
        if self.args:
            return self.args[0]
        return ''

    def __repr__(self):
        """
        Returns a string representation of the exception.

        Returns:
            str: The string representation of the exception.
        """
        return self.__str__()


