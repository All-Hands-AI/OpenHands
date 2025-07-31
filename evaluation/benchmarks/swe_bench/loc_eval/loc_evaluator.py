import argparse
import ast
import json
import os
import re

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

from evaluation.benchmarks.swe_bench.loc_eval.loc_utils import LocMeta
from evaluation.benchmarks.swe_bench.run_infer import filter_dataset
from evaluation.utils.shared import prepare_dataset
from openhands.core.logger import openhands_logger as logger


class LocEvaluator:
    def __init__(self, args):
        """
        Localization evaluation.

        Args:
            args: all main arguments
        """
        # Config
        self.args = args
        self.eval_dir = args.eval_dir
        self.eval_task_success = self._check_if_to_eval_success()
        self.sandbox_root = '/workspace'
        self.agent_turn_num = -1
        self.max_agent_turn = args.max_infer_turn
        self.align_failed_with_max_iter = args.align_with_max

        # Data
        self.instance = None
        self.trajectory = None

        # Localization
        self.localizer = LocMeta(args.dataset, args.split)
        self.gold_loc = {'file': [], 'function': []}
        self.agent_loc = {
            'gold loc': {'file': [], 'function': []},
            'agent loc': {'file': [], 'function': []},
            'turn index': {'file': [], 'function': []},
            'loc progress': {'file': [], 'function': []},
        }

        # Task success tracking
        self.task_resolved = False

        # Cost
        self.cost_summary = {'total_cost': 0.0, 'avg_cost': 0.0, 'details': {}}

        # Save
        self.save_dir = os.path.join(args.save_dir, 'loc_eval_results')
        self._init_dir(self.save_dir)
        self.all_eval_results = {}
        self.overall_eval = {}

    def _init_config(self):
        # Data
        self.instance = None
        self.gold_loc = {'file': [], 'function': []}
        self.trajectory = None
        self.agent_turn_num = -1

        # Localization
        self.agent_loc = {
            'gold loc': {'file': [], 'function': []},
            'agent loc': {'file': [], 'function': []},
            'turn index': {'file': [], 'function': []},
            'loc progress': {'file': [], 'function': []},
        }

        # Task success tracking
        self.task_resolved = False

    def _init_dir(self, directory_path):
        """
        Check if a directory exists and create it if it doesn't.

        Args:
            directory_path (str): Path to the directory to check/create

        Returns:
            bool: True if directory already existed, False if it was created
        """
        if os.path.exists(directory_path):
            if not os.path.isdir(directory_path):
                raise NotADirectoryError(
                    f'Path exists but is not a directory: {directory_path}'
                )
            return True
        else:
            os.makedirs(directory_path)
            return False

    def _check_if_to_eval_success(self):
        """Check if post-evaluation outputs exist"""
        if not os.path.isdir(self.eval_dir):
            return False
        else:
            return True

    def _compute_avg_over_all(self):
        """Compute average loc evaluations over all instances"""
        macro_la_file, micro_la_file = 0, 0
        macro_la_func, micro_la_func = 0, 0
        resolve_rate = 0
        macro_avg_file_idx, macro_avg_func_idx = 0, 0
        micro_avg_file_idx, micro_avg_func_idx = 0, 0
        avg_resolve_idx = 0
        total_instance_num = len(self.all_eval_results)

        for instance_id in self.all_eval_results:
            curr_eval_result = self.all_eval_results[instance_id]['final_eval']

            # File
            macro_la_file += curr_eval_result['localization']['loc_acc (%)'][
                'la_file (%)'
            ]['la_file_macro']
            micro_la_file += curr_eval_result['localization']['loc_acc (%)'][
                'la_file (%)'
            ]['la_file_micro']
            macro_avg_file_idx += curr_eval_result['localization']['turn_idx']['file'][
                'macro'
            ]
            micro_avg_file_idx += curr_eval_result['localization']['turn_idx']['file'][
                'micro'
            ]

            # Function
            macro_la_func += curr_eval_result['localization']['loc_acc (%)'][
                'la_func (%)'
            ]['la_func_macro']
            micro_la_func += curr_eval_result['localization']['loc_acc (%)'][
                'la_func (%)'
            ]['la_func_micro']
            macro_avg_func_idx += curr_eval_result['localization']['turn_idx'][
                'function'
            ]['macro']
            micro_avg_func_idx += curr_eval_result['localization']['turn_idx'][
                'function'
            ]['micro']

            if self.eval_task_success:
                if curr_eval_result['task_success']['resolved']:
                    resolve_rate += 1
                    avg_resolve_idx += curr_eval_result['task_success']['resolve_index']
                else:
                    avg_resolve_idx += self.max_agent_turn

        # Average
        macro_la_file = macro_la_file / total_instance_num
        micro_la_file = micro_la_file / total_instance_num
        macro_la_func = macro_la_func / total_instance_num
        micro_la_func = micro_la_func / total_instance_num
        macro_avg_file_idx = macro_avg_file_idx / total_instance_num
        micro_avg_file_idx = micro_avg_file_idx / total_instance_num
        macro_avg_func_idx = macro_avg_func_idx / total_instance_num
        micro_avg_func_idx = micro_avg_func_idx / total_instance_num

        if self.eval_task_success:
            resolve_rate = resolve_rate / total_instance_num * 100
            avg_resolve_idx = avg_resolve_idx / total_instance_num

        # Cost metric
        total_cost, avg_cost = 0.0, 0.0
        for instance_key in self.cost_summary['details']:
            total_cost += self.cost_summary['details'][instance_key]
        avg_cost = total_cost / len(self.cost_summary['details'])
        self.cost_summary['total_cost'] = total_cost
        self.cost_summary['avg_cost'] = avg_cost

        self.overall_eval = {
            'la_file (%)': {'macro': macro_la_file, 'micro': micro_la_file},
            'la_func (%)': {'macro': macro_la_func, 'micro': micro_la_func},
            'resolve_rate (%)': resolve_rate if self.eval_task_success else None,
            'loc_file_idx (turn idx)': {
                'macro': macro_avg_file_idx,
                'micro': micro_avg_file_idx,
            },
            'loc_func_idx (turn idx)': {
                'macro': macro_avg_func_idx,
                'micro': micro_avg_func_idx,
            },
            'resolve_idx (turn idx)': avg_resolve_idx
            if self.eval_task_success
            else None,
            'max_turn_limit': self.max_agent_turn,
            'total_instance_num': total_instance_num,
            'cost_summary': self.cost_summary,
        }
        self._write_to_json(self.overall_eval, 'overall_eval.json')

    def _save_to_eval_dicts(self, agent_trajectory: dict):
        # Current instancec
        self._write_to_json(
            agent_trajectory, f'loc__instance_{self.instance.instance_id}.json'
        )

        # All instances
        self.all_eval_results[self.instance.instance_id] = agent_trajectory
        self._write_to_json(self.all_eval_results, 'all_loc_evals.json')

        # Overall scores
        self._compute_avg_over_all()

    def _write_to_json(self, data, file_name):
        """
        Writes the current object data to a JSON file.

        Returns:
            bool: True if writing was successful, False otherwise.
        """
        try:
            output_dir = os.path.join(self.save_dir, 'loc_acc')
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, file_name)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f'Error writing to JSON: {str(e)}')
            return False

    def read_from_json(self, file_path):
        """
        Reads data from a JSON file and loads it into the current object.

        Returns:
            dict: The loaded JSON data, or an empty dict if the file doesn't exist
                or an error occurs.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            logger.warning(
                f"Warning: File '{file_path}' not found. Returning an empty dictionary..."
            )
            return {}
        except json.JSONDecodeError:
            logger.error(
                f"Error: File '{file_path}' contains invalid JSON. Returning an empty dictionary..."
            )
            return {}
        except Exception as e:
            logger.error(
                f'Error reading from JSON: {str(e)}\nReturning an empty dictionary...'
            )
            return {}

    def read_from_jsonl(self, file_path):
        """
        Reads data from a JSON file and loads it into the current object.

        Returns:
            dict: The loaded JSON data, or an empty dict if the file doesn't exist
                or an error occurs.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            logger.warning(
                f"Warning: File '{file_path}' not found. Returning an empty dictionary..."
            )
            return {}
        except json.JSONDecodeError:
            logger.error(
                f"Error: File '{file_path}' contains invalid JSON. Returning an empty dictionary..."
            )
            return {}
        except Exception as e:
            logger.error(
                f'Error reading from JSON: {str(e)}\nReturning an empty dictionary...'
            )
            return {}

    def _parse_agent_turn_num(self):
        """Get the max agent turn for current instance"""
        history_idx = 1
        self.agent_turn_num = 0
        while history_idx < len(self.trajectory) - 1:
            if (
                (self.trajectory[history_idx]['source'] == 'agent')
                and ('action' in self.trajectory[history_idx].keys())
                and (self.trajectory[history_idx]['action'] != 'system')
            ):
                self.agent_turn_num += 1
            history_idx += 1

    def _parse_string_to_dict(self, dict_string) -> dict:
        """
        Convert a string representation of a dictionary to an actual dictionary.

        Args:
            dict_string (str): String representation of a dictionary

        Returns:
            dict or None: The parsed dictionary if successful, None if failed
        """
        if not isinstance(dict_string, str):
            return None

        dict_string = dict_string.strip()

        # (1) Try JSON parsing
        try:
            return json.loads(dict_string)
        except (json.JSONDecodeError, ValueError):
            pass

        # (1) Try ast parsing
        try:
            result = ast.literal_eval(dict_string)
            if isinstance(result, dict):
                return result
            else:
                return None
        except (ValueError, SyntaxError):
            pass

        # If both methods fail, return None
        return None

    def _parse_value_from_args(self, argument_str: str, key: str) -> str:
        """
        Parse a specific key's value from argument string.

        Args:
            argument_str (str): The argument string containing key-value pairs
            key (str): The key to extract (e.g., "path", "new_str", "old_str")

        Returns:
            str: The extracted value, or empty string if not found
        """
        if not isinstance(argument_str, str) or not isinstance(key, str):
            return ''

        try:
            json_pattern = rf'"{re.escape(key)}"\s*:\s*"((?:[^"\\]|\\.)*)"`'
            match = re.search(json_pattern, argument_str, re.DOTALL)
            if match:
                value = match.group(1)
                value = (
                    value.replace('\\"', '"')
                    .replace('\\n', '\n')
                    .replace('\\t', '\t')
                    .replace('\\\\', '\\')
                )
                return value

            python_pattern = rf"'{re.escape(key)}'\s*:\s*'((?:[^'\\]|\\.)*)'"
            match = re.search(python_pattern, argument_str, re.DOTALL)
            if match:
                value = match.group(1)
                value = (
                    value.replace("\\'", "'")
                    .replace('\\n', '\n')
                    .replace('\\t', '\t')
                    .replace('\\\\', '\\')
                )
                return value

            if key in argument_str:
                parts = argument_str.split(f'"{key}"', 1)
                if len(parts) == 1:
                    parts = argument_str.split(f"'{key}'", 1)

                if len(parts) > 1:
                    remainder = parts[1].strip()

                    for quote_char in ['"', "'"]:
                        pattern = f'\\s*:\\s*{quote_char}((?:[^{quote_char}\\\\]|\\\\.)*)(?:{quote_char}|$)'
                        match = re.search(pattern, remainder, re.DOTALL)
                        if match:
                            value = match.group(1)
                            if quote_char == '"':
                                value = (
                                    value.replace('\\"', '"')
                                    .replace('\\n', '\n')
                                    .replace('\\t', '\t')
                                    .replace('\\\\', '\\')
                                )
                            else:
                                value = (
                                    value.replace("\\'", "'")
                                    .replace('\\n', '\n')
                                    .replace('\\t', '\t')
                                    .replace('\\\\', '\\')
                                )
                            return value

                    if key == 'path':
                        path_pattern = r'/[^\s,}"\']*'
                        match = re.search(path_pattern, remainder)
                        if match:
                            return match.group(0)

            return ''

        except Exception:
            return ''

    def _parse_path_from_args(self, argument_str: str) -> str:
        """
        Parse path from argument string.

        Args:
            argument_str (str): The argument string containing path information

        Returns:
            str: The extracted file path, or empty string if not found
        """
        return self._parse_value_from_args(argument_str, 'path')

    def _parse_func_names_from_str(self, code_patch) -> list:
        """
        Parse function names from the new_str code patch.

        Args:
            code_patch: Either a string (argument string) or already extracted new_str code

        Returns:
            list: List of function names found in the code patch
        """
        if not code_patch:
            return []

        try:
            # Look for "def function_name(" patterns
            # This pattern matches:
            # - "def" followed by whitespace
            # - function name (letters, numbers, underscores, also handle special methods like __len__)
            # - opening parenthesis
            func_pattern = r'\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('

            matches = re.findall(func_pattern, code_patch)

            # Remove duplicates while preserving order
            seen = set()
            unique_funcs = []
            for func_name in matches:
                if func_name not in seen:
                    seen.add(func_name)
                    unique_funcs.append(func_name)

            return unique_funcs

        except Exception:
            return []

    def _parse_loc_from_history(self, action_history: dict) -> list:
        """Parse function name and file path"""
        if not action_history:
            logger.error('No action history provided.')
            raise

        curr_turn_agent_loc = {}

        if action_history['action'] != 'edit':
            return curr_turn_agent_loc

        agent_msg_list = action_history['tool_call_metadata']['model_response'][
            'choices'
        ]
        agent_edit = {
            'create': ['file_text'],
            'str_replace': ['old_str', 'new_str'],
        }

        for cho in agent_msg_list:
            for func_dict in cho['message']['tool_calls']:
                edit_args = func_dict['function']['arguments']
                edit_dict = self._parse_string_to_dict(edit_args)

                if edit_dict:
                    curr_command = edit_dict['command']
                    agent_acts = agent_edit[curr_command]

                    file_path = edit_dict.get('path', None)
                    func_names = []

                    for act in agent_acts:
                        code_patch = edit_dict.get(act, None)
                        func_names.extend(self._parse_func_names_from_str(code_patch))
                    func_names = list(set(func_names))

                else:
                    for new_act in list(agent_edit.values()):
                        if new_act in edit_args:
                            agent_acts = new_act
                            break

                    file_path = self._parse_path_from_args(edit_args)
                    func_names = []

                    for act in agent_acts:
                        code_patch = edit_args.split(agent_acts)[-1].strip()
                        func_names.extend(self._parse_func_names_from_str(code_patch))
                    func_names = list(set(func_names))

                if file_path and len(file_path) > 0:
                    if func_names:
                        if file_path in curr_turn_agent_loc:
                            curr_turn_agent_loc[file_path].extend(func_names)
                        else:
                            curr_turn_agent_loc[file_path] = func_names
                    else:
                        curr_turn_agent_loc[file_path] = []

        return curr_turn_agent_loc

    def _add_task_success_metric(self) -> bool:
        """Task success evaluation result"""
        self.task_resolved = False
        report_pth = os.path.join(
            self.eval_dir, self.instance.instance_id, 'report.json'
        )
        eval_report = self.read_from_json(report_pth)
        if self.instance.instance_id in eval_report.keys():
            self.task_resolved = eval_report[self.instance.instance_id]['resolved']

        if self.task_resolved:
            return {
                'resolved': self.task_resolved,
                'resolve_index': self.agent_turn_num,
            }

        if self.align_failed_with_max_iter:
            return {
                'resolved': self.task_resolved,
                'resolve_index': self.max_agent_turn,
            }
        else:
            return {
                'resolved': self.task_resolved,
                'resolve_index': self.agent_turn_num,
            }

    def eval_agent_trajectory(self):
        """Evaluate agent's localization at current state"""
        if not self.trajectory:
            logger.warning(
                f'Inference trajectory for current instance (instance ID: {self.instance.instance_id}) is None, skipping localization evaluation for current instance...'
            )
            return

        # Process history
        agent_trajectory = {'final_eval': {}, 'trajectory': {}}
        turn_idx = 0
        history_idx = 1

        while history_idx < len(self.trajectory) - 2:
            history_idx += 1
            action_history = self.trajectory[history_idx]
            observ_history = self.trajectory[history_idx + 1]

            # Pass non-agent histories
            if (action_history['source'] != 'agent') or (
                'action' not in action_history.keys()
            ):
                continue

            # Parse action
            turn_idx += 1
            curr_turn_agent_loc = self._parse_loc_from_history(action_history)

            agent_trajectory['trajectory'][f'turn {turn_idx}'] = {
                'loc_eval': None,
                'loc': curr_turn_agent_loc,
                'action': {
                    'action': action_history['action'],
                    'message': action_history['message'],
                },
                'observation': None,
            }

            if 'observation' in observ_history.keys():
                agent_trajectory['trajectory'][f'turn {turn_idx}']['observation'] = {
                    'observation': observ_history['observation'],
                    'message': observ_history['message'],
                }

            # Loc eval
            if len(curr_turn_agent_loc) > 0:
                for file_key in curr_turn_agent_loc:
                    for func_name in curr_turn_agent_loc[file_key]:
                        # File loc
                        if file_key in self.gold_loc['file']:
                            if file_key not in self.agent_loc['agent loc']['file']:
                                self.agent_loc['agent loc']['file'].append(file_key)
                                self.agent_loc['turn index']['file'][
                                    self.gold_loc['file'].index(file_key)
                                ] = turn_idx
                                self.agent_loc['loc progress']['file'][
                                    self.gold_loc['file'].index(file_key)
                                ] = True

                        # Function loc
                        new_agent_loc = {'file': file_key, 'function': func_name}
                        if new_agent_loc in self.gold_loc['function']:
                            if (
                                new_agent_loc
                                not in self.agent_loc['agent loc']['function']
                            ):
                                self.agent_loc['agent loc']['function'].append(
                                    new_agent_loc
                                )
                                self.agent_loc['turn index']['function'][
                                    self.gold_loc['function'].index(new_agent_loc)
                                ] = turn_idx
                                self.agent_loc['loc progress']['function'][
                                    self.gold_loc['function'].index(new_agent_loc)
                                ] = True

            agent_trajectory['trajectory'][f'turn {turn_idx}']['loc_eval'] = (
                self.agent_loc
            )

        # Task success
        agent_trajectory['final_eval'] = {
            'total turn': self.agent_turn_num,
            'max turn': self.max_agent_turn,
            'localization': {
                'loc_acc (%)': {
                    'la_file (%)': {
                        'la_file_micro': sum(self.agent_loc['loc progress']['file'])
                        / len(self.agent_loc['loc progress']['file'])
                        * 100,
                        'la_file_macro': 100.0
                        if sum(self.agent_loc['loc progress']['file']) > 0
                        else 0.0,
                    },
                    'la_func (%)': {
                        'la_func_micro': sum(self.agent_loc['loc progress']['function'])
                        / len(self.agent_loc['loc progress']['function'])
                        * 100,
                        'la_func_macro': 100.0
                        if sum(self.agent_loc['loc progress']['function']) > 0
                        else 0.0,
                    },
                },
                'turn_idx': {
                    'file': {
                        'micro': max(self.agent_loc['turn index']['file']),
                        'macro': min(self.agent_loc['turn index']['file']),
                    },
                    'function': {
                        'micro': max(self.agent_loc['turn index']['function']),
                        'macro': min(self.agent_loc['turn index']['function']),
                    },
                },
                'details': {
                    'loc_file': self.agent_loc['loc progress']['file'],
                    'loc_func': self.agent_loc['loc progress']['function'],
                },
            },
            'task_success': None,
        }

        # Task success
        if self.eval_task_success:
            agent_trajectory['final_eval']['task_success'] = (
                self._add_task_success_metric()
            )

        # Align loc with success
        if self.task_resolved:
            if agent_trajectory['final_eval']['localization']['loc_acc (%)'] != {
                'la_file (%)': {'la_file_micro': 100.0, 'la_file_macro': 100.0},
                'la_func (%)': {'la_func_micro': 100.0, 'la_func_macro': 100.0},
            }:
                agent_trajectory['final_eval']['localization']['loc_acc (%)'] = {
                    'la_file (%)': {'la_file_micro': 100.0, 'la_file_macro': 100.0},
                    'la_func (%)': {'la_func_micro': 100.0, 'la_func_macro': 100.0},
                }
                agent_trajectory['final_eval']['localization']['details'] = {
                    'loc_file': [
                        True for i in range(len(self.agent_loc['loc progress']['file']))
                    ],
                    'loc_func': [
                        True
                        for i in range(len(self.agent_loc['loc progress']['function']))
                    ],
                }

            if self.align_failed_with_max_iter:
                for level1 in agent_trajectory['final_eval']['localization'][
                    'turn_idx'
                ]:
                    for level2 in agent_trajectory['final_eval']['localization'][
                        'turn_idx'
                    ][level1]:
                        if (
                            agent_trajectory['final_eval']['localization']['turn_idx'][
                                level1
                            ][level2]
                            > self.agent_turn_num
                        ):
                            agent_trajectory['final_eval']['localization']['turn_idx'][
                                level1
                            ][level2] = self.agent_turn_num

        # Save
        self._save_to_eval_dicts(agent_trajectory)

    def _get_instance_gt_loc(self):
        """Get ground-truth localization for current instance"""
        gt_localization = self.localizer.parse_instance_loc(self.instance)

        # Convert to dict
        gt_loc_dict = gt_localization['patch'].to_dict()
        assert gt_loc_dict['instance_id'] == self.instance.instance_id
        self.gold_loc = {
            'gt_loc_dict': gt_loc_dict['functions'],
            'file': [],
            'function': [],
        }

        for file_key in gt_loc_dict['functions']:
            if len(gt_loc_dict['functions'][file_key]) == 0:
                continue

            # File
            if file_key not in self.gold_loc['file']:
                self.gold_loc['file'].append(f'{self.sandbox_root}/{file_key}')

            # Function
            for func_name in gt_loc_dict['functions'][file_key]:
                new_gt = {
                    'file': f'{self.sandbox_root}/{file_key}',
                    'function': func_name,
                }
                self.gold_loc['function'].append(new_gt)

        # Init agent loc accordingly
        init_turn = (
            self.max_agent_turn
            if self.align_failed_with_max_iter
            else self.agent_turn_num
        )
        self.agent_loc['gold loc'] = {
            'file': self.gold_loc['file'],
            'function': self.gold_loc['function'],
        }
        self.agent_loc['turn index']['file'] = [
            init_turn for i in range(len(self.gold_loc['file']))
        ]
        self.agent_loc['turn index']['function'] = [
            init_turn for i in range(len(self.gold_loc['function']))
        ]
        self.agent_loc['loc progress']['file'] = [
            False for i in range(len(self.gold_loc['file']))
        ]
        self.agent_loc['loc progress']['function'] = [
            False for i in range(len(self.gold_loc['function']))
        ]

    def instance_loc_eval(
        self,
        instance: pd.Series = None,
        repo_root: str = None,
        trajectory: list = None,
        infer_cost: dict = None,
    ):
        if instance is None:
            logger.error(
                'No instance provided. Skipping current localization evaluation...'
            )
        if trajectory is None:
            logger.error(
                f'No inference trajectory provided for current instance with ID: {instance.instance_id}'
            )
        if infer_cost is None:
            logger.error(
                f'No inference accumulated cost for current instance with ID: {instance.instance_id}'
            )

        # Init
        self._init_config()
        self.cost_summary['details'][instance.instance_id] = infer_cost

        # Update current instance
        self.instance = instance
        self.trajectory = trajectory
        self.sandbox_root = repo_root

        # Max turn
        self._parse_agent_turn_num()

        # GT loc
        self._get_instance_gt_loc()

        # Loc evaluation
        self.eval_agent_trajectory()


