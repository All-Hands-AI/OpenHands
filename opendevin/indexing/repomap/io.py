import base64
import os
from datetime import datetime

from rich.console import Console
from rich.text import Text

from .utils import is_image_file


class InputOutput:
    def __init__(
        self,
        pretty=True,
        encoding='utf-8',
    ):
        no_color = os.environ.get('NO_COLOR')
        if no_color is not None and no_color != '':
            pretty = False

        self.pretty = pretty

        self.encoding = encoding

        if pretty:
            self.console = Console()
        else:
            self.console = Console(force_terminal=False, no_color=True)

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.append_chat_history(f'\n# aider chat started at {current_time}\n\n')

    def read_image(self, filename):
        try:
            with open(str(filename), 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read())
                return encoded_string.decode('utf-8')
        except FileNotFoundError:
            self.tool_error(f'{filename}: file not found error')
            return
        except IsADirectoryError:
            self.tool_error(f'{filename}: is a directory')
            return
        except Exception as e:
            self.tool_error(f'{filename}: {e}')
            return

    def read_text(self, filename):
        if is_image_file(filename):
            return self.read_image(filename)

        try:
            with open(str(filename), 'r', encoding=self.encoding) as f:
                return f.read()
        except FileNotFoundError:
            self.tool_error(f'{filename}: file not found error')
            return
        except IsADirectoryError:
            self.tool_error(f'{filename}: is a directory')
            return
        except UnicodeError as e:
            self.tool_error(f'{filename}: {e}')
            self.tool_error('Use --encoding to set the unicode encoding.')
            return

    # OUTPUT

    def tool_error(self, message='', strip=True):
        if message.strip():
            if '\n' in message:
                for line in message.splitlines():
                    self.append_chat_history(
                        line, linebreak=True, blockquote=True, strip=strip
                    )
            else:
                if strip:
                    hist = message.strip()
                else:
                    hist = message
                self.append_chat_history(hist, linebreak=True, blockquote=True)

        message = Text(message)
        self.console.print(message, dict())

    def tool_output(self, *messages, log_only=False):
        if messages:
            hist = ' '.join(messages)
            hist = f'{hist.strip()}'
            self.append_chat_history(hist, linebreak=True, blockquote=True)

        if not log_only:
            messages = tuple(map(Text, messages))
            self.console.print(*messages, dict())

    def append_chat_history(self, text, linebreak=False, blockquote=False, strip=True):
        if blockquote:
            if strip:
                text = text.strip()
            text = '> ' + text
        if linebreak:
            if strip:
                text = text.rstrip()
            text = text + '  \n'
        if not text.endswith('\n'):
            text += '\n'
