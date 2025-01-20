# Adapted from https://github.com/EngineeringSoftware/teco/blob/main/src/CodeBLEU/bleu.py
# -*- coding: utf-8 -*-
# Natural Language Toolkit: BLEU Score
#
# Copyright (C) 2001-2020 NLTK Project
# Authors: Chin Yee Lee, Hengfeng Li, Ruxin Hou, Calvin Tanujaya Lim
# Contributors: Björn Mattsson, Dmitrijs Milajevs, Liling Tan
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

"""BLEU score implementation."""

import math
import sys
import warnings
from collections import Counter
from fractions import Fraction

from CodeBLEU.utils import ngrams


def sentence_bleu(
    references,
    hypothesis,
    weights=(0.25, 0.25, 0.25, 0.25),
    smoothing_function=None,
    auto_reweigh=False,
):
    """
    Calculate BLEU score (Bilingual Evaluation Understudy) from
    Papineni, Kishore, Salim Roukos, Todd Ward, and Wei-Jing Zhu. 2002.
    "BLEU: a method for automatic evaluation of machine translation."
    In Proceedings of ACL. http://www.aclweb.org/anthology/P02-1040.pdf
    >>> hypothesis1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'which',
    ...               'ensures', 'that', 'the', 'military', 'always',
    ...               'obeys', 'the', 'commands', 'of', 'the', 'party']
    >>> hypothesis2 = ['It', 'is', 'to', 'insure', 'the', 'troops',
    ...               'forever', 'hearing', 'the', 'activity', 'guidebook',
    ...               'that', 'party', 'direct']
    >>> reference1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'that',
    ...               'ensures', 'that', 'the', 'military', 'will', 'forever',
    ...               'heed', 'Party', 'commands']
    >>> reference2 = ['It', 'is', 'the', 'guiding', 'principle', 'which',
    ...               'guarantees', 'the', 'military', 'forces', 'always',
    ...               'being', 'under', 'the', 'command', 'of', 'the',
    ...               'Party']
    >>> reference3 = ['It', 'is', 'the', 'practical', 'guide', 'for', 'the',
    ...               'army', 'always', 'to', 'heed', 'the', 'directions',
    ...               'of', 'the', 'party']
    >>> sentence_bleu([reference1, reference2, reference3], hypothesis1) # doctest: +ELLIPSIS
    0.5045...
    If there is no ngrams overlap for any order of n-grams, BLEU returns the
    value 0. This is because the precision for the order of n-grams without
    overlap is 0, and the geometric mean in the final BLEU score computation
    multiplies the 0 with the precision of other n-grams. This results in 0
    (independently of the precision of the othe n-gram orders). The following
    example has zero 3-gram and 4-gram overlaps:
    >>> round(sentence_bleu([reference1, reference2, reference3], hypothesis2),4) # doctest: +ELLIPSIS
    0.0
    To avoid this harsh behaviour when no ngram overlaps are found a smoothing
    function can be used.
    >>> chencherry = SmoothingFunction()
    >>> sentence_bleu([reference1, reference2, reference3], hypothesis2,
    ...     smoothing_function=chencherry.method1) # doctest: +ELLIPSIS
    0.0370...
    The default BLEU calculates a score for up to 4-grams using uniform
    weights (this is called BLEU-4). To evaluate your translations with
    higher/lower order ngrams, use customized weights. E.g. when accounting
    for up to 5-grams with uniform weights (this is called BLEU-5) use:
    >>> weights = (1./5., 1./5., 1./5., 1./5., 1./5.)
    >>> sentence_bleu([reference1, reference2, reference3], hypothesis1, weights) # doctest: +ELLIPSIS
    0.3920...
    :param references: reference sentences
    :type references: list(list(str))
    :param hypothesis: a hypothesis sentence
    :type hypothesis: list(str)
    :param weights: weights for unigrams, bigrams, trigrams and so on
    :type weights: list(float)
    :param smoothing_function:
    :type smoothing_function: SmoothingFunction
    :param auto_reweigh: Option to re-normalize the weights uniformly.
    :type auto_reweigh: bool
    :return: The sentence-level BLEU score.
    :rtype: float
    """
    return corpus_bleu(
        [references], [hypothesis], weights, smoothing_function, auto_reweigh
    )


