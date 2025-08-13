import sys
from typing import Callable, Optional, Sequence, TypeVar, Union

import nltk
import numpy as np
from fuzzywuzzy import fuzz
from rouge import Rouge

# increase recursion depth to ensure ROUGE can be calculated for long sentences
if sys.getrecursionlimit() < 10_000:
    sys.setrecursionlimit(10_000)


def bleu(gold: list[str], pred: list[str]) -> float:
    """Calculate BLEU score, using smoothing method 2 with auto reweighting, in the range of 0~100.

    :param gold: list of gold tokens
    :param pred: list of predicted tokens
    :return: BLEU score
    """
    if len(pred) == 0 or len(gold) == 0:
        return 0.0
    return 100.0 * nltk.translate.bleu_score.sentence_bleu(
        [gold],
        pred,
        smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method2,
        auto_reweigh=True,
    )


def batch_bleu(golds: list[list[str]], preds: list[list[str]]) -> list[float]:
    """Calculate BLEU score for a batch of sentences.

    :param golds: list of gold sentences
    :param preds: list of predicted sentences
    :return: list of BLEU scores
    """
    if len(golds) != len(preds):
        raise ValueError('golds and preds must have the same length')
    return [bleu(gold, pred) for gold, pred in zip(golds, preds)]


def corpus_bleu(golds: list[list[str]], preds: list[list[str]]) -> float:
    """Calculate corpus-level BLEU score for a batch of sentences.

    :param golds: list of gold sentences
    :param preds: list of predicted sentences
    :return: corpus-level BLEU score
    """
    if len(golds) != len(preds):
        raise ValueError('golds and preds must have the same length')
    return 100.0 * nltk.translate.bleu_score.corpus_bleu(
        [[gold] for gold in golds],
        preds,
        smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method2,
        auto_reweigh=True,
    )


def edit_sim(
    gold: Union[str, list[str]], pred: Union[str, list[str]], sep: str = ' '
) -> float:
    """Calculate char-level edit similarity, in the range of 0~100.

    :param gold: gold sentence or list of gold tokens
    :param pred: predicted sentence or list of predicted tokens
    :param sep: separator between tokens
    :return: char-level edit similarity
    """
    if len(pred) == 0 or len(gold) == 0:
        return 0.0
    if isinstance(gold, list):
        gold = sep.join(gold)
    if isinstance(pred, list):
        pred = sep.join(pred)
    return fuzz.ratio(gold, pred)


def batch_edit_sim(
    golds: list[Union[str, list[str]]],
    preds: list[Union[str, list[str]]],
    sep: str = ' ',
) -> list[float]:
    """Calculate char-level edit similarity for a batch of sentences.

    :param golds: list of gold sentences
    :param preds: list of predicted sentences
    :param sep: separator between tokens
    :return: list of char-level edit similarity
    """
    if len(golds) != len(preds):
        raise ValueError('golds and preds must have the same length')
    return [edit_sim(gold, pred, sep) for gold, pred in zip(golds, preds)]


T = TypeVar('T')


def exact_match(gold: T, pred: T) -> float:
    """Calculate exact match accuracy, in the range of {0, 100}.

    :param gold: gold sentence or list of gold tokens
    :param pred: predicted sentence or list of predicted tokens
    :return: exact match accuracy
    """
    if len(pred) == 0 or len(gold) == 0:
        return 0.0
    return 100.0 if gold == pred else 0.0


def batch_exact_match(golds: list[T], preds: list[T]) -> list[float]:
    """Calculate exact match accuracy for a batch of sentences.

    :param golds: list of gold sentences
    :param preds: list of predicted sentences
    :return: list of exact match accuracy
    """
    if len(golds) != len(preds):
        raise ValueError('golds and preds must have the same length')
    return [exact_match(gold, pred) for gold, pred in zip(golds, preds)]


def rouge_l(
    gold: Union[str, list[str]], pred: Union[str, list[str]], sep: str = ' '
) -> dict[str, float]:
    """Calculate ROUGE-L F1, precision, and recall scores, in the range of 0~100.

    :param gold: gold sentence or list of gold tokens
    :param pred: predicted sentence or list of predicted tokens
    :return: {"p": precision, "r": recall, "f": F1}
    """
    if len(pred) == 0 or len(gold) == 0:
        return {'p': 0.0, 'r': 0.0, 'f': 0.0}
    if isinstance(gold, list):
        gold = sep.join(gold)
    if isinstance(pred, list):
        pred = sep.join(pred)
    try:
        rouge = Rouge()
        scores = rouge.get_scores(hyps=pred, refs=gold, avg=True)
        return {x: scores['rouge-l'][x] * 100.0 for x in ['p', 'r', 'f']}
    except ValueError:
        return {'p': 0.0, 'r': 0.0, 'f': 0.0}


