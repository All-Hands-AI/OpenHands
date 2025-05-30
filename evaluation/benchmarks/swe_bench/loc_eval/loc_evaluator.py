import os
import re
import json
import argparse
import pandas as pd
from collections import Counter
from datasets import load_dataset
from typing import Dict, List, Any, Tuple, Optional

from evaluation.utils.shared import prepare_dataset
from evaluation.benchmarks.swe_bench.run_infer import filter_dataset
from openhands.core.logger import openhands_logger as logger


class LocEvaluator:
    def __init__(self, args, cost_summary: Dict = None):
        """
        Localization evaluation.

        Args:
            args: all main arguments
        """
        # Config
        self.args = args
        self.eval_dir = args.eval_dir
        self.eval_task_success = self._check_if_eval_success()
        self.sandbox_root = "/workspace/"
        self.agent_turn_num = 100
        self.max_agent_turn = args.max_infer_turn

        # Data
        self.instance = None
        self.gold_loc = None
        self.trajectory = None

        # Localization
        self.loc_file = False
        self.loc_file_idx = None
        self.loc_func = False
        self.loc_func_idx = None

        self.curr_turn_loc_file = False
        self.curr_turn_loc_func = False

        # Task success tracking
        self.task_success = False

        # Cost metric
        self.cost_summary = cost_summary

        # Save
        self.save_dir = os.path.join(args.output_dir, "loc_eval_results")
        self._init_dir(self.save_dir)
        self.eval_dict = {"final_eval": {}, "trajectory": {}}
        self.all_eval_results = {}
        self.overall_eval = {}

    def _init_config(self):
        # Data
        self.instance = None
        self.gold_loc = None
        self.trajectory = None
        self.agent_turn_num = 100

        # Localization
        self.loc_file = False
        self.loc_file_idx = None
        self.loc_func = False
        self.loc_func_idx = None
        
        self.curr_turn_loc_file = False
        self.curr_turn_loc_func = False

        # Task success tracking
        self.task_success = False

        # Save
        self.save_dir = os.path.join(args.output_dir, "loc_eval_results")
        self._init_dir(self.save_dir)
        self.eval_dict = {"final_eval": {}, "trajectory": {}}

    def _init_dir(self, directory_path):
        """
        Check if a directory exists and create it if it doesn't.
        
        Args:
            directory_path (str): Path to the directory to check/create
            
        Returns:
            bool: True if directory already existed, False if it was created
        """
        if os.path.exists(directory_path):
            # Check if it's actually a directory and not a file
            if not os.path.isdir(directory_path):
                raise NotADirectoryError(f"Path exists but is not a directory: {directory_path}")
            return True
        else:
            # Create the directory and any necessary parent directories
            os.makedirs(directory_path)
            return False

    def _check_if_eval_success(self):
        """Check if post-evaluation outputs exist"""
        if not os.path.isdir(self.eval_dir):
            return False
        else:
            return True

    def _parse_loc_ground_truth(self, trajectory: List) -> Dict:
        """Get ground-truth localization"""
        # Parse localization ground truth
        for line in self.instance.patch.split('\n'):
            # File path
            if 'diff --git' in line:
                gt_file = line.replace('diff --git a/', self.sandbox_root).strip().split(' ')[0].strip()
            # Function name
            if '@@ def' in line:
                gt_func = line.split('@@ def')[-1].split('(')[0].strip()

        # Adapt root path to current task
        for idx in range(1, len(trajectory)):
            if trajectory[idx]["source"] == "user":
                user_input = trajectory[idx]["message"]
                repo_root = user_input.split("<uploaded_files>")[1].split("</uploaded_files>")[0].strip()
                break
        current_root = self.sandbox_root.rstrip("/")
        gt_file = gt_file.replace(current_root, repo_root)

        # Log parsing results
        logger.info(f"Parsed ground truth: file={gt_file}, function={gt_func}")
        
        return {'file': gt_file, 'function': gt_func}

    def _compute_avg_over_all(self):
        """Compute average loc evaluations over all instances"""
        la_file, la_func, resolve_rate = 0, 0, 0
        avg_file_idx, avg_func_idx, avg_sr_idx = 0, 0, 0
        total_instance_num = len(self.all_eval_results.keys())

        for instance_id in self.all_eval_results.keys():
            curr_eval_result = self.all_eval_results[instance_id]["final_eval"]

            if curr_eval_result["file"]:
                la_file += 1
                avg_file_idx += curr_eval_result["file_idx"]
            else:
                avg_file_idx += self.max_agent_turn

            if curr_eval_result["func"]:
                la_func += 1
                avg_func_idx += curr_eval_result["func_idx"]
            else:
                avg_func_idx += self.max_agent_turn

            if curr_eval_result["task_success"]:
                resolve_rate += 1
                avg_sr_idx += curr_eval_result["task_success_idx"]
            else:
                avg_sr_idx += self.max_agent_turn

        # Average
        la_file = la_file / total_instance_num * 100 
        la_func = la_func / total_instance_num * 100
        resolve_rate = resolve_rate / total_instance_num * 100
        avg_file_idx = avg_file_idx / total_instance_num
        avg_func_idx = avg_func_idx / total_instance_num
        avg_sr_idx = avg_sr_idx / total_instance_num

        # Cost metric
        cost_metric = {
            "total_cost": cost_summary["total_cost"],
            "average_cost": cost_summary["average_cost"],
        }

        self.overall_eval = {
            "la_file (%)": la_file,
            "la_func (%)": la_func,
            "resolve_rate (%)": resolve_rate,
            "loc_file_idx (turn idx)": avg_file_idx,
            "loc_func_idx (turn idx)": avg_func_idx,
            "success_idx (turn idx)": avg_sr_idx,
            "max_turn_limit": self.max_agent_turn,
            "total_instance_num": total_instance_num,
            "cost_summary": cost_metric,
        }
        self._write_to_json(self.overall_eval, "overall_eval.json")

    def _save_to_eval_dicts(self, agent_trajectory: Dict):
        # Current instancec
        self.eval_dict["final_eval"] = {
            'file': self.loc_file,
            'file_idx': self.loc_file_idx if self.loc_file else None,
            'func': self.loc_func,
            'func_idx': self.loc_func_idx if self.loc_func else None,
            'task_success': self.task_success,
            'task_success_idx': self.agent_turn_num if self.task_success else None,
            'total_turn': self.agent_turn_num,
        }
        self.eval_dict["trajectory"] = agent_trajectory
        self._write_to_json(self.eval_dict, f"loc__instance_{self.instance.instance_id}.json")

        # All instances
        self.all_eval_results[self.instance.instance_id] = self.eval_dict
        self._write_to_json(self.all_eval_results, "all_loc_evals.json")

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
            logger.info(f"Saved localization evaluation to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error writing to JSON: {str(e)}")
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
            logger.warning(f"Warning: File '{file_path}' not found. Returning an empty dictionary...")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Error: File '{file_path}' contains invalid JSON. Returning an empty dictionary...")
            return {}
        except Exception as e:
            logger.error(f"Error reading from JSON: {str(e)}\nReturning an empty dictionary...")
            return {}

    def _parse_agent_turn_num(self):
        """Get the max agent turn for current instance"""
        history_idx = 1  # skip system prompt
        self.agent_turn_num = 0
        while history_idx < len(self.trajectory):
            if (self.trajectory[history_idx]["source"] == "agent") and ("action" in self.trajectory[history_idx].keys()):
                self.agent_turn_num += 1
            history_idx += 1

        # Init as max
        self.loc_file_idx = self.agent_turn_num
        self.loc_func_idx = self.agent_turn_num

    def _parse_string_to_dict(self, dict_string):
        """
        Parse a string representation of a dictionary to a real dictionary.
        
        Args:
            dict_string (str): String representation of a dictionary
            
        Returns:
            dict: Parsed dictionary object
            
        Raises:
            json.JSONDecodeError: If the string is not valid JSON
            TypeError: If input is not a string
        """
        if not isinstance(dict_string, str):
            raise TypeError("Input must be a string")
        
        try:
            return json.loads(dict_string)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON string: {e}")

    def _extract_function_names(self, code_string):
        """
        Extract all function names from a Python code string with better handling
        of edge cases like decorators and indentation.
        
        Args:
            code_string (str): String containing Python code
        
        Returns:
            list: List of function names found in the code
        """
        # Pattern that handles:
        # - Optional decorators (@decorator)
        # - Optional indentation (for methods in classes)
        # - def keyword
        # - function name
        # - opening parenthesis
        pattern = r'(?:^|\n)(?:\s*@.*\n)*\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        
        function_names = re.findall(pattern, code_string, re.MULTILINE)
        
        return function_names

    def _parse_loc_from_history(self, action_history: Dict) -> Tuple[str, str]:
        """Parse function name and file path"""
        if not action_history:
            logger.error("No action history provided.")
            raise
        
        func_names = None
        file_path = None

        if "tool_call_metadata" in action_history.keys():
            # Get argument
            argument = action_history["tool_call_metadata"]["model_response"]["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
            argument_dict = self._parse_string_to_dict(argument)
            
            # Function
            agent_patch = argument
            if "new_str" in argument_dict.keys():  # replace
                agent_patch = argument_dict["new_str"].strip()
            elif "file_text" in argument_dict.keys():  # create
                agent_patch = argument_dict["file_text"].strip()
            func_names = self._extract_function_names(agent_patch)
            
            # File            
            if "path" in argument_dict.keys():
                file_path = argument_dict["path"].strip()
            else:
                for piece in argument.split(" "):
                    if self.sandbox_root in piece:
                        file_path = piece.strip()
                        break

            return func_names, file_path

        elif "extras" in action_history.keys():
            if "path" in action_history["extras"].keys():
                file_path = action_history["extras"]["path"].strip()

            elif "command" in action_history["extras"].keys():
                command = action_history["extras"]["command"]
                for piece in command.split(" "):
                    if self.sandbox_root in piece:
                        file_path = piece.strip()
                        break

            return None, file_path

        elif "args" in action_history.keys():
            if "path" in action_history["args"].keys():
                file_path = action_history["args"]["path"].strip()

            elif "command" in action_history["args"].keys():
                command = action_history["args"]["command"]
                for piece in command.split(" "):
                    if self.sandbox_root in piece:
                        file_path = piece.strip()
                        break

            return None, file_path     

        else:
            return None, None

    def _add_task_success_metric(self) -> bool:
        """Task success evaluation result"""
        self.task_success = False
        report_pth = os.path.join(self.eval_dir, self.instance.instance_id, "report.json")
        eval_report = self.read_from_json(report_pth)
        if self.instance.instance_id in eval_report.keys():
            self.task_success = eval_report[self.instance.instance_id]["resolved"]
        return self.task_success

    def eval_agent_trajectory(self):
        """Evaluate agent's localization at current state"""
        if not self.trajectory:
            logger.warning(f"Inference trajectory for current instance (instance ID: {self.instance.instance_id}) is None, skipping localization evaluation for current instance...")
            return
        
        # Process history
        agent_trajectory = {}
        turn_idx = 0
        history_idx = 0
        
        while history_idx < len(self.trajectory)-2:
            history_idx += 1  # skip system prompt
            logger.info(f"Progress: {history_idx}-{history_idx+1} / {len(self.trajectory)-1}")
            
            action_history = self.trajectory[history_idx]
            observ_history = self.trajectory[history_idx+1]

            # Pass non-agent histories
            if (action_history["source"] != "agent") or ("action" not in action_history.keys()):
                continue
            
            # Parse action
            turn_idx += 1
            func_names, file_path = self._parse_loc_from_history(action_history)
            agent_trajectory[f"turn {turn_idx}"] = {
                "loc_eval": None,
                "loc": {
                    "function": func_names,
                    "file": file_path,
                },
                "action": {
                    "action": action_history["action"],
                    "message": action_history["message"],
                    "argument": action_history["tool_call_metadata"]["model_response"]["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] \
                        if "tool_call_metadata" in action_history.keys() else None,
                },
                "observation": None
            }

            if "observation" in observ_history.keys():
                agent_trajectory[f"turn {turn_idx}"]["observation"] = {
                    "observation": observ_history["observation"],
                    "message": observ_history["message"],
                    "argument": observ_history["tool_call_metadata"]["model_response"]["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] \
                        if "tool_call_metadata" in observ_history.keys() else None,
                }
            
            # Loc eval
            if action_history["action"] == "edit":
                # Function
                self.curr_turn_loc_func = self.gold_loc["function"] in func_names

                # File
                self.curr_turn_loc_file = file_path == self.gold_loc["file"]

                if self.curr_turn_loc_file:
                    if not self.loc_file:
                        self.loc_file = True
                        self.loc_file_idx = turn_idx
                if self.curr_turn_loc_func:
                    if not self.loc_func:
                        self.loc_func = True
                        self.loc_func_idx = turn_idx

                        if not self.loc_file:
                            self.loc_file = True
                            self.loc_file_idx = turn_idx

                agent_trajectory[f"turn {turn_idx}"]["loc_eval"] = {
                    "loc_file": self.curr_turn_loc_file,
                    "loc_func": self.curr_turn_loc_func,
                }

            # Show progress
            logger.info(
                f"Progress Debugging:"
                f"\n[Turn {turn_idx} - Agent Action] {action_history['action']}"
                f"\n[Turn {turn_idx} - Localization] file = {file_path}, function = {func_names}"
                f"\n[Turn {turn_idx} - Gold Localiz] file = {self.gold_loc['file']}, function = {self.gold_loc['function']}"
                f"\n[Turn {turn_idx} - Current Loc]  file = {self.curr_turn_loc_file}, function = {self.curr_turn_loc_func}"
                f"\n[Turn {turn_idx} - Overall Loc]  file = {self.loc_file}, function = {self.loc_func}"
            )

        # Task success
        if self.eval_task_success:
            agent_trajectory["task_eval"] = {
                "turn_num": turn_idx,
                "loc_func": self.loc_func,
                "loc_file": self.loc_file,
                "task_success": self._add_task_success_metric(),
            }
            logger.info(f"\n[Turn {turn_idx} - Task Success] {self.task_success}")

        # Align loc with success
        if self.task_success:
            if self.loc_func == False:
                self.loc_file = True
                self.loc_func = True
                self.loc_file_idx = turn_idx
                self.loc_file_idx = turn_idx
                agent_trajectory["task_eval"] = {
                    "turn_num": turn_idx,
                    "loc_func": self.loc_func,
                    "loc_file": self.loc_file,
                    "task_success": self.task_success,
                }

        # Save
        self._save_to_eval_dicts(agent_trajectory)

    def instance_loc_eval(self, instance: pd.Series = None, trajectory: List = None):
        if instance is None:
            logger.error("No instance provided! Skipping current localization evaluation...")
        if trajectory is None:
            logger.error(f"No inference trajectory provided for current instance with ID: {instance.instance_id}")

        # Init
        self._init_config()

        # Update current instance
        self.instance = instance
        self.trajectory = trajectory
        self.gold_loc = self._parse_loc_ground_truth(trajectory)
        
        # Log initialization
        logger.info(f"LocEvaluator initialized for instance {instance.instance_id}")
        logger.info(f"Gold localization: file = {self.gold_loc['file']}, function = {self.gold_loc['function']}")

        # Max turn
        self._parse_agent_turn_num()

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

    # Run evaluation in iterative mode
    instances = prepare_dataset(swe_bench_tests, args.output_file, -1)
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
    instances = []
    
    # Construct the path to the histories directory
    histories_dir = os.path.join(args.infer_dir, "histories")
    
    # Check if the histories directory exists
    if not os.path.exists(histories_dir):
        raise FileNotFoundError(f"Histories directory not found: {histories_dir}")
    
    # Iterate through all files in the histories directory
    for filename in os.listdir(histories_dir):
        # Check if the file is a JSON file
        if filename.endswith('.json'):
            # Extract the instance ID (filename without extension)
            instance_id = os.path.splitext(filename)[0].replace("instance_", "").strip()
            instances.append(instance_id)
    
    return instances

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
    metrics_dir = os.path.join(args.infer_dir, "metrics")
    
    if not os.path.exists(metrics_dir):
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
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
                logger.warning(f"Warning: Error processing {filename}: {e}")
                continue
    
    if not individual_costs:
        raise ValueError("No valid JSON files found in the metrics directory")
    
    total_cost = sum(individual_costs)
    average_cost = total_cost / len(individual_costs)
    
    return {
        'total_cost': total_cost,
        'average_cost': average_cost,
        'file_count': len(individual_costs),
        'individual_costs': individual_costs
    }


if __name__ == '__main__':
    """Main function for localization evaluation"""
    parser = argparse.ArgumentParser(description="Localization evaluation on SWE-Bench.")

    parser.add_argument(
        "--infer-dir",
        type=str,
        default="./llm.claude-3-5-haiku1/litellm_proxy_claude-3-5-haiku-20241022",
        help="Directory containing model inference outputs"
    )
    parser.add_argument(
        "--eval-dir",
        type=str,
        default="./evaluation/evaluation_outputs/outputs/princeton-nlp__SWE-bench_Verified-test/CodeActAgent/claude-3-5-haiku-20241022_maxiter_20_N_v0.38.0-no-hint-run_1/eval_outputs",
        help="Directory containing inference evaluation outputs"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./evaluation/benchmarks/swe_bench/loc_eval/saves",
        help="Output directory to save eval results"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="princeton-nlp/SWE-bench_Verified",
        help="SWE-Bench dataset version"
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="SWE-Bench dataset split selection"
    )
    parser.add_argument(
        "--max-infer-turn",
        type=int,
        default=20,
        help="Max number of turns allowed for coding agent."
    )

    args = parser.parse_args()

    # SWE-Bench
    args.output_file = os.path.join(args.output_dir, "swe_dataset.json")

    # Load swebench data
    swe_instances = swe_data_loader(args)

    # Load inference data
    instances = infer_data_loader(args)

    # Show costs
    cost_summary = infer_cost_calculator(args)
    if len(instances) != cost_summary['file_count']:
        logger.error(
            f"\n[ERROR] Instance number mismatch between histories and metrics:"
            f"\n{' ' * 4} - Number of Instance histories: {cost_summary['file_count']}"
            f"\n{' ' * 4} - Number of Instance metrics:   {len(instances)}"
        )
        raise

    # Loc eval
    processed_instances = []
    loc_eval_results = {}
    loc_evaluator = LocEvaluator(args, cost_summary)
    for swe_index, swe_instance in swe_instances.iterrows():
        # If completed processing all inference instances
        if Counter(processed_instances) == Counter(instances):
            break
        
        # Process inference data
        if swe_instance.instance_id in instances:
            logger.warning(f"instances: {instances}, swe_instance.instance_id: {swe_instance.instance_id}")
            processed_instances.append(swe_instance.instance_id)

            # Read trajectory
            curr_trajectory_pth = os.path.join(args.infer_dir, "histories", f"instance_{swe_instance.instance_id}.json")
            curr_trajectory = loc_evaluator.read_from_json(curr_trajectory_pth)
            loc_evaluator.instance_loc_eval(swe_instance, curr_trajectory)

    # Cost metric
    logger.info(
        f"\n[Inference Data Summary]"
        f"\n{' ' * 4} - Total cost:   $ {cost_summary['total_cost']}"
        f"\n{' ' * 4} - Average cost: $ {cost_summary['average_cost']}"
        f"\n{' ' * 4} - Number of Instances: {len(instances)}"
    )
    