def corpus_bleu(
    list_of_references,
    hypotheses,
    weights=(0.25, 0.25, 0.25, 0.25),
    smoothing_function=None,
    auto_reweigh=False,
):
    """
    Calculate a single corpus-level BLEU score (aka. system-level BLEU) for all
    the hypotheses and their respective references.
    Instead of averaging the sentence level BLEU scores (i.e. marco-average
    precision), the original BLEU metric (Papineni et al. 2002) accounts for
    the micro-average precision (i.e. summing the numerators and denominators
    for each hypothesis-reference(s) pairs before the division).
    >>> hyp1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'which',
    ...         'ensures', 'that', 'the', 'military', 'always',
    ...         'obeys', 'the', 'commands', 'of', 'the', 'party']
    >>> ref1a = ['It', 'is', 'a', 'guide', 'to', 'action', 'that',
    ...          'ensures', 'that', 'the', 'military', 'will', 'forever',
    ...          'heed', 'Party', 'commands']
    >>> ref1b = ['It', 'is', 'the', 'guiding', 'principle', 'which',
    ...          'guarantees', 'the', 'military', 'forces', 'always',
    ...          'being', 'under', 'the', 'command', 'of', 'the', 'Party']
    >>> ref1c = ['It', 'is', 'the', 'practical', 'guide', 'for', 'the',
    ...          'army', 'always', 'to', 'heed', 'the', 'directions',
    ...          'of', 'the', 'party']
    >>> hyp2 = ['he', 'read', 'the', 'book', 'because', 'he', 'was',
    ...         'interested', 'in', 'world', 'history']
    >>> ref2a = ['he', 'was', 'interested', 'in', 'world', 'history',
    ...          'because', 'he', 'read', 'the', 'book']
    >>> list_of_references = [[ref1a, ref1b, ref1c], [ref2a]]
    >>> hypotheses = [hyp1, hyp2]
    >>> corpus_bleu(list_of_references, hypotheses) # doctest: +ELLIPSIS
    0.5920...
    The example below show that corpus_bleu() is different from averaging
    sentence_bleu() for hypotheses
    >>> score1 = sentence_bleu([ref1a, ref1b, ref1c], hyp1)
    >>> score2 = sentence_bleu([ref2a], hyp2)
    >>> (score1 + score2) / 2 # doctest: +ELLIPSIS
    0.6223...
    :param list_of_references: a corpus of lists of reference sentences, w.r.t. hypotheses
    :type list_of_references: list(list(list(str)))
    :param hypotheses: a list of hypothesis sentences
    :type hypotheses: list(list(str))
    :param weights: weights for unigrams, bigrams, trigrams and so on
    :type weights: list(float)
    :param smoothing_function:
    :type smoothing_function: SmoothingFunction
    :param auto_reweigh: Option to re-normalize the weights uniformly.
    :type auto_reweigh: bool
    :return: The corpus-level BLEU score.
    :rtype: float
    """
    # Before proceeding to compute BLEU, perform sanity checks.

    p_numerators = Counter()  # Key = ngram order, and value = no. of ngram matches.
    p_denominators = Counter()  # Key = ngram order, and value = no. of ngram in ref.
    hyp_lengths, ref_lengths = 0, 0

    assert len(list_of_references) == len(hypotheses), (
        'The number of hypotheses and their reference(s) should be the ' 'same '
    )

    # Iterate through each hypothesis and their corresponding references.
    for references, hypothesis in zip(list_of_references, hypotheses):
        # For each order of ngram, calculate the numerator and
        # denominator for the corpus-level modified precision.
        for i, _ in enumerate(weights, start=1):
            p_i = modified_precision(references, hypothesis, i)
            p_numerators[i] += p_i.numerator
            p_denominators[i] += p_i.denominator

        # Calculate the hypothesis length and the closest reference length.
        # Adds them to the corpus-level hypothesis and reference counts.
        hyp_len = len(hypothesis)
        hyp_lengths += hyp_len
        ref_lengths += closest_ref_length(references, hyp_len)

    # Calculate corpus-level brevity penalty.
    bp = brevity_penalty(ref_lengths, hyp_lengths)

    # Uniformly re-weighting based on maximum hypothesis lengths if largest
    # order of n-grams < 4 and weights is set at default.
    if auto_reweigh:
        if hyp_lengths < 4 and weights == (0.25, 0.25, 0.25, 0.25):
            weights = (1 / hyp_lengths,) * hyp_lengths

    # Collects the various precision values for the different ngram orders.
    p_n = [
        Fraction(p_numerators[i], p_denominators[i])
        for i, _ in enumerate(weights, start=1)
    ]

    # Returns 0 if there's no matching n-grams
    # We only need to check for p_numerators[1] == 0, since if there's
    # no unigrams, there won't be any higher order ngrams.
    if p_numerators[1] == 0:
        return 0

    # If there's no smoothing, set use method0 from SmoothinFunction class.
    if not smoothing_function:
        smoothing_function = SmoothingFunction().method1
    # Smoothen the modified precision.
    # Note: smoothing_function() may convert values into floats;
    #       it tries to retain the Fraction object as much as the
    #       smoothing method allows.
    p_n = smoothing_function(
        p_n, references=references, hypothesis=hypothesis, hyp_len=hyp_lengths
    )
    s = (w_i * math.log(p_i) for w_i, p_i in zip(weights, p_n))
    s = bp * math.exp(math.fsum(s))
    return s


