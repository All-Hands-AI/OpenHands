import collections
import re
from warnings import warn

import yaml


def yaml_parser(message):
    """Parse a yaml message for the retry function."""

    # saves gpt-3.5 from some yaml parsing errors
    message = re.sub(r':\s*\n(?=\S|\n)', ': ', message)

    try:
        value = yaml.safe_load(message)
        valid = True
        retry_message = ''
    except yaml.YAMLError as e:
        warn(str(e), stacklevel=2)
        value = {}
        valid = False
        retry_message = "Your response is not a valid yaml. Please try again and be careful to the format. Don't add any apology or comment, just the answer."
    return value, valid, retry_message


def _compress_chunks(text, identifier, skip_list, split_regex='\n\n+'):
    """Compress a string by replacing redundant chunks by identifiers. Chunks are defined by the split_regex."""
    text_list = re.split(split_regex, text)
    text_list = [chunk.strip() for chunk in text_list]
    counter = collections.Counter(text_list)
    def_dict = {}
    id = 0

    # Store items that occur more than once in a dictionary
    for item, count in counter.items():
        if count > 1 and item not in skip_list and len(item) > 10:
            def_dict[f'{identifier}-{id}'] = item
            id += 1

    # Replace redundant items with their identifiers in the text
    compressed_text = '\n'.join(text_list)
    for key, value in def_dict.items():
        compressed_text = compressed_text.replace(value, key)

    return def_dict, compressed_text


def compress_string(text):
    """Compress a string by replacing redundant paragraphs and lines with identifiers."""

    # Perform paragraph-level compression
    def_dict, compressed_text = _compress_chunks(
        text, identifier='§', skip_list=[], split_regex='\n\n+'
    )

    # Perform line-level compression, skipping any paragraph identifiers
    line_dict, compressed_text = _compress_chunks(
        compressed_text, '¶', list(def_dict.keys()), split_regex='\n+'
    )
    def_dict.update(line_dict)

    # Create a definitions section
    def_lines = ['<definitions>']
    for key, value in def_dict.items():
        def_lines.append(f'{key}:\n{value}')
    def_lines.append('</definitions>')
    definitions = '\n'.join(def_lines)

    return definitions + '\n' + compressed_text


def extract_html_tags(text, keys):
    """Extract the content within HTML tags for a list of keys.

    Parameters
    ----------
    text : str
        The input string containing the HTML tags.
    keys : list of str
        The HTML tags to extract the content from.

    Returns
    -------
    dict
        A dictionary mapping each key to a list of subset in `text` that match the key.

    Notes
    -----
    All text and keys will be converted to lowercase before matching.

    """
    content_dict = {}
    # text = text.lower()
    # keys = set([k.lower() for k in keys])
    for key in keys:
        pattern = f'<{key}>(.*?)</{key}>'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            content_dict[key] = [match.strip() for match in matches]
    return content_dict


class ParseError(Exception):
    pass


def parse_html_tags_raise(text, keys=(), optional_keys=(), merge_multiple=False):
    """A version of parse_html_tags that raises an exception if the parsing is not successful."""
    content_dict, valid, retry_message = parse_html_tags(
        text, keys, optional_keys, merge_multiple=merge_multiple
    )
    if not valid:
        raise ParseError(retry_message)
    return content_dict


def parse_html_tags(text, keys=(), optional_keys=(), merge_multiple=False):
    """Satisfy the parse api, extracts 1 match per key and validates that all keys are present

    Parameters
    ----------
    text : str
        The input string containing the HTML tags.
    keys : list of str
        The HTML tags to extract the content from.
    optional_keys : list of str
        The HTML tags to extract the content from, but are optional.

    Returns
    -------
    dict
        A dictionary mapping each key to subset of `text` that match the key.
    bool
        Whether the parsing was successful.
    str
        A message to be displayed to the agent if the parsing was not successful.
    """
    all_keys = tuple(keys) + tuple(optional_keys)
    content_dict = extract_html_tags(text, all_keys)
    retry_messages = []

    for key in all_keys:
        if key not in content_dict:
            if key not in optional_keys:
                retry_messages.append(f'Missing the key <{key}> in the answer.')
        else:
            val = content_dict[key]
            content_dict[key] = val[0]
            if len(val) > 1:
                if not merge_multiple:
                    retry_messages.append(
                        f'Found multiple instances of the key {key}. You should have only one of them.'
                    )
                else:
                    # merge the multiple instances
                    content_dict[key] = '\n'.join(val)

    valid = len(retry_messages) == 0
    retry_message = '\n'.join(retry_messages)
    return content_dict, valid, retry_message
