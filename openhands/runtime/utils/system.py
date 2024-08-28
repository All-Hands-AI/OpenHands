import socket


def find_available_tcp_port() -> int:
    """Find an available TCP port, return -1 if none available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', 0))
        port = sock.getsockname()[1]
        return port
    except Exception:
        return -1
    finally:
        sock.close()


def display_number_matrix(number: int) -> str | None:
    if not 0 <= number <= 999:
        return None

    # Define the matrix representation for each digit
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

    # alternatively, with leading zeros: num_str = f"{number:03d}"
    num_str = str(number)  # Convert to string without padding

    result = []
    for row in range(5):
        line = ' '.join(digits[digit][row] for digit in num_str)
        result.append(line)

    matrix_display = '\n'.join(result)
    return f'\n{matrix_display}\n'
