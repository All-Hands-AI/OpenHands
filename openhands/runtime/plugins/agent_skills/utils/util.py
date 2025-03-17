from datasets import load_dataset
import os
import fnmatch
from collections import defaultdict
import re
from util.benchmark.setup_repo import setup_repo


# SET THIS IF YOU WANT TO USE THE PREPROCESSED FILES
GRAPH_INDEX_DIR = os.environ.get("GRAPH_INDEX_DIR")
BM25_INDEX_DIR = os.environ.get("BM25_INDEX_DIR")
assert GRAPH_INDEX_DIR != ''
assert BM25_INDEX_DIR != ''


def find_matching_files_from_list(file_list, file_pattern):
    """
    Find and return a list of file paths from the given list that match the given keyword or pattern.
    
    :param file_list: A list of file paths to search through.
    :param file_pattern: A keyword or pattern for file matching. Can be a simple keyword or a glob-style pattern.
    :return: A list of matching file paths
    """
    # If the pattern contains any of these glob-like characters, treat it as a glob pattern.
    if '*' in file_pattern or '?' in file_pattern or '[' in file_pattern:
        matching_files = fnmatch.filter(file_list, file_pattern)
    else:
        # Otherwise, treat it as a keyword search
        matching_files = [file for file in file_list if file_pattern in file]
    
    return matching_files


def get_meta_data(target_id, dataset:str="princeton-nlp/SWE-bench_Lite", split:str = "test"):
    swe_bench_data = load_dataset(dataset, split=split)
    bench_data = [x for x in swe_bench_data if x["instance_id"] == target_id][0]
    return bench_data


def merge_intervals(intervals):
    # intervals inclusive
    if not intervals:
        return []

    # Sort the intervals based on the starting value of each tuple
    intervals.sort(key=lambda interval: interval[0])

    merged_intervals = [intervals[0]]

    for current in intervals[1:]:
        last = merged_intervals[-1]

        # Check if there is overlap
        if current[0] <= last[1]:
            # If there is overlap, merge the intervals
            merged_intervals[-1] = (last[0], max(last[1], current[1]))
        else:
            # If there is no overlap, just add the current interval to the result list
            merged_intervals.append(current)

    return merged_intervals


def extract_file_to_code(raw_content: str):
    # Pattern to extract the file name and code
    pattern = r'([\w\/\.]+)\n```\n(.*?)\n```'

    # Use re.findall to extract all matches (file name and code)
    matches = re.findall(pattern, raw_content, re.DOTALL)

    # Create a dictionary from the extracted file names and code
    file_to_code = {filename: code for filename, code in matches}

    return file_to_code


