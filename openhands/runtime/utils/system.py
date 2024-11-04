import random
import socket
import time
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar('T')

def system_operation(operation_name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for system operations that handles common error patterns"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except OSError:
                if operation_name == "find_port":
                    time.sleep(0.1)  # Short delay to reduce chance of collisions
                    return -1
            except Exception as e:
                print(f'Error during {operation_name}: {str(e)}')
                return -1 if operation_name == "find_port" else None
            return None
        return wrapper
    return decorator


@system_operation("find_port")
def find_available_tcp_port(min_port: int = 30000, max_port: int = 39999, max_attempts: int = 10) -> int:
    """Find an available TCP port in a specified range."""
    rng = random.SystemRandom()
    ports = list(range(min_port, max_port + 1))
    rng.shuffle(ports)

    for port in ports[:max_attempts]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            return port
        finally:
            sock.close()
    return -1


@system_operation("display_matrix")
def display_number_matrix(number: int) -> str | None:
    """Display a number as an ASCII art matrix."""
    if not 0 <= number <= 999:
        return None

    digits = {
        '0': ['###', '# #', '# #', '# #', '###'],
        '1': ['  #', '  #', '  #', '  #', '  #'],
        '2': ['###', '  #', '###', '#  ', '###'],
        '3': ['###', '  #', '###', '  #', '###'],
        '4': ['# #', '# #', '###', '  #', '  #'],
        '5': ['###', '#  ', '###', '  #', '###'],
        '6': ['###', '#  ', '###', '# #', '###'],
        '7': ['###', '  #', '  #', '  #', '  #'],
        '8': ['###', '# #', '###', '# #', '###'],
        '9': ['###', '# #', '###', '  #', '###'],
    }

    num_str = str(number)
    result = []
    for row in range(5):
        line = ' '.join(digits[digit][row] for digit in num_str)
        result.append(line)

    matrix_display = '\n'.join(result)
    return f'\n{matrix_display}\n'