def swe_data_loader(args):
    """
    Loading SWE-Bench data.

    Args:
        args: Main arguments.
    """
    dataset = load_dataset(args.dataset, split=args.split)
    swe_bench_tests = filter_dataset(dataset.to_pandas(), 'instance_id')
    logger.info(
        f'Loaded dataset {args.dataset} with split {args.split}: {len(swe_bench_tests)} tasks'
    )
    if 'SWE-Gym' in args.dataset:
        with open(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'split',
                'swegym_verified_instances.json',
            ),
            'r',
        ) as f:
            swegym_verified_instances = json.load(f)
            swe_bench_tests = swe_bench_tests[
                swe_bench_tests['instance_id'].isin(swegym_verified_instances)
            ]
        logger.info(
            f'{len(swe_bench_tests)} tasks left after filtering for SWE-Gym verified instances'
        )

    instances = prepare_dataset(swe_bench_tests, args.swe_output_file, -1)
    return instances


def infer_data_loader(args):
    """
    Load instance IDs.

    Args:
        args: Main arguments.

    Returns:
        list: A list of instance IDs (strings) extracted from JSON filenames
              in the histories directory.

    Raises:
        FileNotFoundError: If the histories directory doesn't exist.
        AttributeError: If args doesn't have a 'infer_dir' attribute.
    """
    infer_output_filepath = os.path.join(args.infer_dir, 'output.jsonl')

    infer_outputs = []
    with open(infer_output_filepath, 'r') as file:
        for line_num, line in enumerate(file, 1):
            line = line.strip()
            if line:
                try:
                    json_obj = json.loads(line)
                    infer_outputs.append(json_obj)
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Error parsing JSON on line {line_num} in '{infer_output_filepath}': {str(e)}"
                    )
                    continue

    return infer_outputs


