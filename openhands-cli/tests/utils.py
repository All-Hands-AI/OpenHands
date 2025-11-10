import time

from prompt_toolkit.input import PipeInput


def _send_keys(pipe: PipeInput, text: str, delay: float = 0.05) -> None:
    """Helper: small delay then send keys to avoid race with app.run()."""
    time.sleep(delay)
    pipe.send_text(text)