def modified_precision(references, hypothesis, n):
    """
    Calculate modified ngram precision.
    The normal precision method may lead to some wrong translations with
    high-precision, e.g., the translation, in which a word of reference
    repeats several times, has very high precision.
    This function only returns the Fraction object that contains the numerator
    and denominator necessary to calculate the corpus-level precision.
    To calculate the modified precision for a single pair of hypothesis and
    references, cast the Fraction object into a float.
    The famous "the the the ... " example shows that you can get BLEU precision
    by duplicating high frequency words.
        >>> reference1 = 'the cat is on the mat'.split()
        >>> reference2 = 'there is a cat on the mat'.split()
        >>> hypothesis1 = 'the the the the the the the'.split()
        >>> references = [reference1, reference2]
        >>> float(modified_precision(references, hypothesis1, n=1)) # doctest: +ELLIPSIS
        0.2857...
    In the modified n-gram precision, a reference word will be considered
    exhausted after a matching hypothesis word is identified, e.g.
        >>> reference1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'that',
        ...               'ensures', 'that', 'the', 'military', 'will',
        ...               'forever', 'heed', 'Party', 'commands']
        >>> reference2 = ['It', 'is', 'the', 'guiding', 'principle', 'which',
        ...               'guarantees', 'the', 'military', 'forces', 'always',
        ...               'being', 'under', 'the', 'command', 'of', 'the',
        ...               'Party']
        >>> reference3 = ['It', 'is', 'the', 'practical', 'guide', 'for', 'the',
        ...               'army', 'always', 'to', 'heed', 'the', 'directions',
        ...               'of', 'the', 'party']
        >>> hypothesis = 'of the'.split()
        >>> references = [reference1, reference2, reference3]
        >>> float(modified_precision(references, hypothesis, n=1))
        1.0
        >>> float(modified_precision(references, hypothesis, n=2))
        1.0
    An example of a normal machine translation hypothesis:
        >>> hypothesis1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'which',
        ...               'ensures', 'that', 'the', 'military', 'always',
        ...               'obeys', 'the', 'commands', 'of', 'the', 'party']
        >>> hypothesis2 = ['It', 'is', 'to', 'insure', 'the', 'troops',
        ...               'forever', 'hearing', 'the', 'activity', 'guidebook',
        ...               'that', 'party', 'direct']
        >>> reference1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'that',
        ...               'ensures', 'that', 'the', 'military', 'will',
        ...               'forever', 'heed', 'Party', 'commands']
        >>> reference2 = ['It', 'is', 'the', 'guiding', 'principle', 'which',
        ...               'guarantees', 'the', 'military', 'forces', 'always',
        ...               'being', 'under', 'the', 'command', 'of', 'the',
        ...               'Party']
        >>> reference3 = ['It', 'is', 'the', 'practical', 'guide', 'for', 'the',
        ...               'army', 'always', 'to', 'heed', 'the', 'directions',
        ...               'of', 'the', 'party']
        >>> references = [reference1, reference2, reference3]
        >>> float(modified_precision(references, hypothesis1, n=1)) # doctest: +ELLIPSIS
        0.9444...
        >>> float(modified_precision(references, hypothesis2, n=1)) # doctest: +ELLIPSIS
        0.5714...
        >>> float(modified_precision(references, hypothesis1, n=2)) # doctest: +ELLIPSIS
        0.5882352941176471
        >>> float(modified_precision(references, hypothesis2, n=2)) # doctest: +ELLIPSIS
        0.07692...
    :param references: A list of reference translations.
    :type references: list(list(str))
    :param hypothesis: A hypothesis translation.
    :type hypothesis: list(str)
    :param n: The ngram order.
    :type n: int
    :return: BLEU's modified precision for the nth order ngram.
    :rtype: Fraction
    """
    # Extracts all ngrams in hypothesis
    # Set an empty Counter if hypothesis is empty.

    counts = Counter(ngrams(hypothesis, n)) if len(hypothesis) >= n else Counter()
    # Extract a union of references' counts.
    # max_counts = reduce(or_, [Counter(ngrams(ref, n)) for ref in references])
    max_counts = {}
    for reference in references:
        reference_counts = (
            Counter(ngrams(reference, n)) if len(reference) >= n else Counter()
        )
        for ngram in counts:
            max_counts[ngram] = max(max_counts.get(ngram, 0), reference_counts[ngram])

    # Assigns the intersection between hypothesis and references' counts.
    clipped_counts = {
        ngram: min(count, max_counts[ngram]) for ngram, count in counts.items()
    }

    numerator = sum(clipped_counts.values())
    # Ensures that denominator is minimum 1 to avoid ZeroDivisionError.
    # Usually this happens when the ngram order is > len(reference).
    denominator = max(1, sum(counts.values()))

    return Fraction(numerator, denominator)