def batch_rouge_l(
    golds: list[Union[str, list[str]]],
    preds: list[Union[str, list[str]]],
    sep: str = ' ',
) -> dict[str, list[float]]:
    """Calculate ROUGE-L F1, precision, and recall scores for a batch of sentences.

    :param golds: list of gold sentences
    :param preds: list of predicted sentences
    :param sep: separator between tokens
    :return: list of {"p": precision, "r": recall, "f": F1}
    """
    if len(golds) != len(preds):
        raise ValueError('golds and preds must have the same length')
    scores = [rouge_l(gold, pred, sep) for gold, pred in zip(golds, preds)]
    return {x: [score[x] for score in scores] for x in ['p', 'r', 'f']}


def accuracy(
    gold: list[str],
    pred: list[str],
    ignore: Optional[Sequence[str]] = None,
) -> float:
    """Calculate token-level accuracy, in the range of 0~100.
    If gold and pred are not the same length, the longer one would be truncated.

    :param gold: list of gold tokens
    :param pred: list of predicted tokens
    :param ignore: list of (gold) tokens to ignore
    :return: accuracy
    """
    if len(pred) == 0 or len(gold) == 0:
        return 0.0
    if ignore is None:
        ignore = []
    i = 0
    total = 0
    match = 0
    while i < len(gold) and i < len(pred):
        if gold[i] in ignore:
            i += 1
            continue
        total += 1
        if gold[i] == pred[i]:
            match += 1
        i += 1

    if total == 0:
        return 0.0
    return 100.0 * match / total


def batch_accuracy(
    golds: list[list[str]],
    preds: list[list[str]],
    ignore: Optional[Sequence[str]] = None,
) -> list[float]:
    """Calculate token-level accuracy for a batch of sentences.

    :param golds: list of gold sentences
    :param preds: list of predicted sentences
    :param ignore: list of (gold) tokens to ignore
    :return: list of accuracy
    """
    if len(golds) != len(preds):
        raise ValueError('golds and preds must have the same length')
    return [accuracy(gold, pred, ignore) for gold, pred in zip(golds, preds)]


def first_match_to_topk(
    first_match_list: list[int], k_values: list[int]
) -> dict[int, list[float]]:
    """Calculate top-k accuracy with the first match ranks (1-indexed).

    :param first_match: first match ranks (1-indexed)
    :param k_values: k values to consider
    :return: a mapping from k to top-k accuracies (ranging from 0~100)
    """
    return {k: [100.0 if x <= k else 0.0 for x in first_match_list] for k in k_values}


def pass_at_k(n: int, c: int, k: int) -> float:
    """Sample pass@k metric according to the Codex paper, but in the scale of 0~100.
    :param n: total number of samples
    :param c: number of correct samples
    :param k: k in pass@$k$.
    """
    if n < k or (n - c) < k:
        # fallback to the (1 - (1-p)^k) formula
        return (1 - (1 - (c / n)) ** k) * 100
    else:
        return (1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)).item()) * 100


def self_bleu(samples: list[list[str]]) -> float:
    """Calculate self-BLEU among the samples.
    :param samples: the chosen m samples
    :return: self-BLEU.
    """
    if len(samples) == 0:
        return 100.0

    scores = []
    for i in range(len(samples)):
        scores.append(
            100.0
            * nltk.translate.bleu_score.sentence_bleu(
                [samples[j] for j in range(len(samples)) if j != i],
                samples[i],
                smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method2,
                auto_reweigh=True,
            )
        )
    return np.mean(scores).item()


def self_edit_distance(samples: list[Union[str, list[str]]], sep=' ') -> float:
    """Calculate self-edit-distance among the samples.
    :param samples: the chosen m samples
    :param sep: the separator between tokens
    :return: self-edit-distance.
    """
    if len(samples) == 0:
        return 0.0

    scores = []
    for i in range(len(samples)):
        sample_i = samples[i]
        if not isinstance(sample_i, str):
            sample_i = sep.join(sample_i)
        for j in range(len(samples)):
            if i == j:
                continue
            sample_j = samples[j]
            if not isinstance(sample_j, str):
                sample_j = sep.join(sample_j)

            scores.append(100 - fuzz.ratio(sample_i, sample_j))
    return np.mean(scores).item()


QUALITY_METRICS: dict[str, Callable[[list[str], list[str]], float]] = {
    'bleu': bleu,
    'xmatch': exact_match,
    'edit-sim': edit_sim,
    'rouge-f': lambda g, p: rouge_l(g, p)['f'],
    'rouge-p': lambda g, p: rouge_l(g, p)['p'],
    'rouge-r': lambda g, p: rouge_l(g, p)['r'],
}
