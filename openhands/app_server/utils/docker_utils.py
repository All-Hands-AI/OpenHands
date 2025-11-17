
from urllib.parse import urlparse, urlunparse


def replace_localhost_hostname(
    url: str, replacement: str = 'host.docker.internal'
) -> str:
    """Replace localhost hostname in URL with the specified replacement.

    Only replaces the hostname if it's exactly 'localhost', preserving all other
    parts of the URL including port, path, query parameters, etc.

    Args:
        url: The URL to process
        replacement: The hostname to replace localhost with

    Returns:
        URL with localhost hostname replaced, or original URL if hostname is not localhost
    """
    parsed = urlparse(url)
    if parsed.hostname == 'localhost':
        # Replace only the hostname part, preserving port and everything else
        netloc = parsed.netloc.replace('localhost', replacement, 1)
        return urlunparse(parsed._replace(netloc=netloc))
    return url