def closest_ref_length(references, hyp_len):
    """
    This function finds the reference that is the closest length to the
    hypothesis. The closest reference length is referred to as *r* variable
    from the brevity penalty formula in Papineni et. al. (2002)
    :param references: A list of reference translations.
    :type references: list(list(str))
    :param hyp_len: The length of the hypothesis.
    :type hyp_len: int
    :return: The length of the reference that's closest to the hypothesis.
    :rtype: int
    """
    ref_lens = (len(reference) for reference in references)
    closest_ref_len = min(
        ref_lens, key=lambda ref_len: (abs(ref_len - hyp_len), ref_len)
    )
    return closest_ref_len


def brevity_penalty(closest_ref_len, hyp_len):
    """
    Calculate brevity penalty.
    As the modified n-gram precision still has the problem from the short
    length sentence, brevity penalty is used to modify the overall BLEU
    score according to length.
    An example from the paper. There are three references with length 12, 15
    and 17. And a concise hypothesis of the length 12. The brevity penalty is 1.
        >>> reference1 = list('aaaaaaaaaaaa')      # i.e. ['a'] * 12
        >>> reference2 = list('aaaaaaaaaaaaaaa')   # i.e. ['a'] * 15
        >>> reference3 = list('aaaaaaaaaaaaaaaaa') # i.e. ['a'] * 17
        >>> hypothesis = list('aaaaaaaaaaaa')      # i.e. ['a'] * 12
        >>> references = [reference1, reference2, reference3]
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(references, hyp_len)
        >>> brevity_penalty(closest_ref_len, hyp_len)
        1.0
    In case a hypothesis translation is shorter than the references, penalty is
    applied.
        >>> references = [['a'] * 28, ['a'] * 28]
        >>> hypothesis = ['a'] * 12
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(references, hyp_len)
        >>> brevity_penalty(closest_ref_len, hyp_len)
        0.2635971381157267
    The length of the closest reference is used to compute the penalty. If the
    length of a hypothesis is 12, and the reference lengths are 13 and 2, the
    penalty is applied because the hypothesis length (12) is less then the
    closest reference length (13).
        >>> references = [['a'] * 13, ['a'] * 2]
        >>> hypothesis = ['a'] * 12
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(references, hyp_len)
        >>> brevity_penalty(closest_ref_len, hyp_len) # doctest: +ELLIPSIS
        0.9200...
    The brevity penalty doesn't depend on reference order. More importantly,
    when two reference sentences are at the same distance, the shortest
    reference sentence length is used.
        >>> references = [['a'] * 13, ['a'] * 11]
        >>> hypothesis = ['a'] * 12
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(references, hyp_len)
        >>> bp1 = brevity_penalty(closest_ref_len, hyp_len)
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(reversed(references), hyp_len)
        >>> bp2 = brevity_penalty(closest_ref_len, hyp_len)
        >>> bp1 == bp2 == 1
        True
    A test example from mteval-v13a.pl (starting from the line 705):
        >>> references = [['a'] * 11, ['a'] * 8]
        >>> hypothesis = ['a'] * 7
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(references, hyp_len)
        >>> brevity_penalty(closest_ref_len, hyp_len) # doctest: +ELLIPSIS
        0.8668...
        >>> references = [['a'] * 11, ['a'] * 8, ['a'] * 6, ['a'] * 7]
        >>> hypothesis = ['a'] * 7
        >>> hyp_len = len(hypothesis)
        >>> closest_ref_len =  closest_ref_length(references, hyp_len)
        >>> brevity_penalty(closest_ref_len, hyp_len)
        1.0
    :param hyp_len: The length of the hypothesis for a single sentence OR the
    sum of all the hypotheses' lengths for a corpus
    :type hyp_len: int
    :param closest_ref_len: The length of the closest reference for a single
    hypothesis OR the sum of all the closest references for every hypotheses.
    :type closest_ref_len: int
    :return: BLEU's brevity penalty.
    :rtype: float
    """
    if hyp_len > closest_ref_len:
        return 1
    # If hypothesis is empty, brevity penalty = 0 should result in BLEU = 0.0
    elif hyp_len == 0:
        return 0
    else:
        return math.exp(1 - closest_ref_len / hyp_len)


