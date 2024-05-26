# Natural Language Toolkit: Utility functions
#
# Copyright (C) 2001-2020 NLTK Project
# Author: Steven Bird <stevenbird1@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

from itertools import chain

def pad_sequence(
    sequence,
    n,
    pad_left=False,
    pad_right=False,
    left_pad_symbol=None,
    right_pad_symbol=None,
):
    """
    Returns a padded sequence of items before ngram extraction.

    Args:
        sequence (sequence or iter): The source data to be padded.
        n (int): The degree of the ngrams.
        pad_left (bool): Whether the ngrams should be left-padded.
        pad_right (bool): Whether the ngrams should be right-padded.
        left_pad_symbol (any): The symbol to use for left padding (default is None).
        right_pad_symbol (any): The symbol to use for right padding (default is None).

    Yields:
        sequence or iter: Padded sequence of items.

    Examples:
        >>> list(pad_sequence([1, 2, 3, 4, 5], 2, pad_left=True, pad_right=True, left_pad_symbol='<s>', right_pad_symbol='</s>'))
        ['<s>', 1, 2, 3, 4, 5, '</s>']
        >>> list(pad_sequence([1, 2, 3, 4, 5], 2, pad_left=True, left_pad_symbol='<s>'))
        ['<s>', 1, 2, 3, 4, 5]
        >>> list(pad_sequence([1, 2, 3, 4, 5], 2, pad_right=True, right_pad_symbol='</s>'))
        [1, 2, 3, 4, 5, '</s>']

    Returns:
        sequence or iter: Padded sequence of items.
    """
    sequence = iter(sequence)
    if pad_left:
        sequence = chain((left_pad_symbol,) * (n - 1), sequence)
    if pad_right:
        sequence = chain(sequence, (right_pad_symbol,) * (n - 1))
    return sequence


# add a flag to pad the sequence so we get peripheral ngrams?


def ngrams(
    sequence,
    n,
    pad_left=False,
    pad_right=False,
    left_pad_symbol=None,
    right_pad_symbol=None,
):
    """
    Generate ngrams from a sequence of items.

    Args:
        sequence (sequence or iter): The source data to be converted into ngrams.
        n (int): The degree of the ngrams.
        pad_left (bool, optional): Whether the ngrams should be left-padded.
        pad_right (bool, optional): Whether the ngrams should be right-padded.
        left_pad_symbol (any, optional): The symbol to use for left padding (default is None).
        right_pad_symbol (any, optional): The symbol to use for right padding (default is None).

    Yields:
        sequence or iter: Ngrams generated from the sequence.

    Examples:
        >>> from nltk.util import ngrams
        >>> list(ngrams([1, 2, 3, 4, 5], 3))
        [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        
        >>> list(ngrams([1, 2, 3, 4, 5], 2, pad_right=True))
        [(1, 2), (2, 3), (3, 4), (4, 5), (5, None)]
        
        >>> list(ngrams([1, 2, 3, 4, 5], 2, pad_right=True, right_pad_symbol='</s>'))
        [(1, 2), (2, 3), (3, 4), (4, 5), (5, '</s>')]
        
        >>> list(ngrams([1, 2, 3, 4, 5], 2, pad_left=True, left_pad_symbol='<s>'))
        [('<s>', 1), (1, 2), (2, 3), (3, 4), (4, 5)]
        
        >>> list(ngrams([1, 2, 3, 4, 5], 2, pad_left=True, pad_right=True, left_pad_symbol='<s>', right_pad_symbol='</s>'))
        [('<s>', 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, '</s>')]
    """
    sequence = pad_sequence(
        sequence, n, pad_left, pad_right, left_pad_symbol, right_pad_symbol
    )

    history = []
    while n > 1:
        # PEP 479, prevent RuntimeError from being raised when StopIteration bubbles out of generator
        try:
            next_item = next(sequence)
        except StopIteration:
            # no more data, terminate the generator
            return
        history.append(next_item)
        n -= 1
    for item in sequence:
        history.append(item)
        yield tuple(history)
        del history[0]