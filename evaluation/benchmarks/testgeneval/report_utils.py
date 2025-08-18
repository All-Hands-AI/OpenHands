import json
import re


def check_coverage(coverage_output, code_file):
    json_cov = json.loads(coverage_output)
    if code_file in json_cov['files'].keys():
        file_data = json_cov['files'][code_file]
        return True, file_data['summary']['percent_covered']

    return False, 0


def check_mutation(mutation_output):
    if 'total jobs: ' in mutation_output:
        num_mutants = int(mutation_output.split('total jobs: ')[1].split('\n')[0])
        final_conf = mutation_output.split('\n')[-1]
        if len(final_conf.strip().split(' ')) == 3:
            low, val, high = final_conf.split(' ')
            low = float(low)
            val = float(val)
            high = float(high)

            confidence_range = high - val
            mutation_score = 100 - val

            return True, num_mutants, mutation_score, confidence_range

    return False, -1, 0, -1


def count_methods(code_str):
    """Counts the number of methods/functions in a given string of code.

    Args:
    code_str (str): A string containing code.

    Returns:
    int: The number of methods/functions found.
    """
    # Regular expression to find Python function definitions
    pattern = r'\bdef\b\s+\w+\s*\('
    matches = re.findall(pattern, code_str)
    return len(matches)


def get_lines_of_code(code_str):
    """Extracts lines of code from a given string.

    Args:
    code_str (str): A string containing code.

    Returns:
    list: A list of lines of code.
    """
    return len(code_str.strip().split('\n'))