class SmoothingFunction:
    """
    This is an implementation of the smoothing techniques
    for segment-level BLEU scores that was presented in
    Boxing Chen and Collin Cherry (2014) A Systematic Comparison of
    Smoothing Techniques for Sentence-Level BLEU. In WMT14.
    http://acl2014.org/acl2014/W14-33/pdf/W14-3346.pdf
    """

    def __init__(self, epsilon=0.1, alpha=5, k=5):
        """
        This will initialize the parameters required for the various smoothing
        techniques, the default values are set to the numbers used in the
        experiments from Chen and Cherry (2014).
        >>> hypothesis1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'which', 'ensures',
        ...                 'that', 'the', 'military', 'always', 'obeys', 'the',
        ...                 'commands', 'of', 'the', 'party']
        >>> reference1 = ['It', 'is', 'a', 'guide', 'to', 'action', 'that', 'ensures',
        ...               'that', 'the', 'military', 'will', 'forever', 'heed',
        ...               'Party', 'commands']
        >>> chencherry = SmoothingFunction()
        >>> print(sentence_bleu([reference1], hypothesis1)) # doctest: +ELLIPSIS
        0.4118...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method0)) # doctest: +ELLIPSIS
        0.4118...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method1)) # doctest: +ELLIPSIS
        0.4118...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method2)) # doctest: +ELLIPSIS
        0.4489...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method3)) # doctest: +ELLIPSIS
        0.4118...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method4)) # doctest: +ELLIPSIS
        0.4118...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method5)) # doctest: +ELLIPSIS
        0.4905...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method6)) # doctest: +ELLIPSIS
        0.4135...
        >>> print(sentence_bleu([reference1], hypothesis1, smoothing_function=chencherry.method7)) # doctest: +ELLIPSIS
        0.4905...
        :param epsilon: the epsilon value use in method 1
        :type epsilon: float
        :param alpha: the alpha value use in method 6
        :type alpha: int
        :param k: the k value use in method 4
        :type k: int
        """
        self.epsilon = epsilon
        self.alpha = alpha
        self.k = k

    def method0(self, p_n, *args, **kwargs):
        """
        No smoothing.
        """
        p_n_new = []
        for i, p_i in enumerate(p_n):
            if p_i.numerator != 0:
                p_n_new.append(p_i)
            else:
                _msg = str(
                    '\nThe hypothesis contains 0 counts of {}-gram overlaps.\n'
                    'Therefore the BLEU score evaluates to 0, independently of\n'
                    'how many N-gram overlaps of lower order it contains.\n'
                    'Consider using lower n-gram order or use '
                    'SmoothingFunction()'
                ).format(i + 1)
                warnings.warn(_msg, stacklevel=1)
                # When numerator==0 where denonminator==0 or !=0, the result
                # for the precision score should be equal to 0 or undefined.
                # Due to BLEU geometric mean computation in logarithm space,
                # we we need to take the return sys.float_info.min such that
                # math.log(sys.float_info.min) returns a 0 precision score.
                p_n_new.append(sys.float_info.min)
        return p_n_new

    def method1(self, p_n, *args, **kwargs):
        """
        Smoothing method 1: Add *epsilon* counts to precision with 0 counts.
        """
        return [
            (p_i.numerator + self.epsilon) / p_i.denominator
            if p_i.numerator == 0
            else p_i
            for p_i in p_n
        ]

    def method2(self, p_n, *args, **kwargs):
        """
        Smoothing method 2: Add 1 to both numerator and denominator from
        Chin-Yew Lin and Franz Josef Och (2004) Automatic evaluation of
        machine translation quality using longest common subsequence and
        skip-bigram statistics. In ACL04.
        """
        return [Fraction(p_i.numerator + 1, p_i.denominator + 1) for p_i in p_n]

    def method3(self, p_n, *args, **kwargs):
        """
        Smoothing method 3: NIST geometric sequence smoothing
        The smoothing is computed by taking 1 / ( 2^k ), instead of 0, for each
        precision score whose matching n-gram count is null.
        k is 1 for the first 'n' value for which the n-gram match count is null/
        For example, if the text contains:
         - one 2-gram match
         - and (consequently) two 1-gram matches
        the n-gram count for each individual precision score would be:
         - n=1  =>  prec_count = 2     (two unigrams)
         - n=2  =>  prec_count = 1     (one bigram)
         - n=3  =>  prec_count = 1/2   (no trigram,  taking 'smoothed' value of 1 / ( 2^k ), with k=1)
         - n=4  =>  prec_count = 1/4   (no fourgram, taking 'smoothed' value of 1 / ( 2^k ), with k=2)
        """
        incvnt = 1  # From the mteval-v13a.pl, it's referred to as k.
        for i, p_i in enumerate(p_n):
            if p_i.numerator == 0:
                p_n[i] = 1 / (2**incvnt * p_i.denominator)
                incvnt += 1
        return p_n

    def method4(self, p_n, references, hypothesis, hyp_len=None, *args, **kwargs):
        """
        Smoothing method 4:
        Shorter translations may have inflated precision values due to having
        smaller denominators; therefore, we give them proportionally
        smaller smoothed counts. Instead of scaling to 1/(2^k), Chen and Cherry
        suggests dividing by 1/ln(len(T)), where T is the length of the translation.
        """
        hyp_len = hyp_len if hyp_len else len(hypothesis)
        for i, p_i in enumerate(p_n):
            if p_i.numerator == 0 and hyp_len != 0:
                incvnt = i + 1 * self.k / math.log(
                    hyp_len
                )  # Note that this K is different from the K from NIST.
                p_n[i] = incvnt / p_i.denominator
        return p_n

    def method5(self, p_n, references, hypothesis, hyp_len=None, *args, **kwargs):
        """
        Smoothing method 5:
        The matched counts for similar values of n should be similar. To a
        calculate the n-gram matched count, it averages the n−1, n and n+1 gram
        matched counts.
        """
        hyp_len = hyp_len if hyp_len else len(hypothesis)
        m = {}
        # Requires an precision value for an addition ngram order.
        p_n_plus1 = p_n + [modified_precision(references, hypothesis, 5)]
        m[-1] = p_n[0] + 1
        for i, p_i in enumerate(p_n):
            p_n[i] = (m[i - 1] + p_i + p_n_plus1[i + 1]) / 3
            m[i] = p_n[i]
        return p_n

    def method6(self, p_n, references, hypothesis, hyp_len=None, *args, **kwargs):
        """
        Smoothing method 6:
        Interpolates the maximum likelihood estimate of the precision *p_n* with
        a prior estimate *pi0*. The prior is estimated by assuming that the ratio
        between pn and pn−1 will be the same as that between pn−1 and pn−2; from
        Gao and He (2013) Training MRF-Based Phrase Translation Models using
        Gradient Ascent. In NAACL.
        """
        hyp_len = hyp_len if hyp_len else len(hypothesis)
        # This smoothing only works when p_1 and p_2 is non-zero.
        # Raise an error with an appropriate message when the input is too short
        # to use this smoothing technique.
        assert p_n[2], 'This smoothing method requires non-zero precision for bigrams.'
        for i, p_i in enumerate(p_n):
            if i in [0, 1]:  # Skips the first 2 orders of ngrams.
                continue
            else:
                pi0 = 0 if p_n[i - 2] == 0 else p_n[i - 1] ** 2 / p_n[i - 2]
                # No. of ngrams in translation that matches the reference.
                m = p_i.numerator
                # No. of ngrams in translation.
                len_ngrams = sum(1 for _ in ngrams(hypothesis, i + 1))
                # Calculates the interpolated precision.
                p_n[i] = (m + self.alpha * pi0) / (len_ngrams + self.alpha)
        return p_n

    def method7(self, p_n, references, hypothesis, hyp_len=None, *args, **kwargs):
        """
        Smoothing method 7:
        Interpolates methods 4 and 5.
        """
        hyp_len = hyp_len if hyp_len else len(hypothesis)
        p_n = self.method4(p_n, references, hypothesis, hyp_len)
        p_n = self.method5(p_n, references, hypothesis, hyp_len)
        return p_n