def infer_cost_calculator(args):
    """
    Calculate total and average costs from metric JSON files with detailed output.

    Args:
        args: Main arguments.

    Returns:
        dict: A dictionary containing:
              - 'total_cost': Sum of all accumulated costs
              - 'average_cost': Average cost per JSON file
              - 'file_count': Number of JSON files processed
              - 'individual_costs': List of individual costs (optional)
    """
    metrics_dir = os.path.join(args.infer_dir, 'metrics')

    if not os.path.exists(metrics_dir):
        raise FileNotFoundError(f'Metrics directory not found: {metrics_dir}')

    individual_costs = []

    for filename in os.listdir(metrics_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(metrics_dir, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    metric_data = json.load(file)

                if 'accumulated_cost' not in metric_data:
                    raise KeyError(f"'accumulated_cost' not found in {filename}")

                cost = float(metric_data['accumulated_cost'])
                individual_costs.append(cost)

            except (json.JSONDecodeError, ValueError, TypeError, IOError) as e:
                logger.warning(f'Warning: Error processing {filename}: {e}')
                continue

    if not individual_costs:
        raise ValueError('No valid JSON files found in the metrics directory')

    total_cost = sum(individual_costs)
    average_cost = total_cost / len(individual_costs)

    return {
        'total_cost': total_cost,
        'average_cost': average_cost,
        'file_count': len(individual_costs),
        'individual_costs': individual_costs,
    }


if __name__ == '__main__':
    """Main function for localization evaluation"""
    parser = argparse.ArgumentParser(
        description='Localization evaluation on SWE-Bench.'
    )

    parser.add_argument(
        '--infer-dir',
        type=str,
        default=None,
        help='Directory containing model inference outputs',
    )
    parser.add_argument(
        '--dataset', type=str, default=None, help='SWE-Bench dataset version'
    )
    parser.add_argument(
        '--split', type=str, default=None, help='SWE-Bench dataset split selection'
    )
    parser.add_argument(
        '--max-infer-turn',
        type=int,
        default=None,
        help='Max number of turns allowed for coding agent.',
    )
    parser.add_argument(
        '--align-with-max',
        type=str,
        choices=['true', 'false'],
        default='true',
        help='Whether to align failed instances with max iteration count (true/false)',
    )

    args = parser.parse_args()

    # Convert args.align_with_max str to bool
    args.align_with_max = args.align_with_max.lower() == 'true'

    # Eval infer and loc
    args.save_dir = f'{args.infer_dir}/loc_eval'
    os.makedirs(args.save_dir, exist_ok=True)
    args.eval_dir = f'{args.infer_dir}/eval_outputs'
    if not os.path.isdir(args.eval_dir):
        args.eval_dir = None

    # SWE-Bench
    args.swe_output_file = os.path.join(args.save_dir, 'swe_dataset.json')

    # Load swebench data
    swe_instances = swe_data_loader(args)

    # Load inference data
    infer_outputs = infer_data_loader(args)

    # Loc eval
    processed_instances = []
    loc_eval_results = {}
    loc_evaluator = LocEvaluator(args)

    for infer_idx, infer_instance in tqdm(
        enumerate(infer_outputs), total=len(infer_outputs), desc='Processing instances'
    ):
        instance_id = infer_instance['instance_id']
        swe_instance = swe_instances.query(f"instance_id == '{instance_id}'").iloc[0]
        assert instance_id == swe_instance.instance_id

        processed_instances.append(instance_id)
        upload_instruction = infer_instance['instruction']
        repo_root = (
            upload_instruction.split('<uploaded_files>')[1]
            .split('</uploaded_files>')[0]
            .strip()
        )
        curr_trajectory = infer_instance['history']
        curr_cost = infer_instance['metrics']['accumulated_cost']
        loc_evaluator.instance_loc_eval(
            swe_instance, repo_root, curr_trajectory, curr_cost
        )

    logger.info(
        f'\n[Inference Data Summary]'
        f'\n{" " * 4} - Total cost:   $ {loc_evaluator.cost_summary["total_cost"]}'
        f'\n{" " * 4} - Average cost: $ {loc_evaluator.cost_summary["avg_cost"]}'
        f'\n{" " * 4} - Number of Instances: {len(processed_instances)}'
    )
