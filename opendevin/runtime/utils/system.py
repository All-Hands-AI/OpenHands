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
