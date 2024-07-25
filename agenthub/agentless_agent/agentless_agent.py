import os
import pickle
import subprocess
from collections import Counter
from typing import Any, Dict, List, TypedDict

from opendevin.controller.agent import Agent
from opendevin.controller.state.state import State
from opendevin.core.logger import opendevin_logger as logger
from opendevin.events.action import (
    Action,
    AgentFinishAction,
    IPythonRunCellAction,
)
from opendevin.events.observation import (
    Observation,
)
from opendevin.llm.llm import LLM
from opendevin.runtime.plugins import (
    AgentSkillsRequirement,
    JupyterRequirement,
    PluginRequirement,
)

"""
FIXME: There are a few problems this surfaced
* FileWrites seem to add an unintended newline at the end of the file
* Browser not working
"""

ActionObs = TypedDict(
    'ActionObs', {'action': Action, 'observations': list[Observation]}
)

BACKEND = 'openai'
MODEL_NAME = 'gpt-4o-mini-2024-07-18'
MAX_TOKENS = 300
MAX_CONTEXT_LENGTH = 128000
TOP_N = 3
CONTEXT_WINDOW = 10
ADD_SPACE = False
STICKY_SCROLL = False
NO_LINE_NUMBER = False
TEMPERATURE = 0.8
NUM_SAMPLES = 4
LOC_INTERVAL = True
FINE_GRAIN_LOC_ONLY = False
COT = True
DIFF_FORMAT = True
STOP_AT_N_UNIQUE_VALID_SAMPLES = -1
MAX_SAMPLES = 20
SKIP_GREEDY = False


def _parse_model_return_lines(content: str) -> list[str]:
    if content:
        return content.strip().split('\n')
    return ['']


class AgentlessAgent(Agent):
    VERSION = '0.0.1'
    """
    AgentlessAgent
    """
    sandbox_plugins: list[PluginRequirement] = [
        # NOTE: AgentSkillsRequirement need to go before JupyterRequirement, since
        # AgentSkillsRequirement provides a lot of Python functions,
        # and it needs to be initialized before Jupyter for Jupyter to use those functions.
        AgentSkillsRequirement(),
        JupyterRequirement(),
    ]

    # action_parser = CodeActResponseParser()
    def __init__(self, llm: LLM):
        super().__init__(llm)
        self.steps: list[ActionObs] = []

    def step(self, state: State) -> Action:
        """
        Performs the Agentless localization and repair

        Parameters:
        - state (State): used to get updated info

        Returns:
        - AgentFinishAction() - end the interaction
        """

        if isinstance(state.history.get_last_action(), IPythonRunCellAction):
            logger.info('Last action ran some code!')
            return AgentFinishAction()

        #         final_patch = """diff --git a/astropy/modeling/separable.py b/astropy/modeling/separable.py
        # --- a/astropy/modeling/separable.py
        # +++ b/astropy/modeling/separable.py
        # @@ -242,7 +242,7 @@ def _cstack(left, right):
        #          cright = _coord_matrix(right, 'right', noutp)
        #      else:
        #          cright = np.zeros((noutp, right.shape[1]))
        # -        cright[-right.shape[0]:, -right.shape[1]:] = 1
        # +        cright[-right.shape[0]:, -right.shape[1]:] = right

        #      return np.hstack([cleft, cright])

        # """
        # return IPythonRunCellAction(code=f"apply_git_patch('''{final_patch}''')")

        # Use the above to test the apply_git_patch function

        self.install_agentless_libraries()
        self.copy_directory_to_local()

        problem_statement = state.history.get_last_user_message()
        logger.info('PROBLEM STATEMENT')
        logger.info(problem_statement)

        workspace_path = self.get_subfolder_path(
            '/srv/home/soren/OpenDevin/workspace/_eval_workspace/workspace'
        )

        repo_structure = self.retrieve_structure(workspace_path)
        logger.info('REPO STRUCTURE')
        for key in repo_structure.keys():
            logger.info(key)
            for key2 in repo_structure[key]:
                logger.info(f'    {key2}')

        file_localization = self.agentless_file_localization(
            problem_statement, repo_structure
        )
        logger.info('FILE LOCALIZATION')
        for file in file_localization:
            logger.info(file)

        related_localization = self.agentless_related_localization(
            problem_statement, repo_structure, file_localization
        )
        logger.info('RELATED LOCALIZATION')
        for rel_loc in related_localization:
            logger.info(rel_loc)

        line_localization = self.agentless_line_level_localization(
            file_localization, related_localization, problem_statement, repo_structure
        )
        logger.info('LINE LOCALIZATION')
        logger.info(line_localization)

        repair_outputs, original_file_contents, file_names = self.agentless_repair(
            repo_structure, file_localization, line_localization, problem_statement
        )
        logger.info('REPAIR OUTPUTS')
        for i, repair in enumerate(repair_outputs):
            logger.info(f'Repair {i}')
            logger.info(repair)

        processed_patches = self.agentless_post_process_repair(
            file_localization,
            line_localization,
            original_file_contents,
            file_names,
            repair_outputs,
        )
        logger.info('PROCESSED PATCHES')
        for i, patch in enumerate(processed_patches):
            logger.info(f'PATCH {i}')
            logger.info(patch[1])
        final_patch = most_frequent_string(processed_patches)
        logger.info('FINAL PATCH')
        logger.info(final_patch)

        return IPythonRunCellAction(code=f"apply_git_patch('''{final_patch}''')")

    def search_memory(self, query: str) -> list[str]:
        return []

    def install_agentless_libraries(self):
        import sys

        def install_libcst():
            # try:
            #     # Try to import the package. If it's already installed, this will succeed.
            #     import libcst

            #     print('libcst is already installed.')
            # except ImportError:
            # If the import fails, it means the package is not installed.
            print('libcst not found. Installing...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'libcst'])
            print('libcst installed successfully.')

        install_libcst()

    def copy_directory_to_local(self):
        def get_most_recent_container_id(image_name):
            try:
                result = subprocess.run(
                    [
                        'docker',
                        'ps',
                        '-a',
                        '--filter',
                        f'ancestor={image_name}',
                        '--format',
                        '{{.ID}}',
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                container_ids = result.stdout.strip().split('\n')
                return container_ids[0] if container_ids else None
            except subprocess.CalledProcessError as e:
                print(f'Error while fetching container ID: {e}')
                return None

        def copy_workspace_from_container(container_id, destination_path):
            try:
                subprocess.run(
                    ['docker', 'cp', f'{container_id}:/workspace', destination_path],
                    check=True,
                )
                print(f'Successfully copied workspace to {destination_path}')
            except subprocess.CalledProcessError as e:
                print(f'Error while copying workspace: {e}')

        image_name = 'od_sandbox:ghcr.io___opendevin___eval-swe-bench__full-v1.2.1'
        destination_path = '/srv/home/soren/OpenDevin/workspace/_eval_workspace'

        container_id = get_most_recent_container_id(image_name)
        if container_id:
            print(f'Most recent container ID: {container_id}')
            copy_workspace_from_container(container_id, destination_path)
        else:
            print(f'No container found for image: {image_name}')

    def get_subfolder_path(self, parent_folder_path):
        try:
            entries = os.listdir(parent_folder_path)
            for entry in entries:
                full_path = os.path.join(parent_folder_path, entry)
                if os.path.isdir(full_path):
                    return full_path
            return None  # If no folders are found, return None
        except Exception as e:
            print(f'An error occurred: {e}')
            return None

    def retrieve_structure(self, directory_path):
        """Create the structure of the repository directory by parsing Python files.

        If a pickled structure exists, load it. Otherwise, create it and pickle the result.

        :param directory_path: Path to the repository directory.
        :return: A dictionary representing the structure.
        """

        from Agentless.agentless.util.preprocess_data import (
            filter_none_python,
            filter_out_test_files,
        )
        from Agentless.get_repo_structure.get_repo_structure import (
            parse_python_file,
        )

        pickle_file = os.path.join(directory_path, 'repo_structure.pkl')

        # Try to load the pickle file if it exists
        if os.path.isfile(pickle_file):
            with open(pickle_file, 'rb') as pf:
                return pickle.load(pf)

        # Proceed to create the structure if pickle file doesn't exist
        structure: Dict[str, Any] = {}

        for root, _, files in os.walk(directory_path):
            repo_name = os.path.basename(directory_path)
            relative_root = os.path.relpath(root, directory_path)

            if relative_root == '.':
                relative_root = repo_name

            curr_struct = structure
            for part in relative_root.split(os.sep):
                if part not in curr_struct:
                    curr_struct[part] = {}
                curr_struct = curr_struct[part]

            for file_name in files:
                if file_name.endswith('.py'):
                    file_path = os.path.join(root, file_name)
                    class_info, function_names, file_lines = parse_python_file(
                        file_path
                    )
                    curr_struct[file_name] = {
                        'classes': class_info,
                        'functions': function_names,
                        'text': file_lines,
                    }
                else:
                    curr_struct[file_name] = {}

        filter_none_python(structure)
        filter_out_test_files(structure)

        return structure

    def agentless_file_localization(self, problem_statement, structure):
        from Agentless.agentless.fl.FL import LLMFL
        from Agentless.agentless.util.preprocess_data import (
            correct_file_paths,
            get_full_file_paths_and_classes_and_functions,
            show_project_structure,
        )

        message = LLMFL.obtain_relevant_files_prompt.format(
            problem_statement=problem_statement,
            structure=show_project_structure(structure).strip(),
        ).strip()
        print(f'prompting with message:\n{message}')
        print('=' * 80)

        raw_output = self.llm.completion(
            model=MODEL_NAME,
            messages=[{'content': message, 'role': 'user'}],
            temperature=0,
            max_tokens=MAX_TOKENS,
        )['choices'][0]['message']['content']
        model_found_files = _parse_model_return_lines(raw_output)

        files, classes, functions = get_full_file_paths_and_classes_and_functions(
            structure
        )

        # Never match partial paths for consistency with main Agentless results
        found_files = correct_file_paths(model_found_files, files, False)
        print(found_files)

        return found_files

    def agentless_related_localization(self, problem_statement, structure, found_files):
        from Agentless.agentless.fl.FL import LLMFL
        from Agentless.agentless.util.api_requests import (
            num_tokens_from_messages,
        )
        from Agentless.agentless.util.compress_file import get_skeleton
        from Agentless.agentless.util.postprocess_data import (
            extract_code_blocks,
            extract_locs_for_files,
        )
        from Agentless.agentless.util.preprocess_data import (
            get_repo_files,
        )

        if len(found_files) != 0:
            file_names = found_files[:TOP_N]
        file_contents = get_repo_files(structure, file_names)
        compressed_file_contents = {
            fn: get_skeleton(code) for fn, code in file_contents.items()
        }
        contents = [
            LLMFL.file_content_in_block_template.format(file_name=fn, file_content=code)
            for fn, code in compressed_file_contents.items()
        ]
        file_contents = ''.join(contents)
        template = (
            LLMFL.obtain_relevant_functions_and_vars_from_compressed_files_prompt_more
        )
        message = template.format(
            problem_statement=problem_statement, file_contents=file_contents
        )

        def message_too_long(message):
            return num_tokens_from_messages(message, MODEL_NAME) >= MAX_CONTEXT_LENGTH

        while message_too_long(message) and len(contents) > 1:
            logger.info(f'reducing to \n{len(contents)} files')
            contents = contents[:-1]
            file_contents = ''.join(contents)
            message = template.format(
                problem_statement=problem_statement, file_contents=file_contents
            )  # Recreate message

        if message_too_long(message):
            logger.info
            raise ValueError(
                'The remaining file content is too long to fit within the context length'
            )
        logger.info(f'prompting with message:\n{message}')
        logger.info('=' * 80)

        raw_output = self.llm.completion(
            model=MODEL_NAME,
            messages=[{'content': message, 'role': 'user'}],
            temperature=0,
            max_tokens=MAX_TOKENS,
        )['choices'][0]['message']['content']

        model_found_locs = extract_code_blocks(raw_output)
        model_found_locs_separated = extract_locs_for_files(
            model_found_locs, file_names
        )

        logger.info('==== raw output ====')
        logger.info(raw_output)
        logger.info('=' * 80)
        logger.info('==== extracted locs ====')
        for loc in model_found_locs_separated:
            logger.info(loc)
        logger.info('=' * 80)

        print(raw_output)

        return model_found_locs_separated

    def agentless_line_level_localization(
        self, file_names, found_related_locs, problem_statement, structure
    ):
        from Agentless.agentless.fl.FL import LLMFL
        from Agentless.agentless.repair.repair import (
            construct_topn_file_context,
        )
        from Agentless.agentless.util.api_requests import (
            num_tokens_from_messages,
        )
        from Agentless.agentless.util.postprocess_data import (
            extract_code_blocks,
            extract_locs_for_files,
        )
        from Agentless.agentless.util.preprocess_data import (
            get_repo_files,
        )

        coarse_locs = {}
        for i, pred_file in enumerate(file_names):
            if len(found_related_locs) > i:
                coarse_locs[pred_file] = found_related_locs[i]

        file_contents = get_repo_files(structure, file_names)
        topn_content, _ = construct_topn_file_context(
            coarse_locs,
            file_names,
            file_contents,
            structure,
            context_window=CONTEXT_WINDOW,
            loc_interval=True,
            add_space=ADD_SPACE,
            sticky_scroll=STICKY_SCROLL,
            no_line_number=NO_LINE_NUMBER,
        )
        if NO_LINE_NUMBER:
            template = LLMFL.obtain_relevant_code_combine_top_n_no_line_number_prompt
        else:
            template = LLMFL.obtain_relevant_code_combine_top_n_prompt
        message = template.format(
            problem_statement=problem_statement, file_contents=topn_content
        )
        logger.info(f'prompting with message:\n{message}')
        logger.info('=' * 80)
        assert num_tokens_from_messages(message, MODEL_NAME) < MAX_CONTEXT_LENGTH

        raw_trajs = self.llm.completion(
            model=MODEL_NAME,
            messages=[{'content': message, 'role': 'user'}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            n=NUM_SAMPLES,
        )['choices']
        # raw_trajs = model.codegen(message, num_samples=NUM_SAMPLES)

        # Merge trajectories
        raw_outputs = [raw_traj['message']['content'] for raw_traj in raw_trajs]

        model_found_locs_separated_in_samples = []
        for raw_output in raw_outputs:
            model_found_locs = extract_code_blocks(raw_output)
            model_found_locs_separated = extract_locs_for_files(
                model_found_locs, file_names
            )
            model_found_locs_separated_in_samples.append(model_found_locs_separated)

            logger.info('==== raw output ====')
            logger.info(raw_output)
            logger.info('=' * 80)
            print(raw_output)
            print('=' * 80)
            logger.info('==== extracted locs ====')
            for loc in model_found_locs_separated:
                logger.info(loc)
            logger.info('=' * 80)
        logger.info('==== Input coarse_locs')
        coarse_info = ''
        for fn, found_locs in coarse_locs.items():
            coarse_info += f'### {fn}\n'
            if isinstance(found_locs, str):
                coarse_info += found_locs + '\n'
            else:
                coarse_info += '\n'.join(found_locs) + '\n'
        logger.info('\n' + coarse_info)
        if len(model_found_locs_separated_in_samples) == 1:
            model_found_locs_separated_in_samples = (
                model_found_locs_separated_in_samples[0]
            )

        merged_locs = []
        merged_locs.append(
            model_found_locs_separated_in_samples[0]
            + model_found_locs_separated_in_samples[1]
        )
        merged_locs.append(
            model_found_locs_separated_in_samples[2]
            + model_found_locs_separated_in_samples[3]
        )

        def flatten_innermost_strings(nested_list):
            if isinstance(nested_list, list):
                # Check if we have a list with a single item which is a string
                if len(nested_list) == 1 and isinstance(nested_list[0], str):
                    return nested_list[0]
                # Otherwise, recursively process each element in the list
                return [flatten_innermost_strings(item) for item in nested_list]
            else:
                return nested_list

        return flatten_innermost_strings(merged_locs)

    def agentless_repair(
        self, structure, found_files, found_edit_locs, problem_statement
    ):
        from Agentless.agentless.repair.repair import (
            _post_process_multifile_repair,
            construct_topn_file_context,
            repair_prompt_combine_topn,
            repair_prompt_combine_topn_cot,
            repair_prompt_combine_topn_cot_diff,
            repair_relevant_file_instruction,
        )
        from Agentless.agentless.util.preprocess_data import (
            get_full_file_paths_and_classes_and_functions,
        )

        pred_files = found_files[:TOP_N]
        file_to_edit_locs = {}
        for i, pred_file in enumerate(pred_files):
            if len(found_edit_locs) > i:
                file_to_edit_locs[pred_file] = found_edit_locs[i]

        files, _, _ = get_full_file_paths_and_classes_and_functions(structure)

        # Construct file contents
        file_contents = dict()
        for i, pred_file in enumerate(pred_files):
            content = None

            for file_content in files:
                if file_content[0] == pred_file:
                    content = '\n'.join(file_content[1])
                    file_contents[pred_file] = content
                    break

        topn_content, file_loc_intervals = construct_topn_file_context(
            file_to_edit_locs,
            pred_files,
            file_contents,
            structure,
            context_window=CONTEXT_WINDOW,
            loc_interval=LOC_INTERVAL,
            fine_grain_loc_only=FINE_GRAIN_LOC_ONLY,
            add_space=ADD_SPACE,
            no_line_number=NO_LINE_NUMBER,
            sticky_scroll=STICKY_SCROLL,
        )

        if topn_content.strip() == '':
            return []

        prompt_template = (
            repair_prompt_combine_topn_cot_diff
            if COT and DIFF_FORMAT
            else repair_prompt_combine_topn_cot
            if COT
            else repair_prompt_combine_topn
        )
        file_instruction = repair_relevant_file_instruction
        message = prompt_template.format(
            repair_relevant_file_instruction=file_instruction,
            problem_statement=problem_statement,
            content=topn_content.rstrip(),
        ).strip()
        logger.info(f'prompting with message:\n{message}')

        all_generations, counts, _, prev_contents, file_names = [], [], [], [], []
        sample_responses: List[Dict[str, Any]] = []
        # Using early stopping will cost more since the input tokens will be charged multiple times.
        # For now we disable it.
        assert STOP_AT_N_UNIQUE_VALID_SAMPLES == -1

        if SKIP_GREEDY:
            greedy_traj = {
                'response': '',
                'usage': {
                    'completion_tokens': 0,
                    'prompt_tokens': 0,
                },
            }
        else:
            greedy_traj = self.llm.completion(
                model=MODEL_NAME,
                messages=[{'content': message, 'role': 'user'}],
                temperature=0,
                max_tokens=1024,
            )['choices'][0]
        sample_responses.append(greedy_traj)

        if MAX_SAMPLES - 1:
            sample_trajs = self.llm.completion(
                model=MODEL_NAME,
                messages=[{'content': message, 'role': 'user'}],
                temperature=TEMPERATURE,
                max_tokens=1024,
                n=MAX_SAMPLES - 1,
            )['choices']
        else:
            sample_trajs = []

        sample_responses.extend(sample_trajs)

        count = 0
        raw_outputs = []
        while count < MAX_SAMPLES:
            print(f'trying the {count + 1}-th sample ...')
            raw_output = sample_responses[count]['message']['content']
            count += 1

            all_generations.append(raw_output)

            edited_file, new_content = _post_process_multifile_repair(
                raw_output,
                file_contents,
                logger,
                file_loc_intervals,
                diff_format=DIFF_FORMAT,
            )

            if new_content == '':
                prev_contents.append('')
                file_names.append('')
            else:
                prev_content = file_contents[edited_file]
                prev_contents.append(prev_content)
                file_names.append(edited_file)

            counts.append(count)
            raw_outputs.append(raw_output)
        return raw_outputs, prev_contents, file_names

    def post_process_raw_output(
        self, raw_output_text, file_contents, logger, file_loc_intervals
    ):
        from difflib import unified_diff

        from Agentless.agentless.repair.repair import (
            _post_process_multifile_repair,
        )
        from Agentless.agentless.util.postprocess_data import (
            check_code_differ_by_just_empty_lines,
            check_syntax,
            fake_git_repo,
            lint_code,
        )

        git_diffs = ''
        raw_git_diffs = ''
        lint_success = False
        content = ''
        try:
            edited_file, new_content = _post_process_multifile_repair(
                raw_output_text,
                file_contents,
                logger,
                file_loc_intervals,
                diff_format=DIFF_FORMAT,
            )
            logger.info('EDITED FILE')
            logger.info(edited_file)
            logger.info('NEW CONTENT')
            logger.info(new_content)
            if edited_file in file_contents:
                content = file_contents[edited_file]

                git_diff = fake_git_repo(
                    'playground', edited_file, content, new_content
                )
                logger.info('1 git diff')
                logger.info(git_diff)

                raw_git_diffs += '\n' + git_diff.replace(
                    '\\ No newline at end of file\n', ''
                )

                syntax_success = check_syntax(new_content)
                lint_success, prev_errors, errors = lint_code(
                    'playground', 'test.py', new_content, file_contents[edited_file]
                )

                differ_by_empty_lines = check_code_differ_by_just_empty_lines(
                    new_content, file_contents[edited_file]
                )

                print(lint_success, prev_errors, errors, differ_by_empty_lines)
                logger.info(
                    f'checks pass: {lint_success, prev_errors, errors, differ_by_empty_lines}'
                )
                if syntax_success and not differ_by_empty_lines:
                    git_diffs = raw_git_diffs
                else:
                    git_diffs = ''  # no need to evaluate
            else:
                diff = list(
                    unified_diff(
                        content.split('\n'),
                        new_content.split('\n'),
                        fromfile=edited_file,
                        tofile=edited_file,
                        lineterm='',
                    )
                )
                print('Failed parsing diff!')
                print('\n'.join(diff))
        except Exception as e:
            print(raw_output_text)
            print(e)

        return git_diffs, raw_git_diffs, content

    def agentless_post_process_repair(
        self,
        pred_files,
        found_edit_locs,
        generation_original_file_contents,
        generation_pred_files,
        raw_outputs,
    ):
        """
        apply some diff formatting. Also strips comments and trailing spaces to better identify identical patches
        """
        from Agentless.agentless.util.postprocess_data import normalize_patch
        from Agentless.agentless.util.preprocess_data import (
            transfer_arb_locs_to_locs,
        )

        processed_patches = []
        for generation_idx, raw_output_text in enumerate(raw_outputs):
            if raw_output_text != '':
                try:
                    original_file_content = generation_original_file_contents[
                        generation_idx
                    ]
                    pred_file = generation_pred_files[
                        generation_idx
                    ]  # Not sure if this works

                    git_diffs = ''

                    file_contents = {pred_file: original_file_content}

                    file_loc_intervals = dict()

                    for i, tmp_pred_file in enumerate(pred_files):
                        if tmp_pred_file != pred_file:
                            continue
                        if len(found_edit_locs) > i:
                            # try:
                            _, context_intervals = transfer_arb_locs_to_locs(
                                found_edit_locs[i],
                                None,
                                pred_files[i],
                                CONTEXT_WINDOW,
                                LOC_INTERVAL,
                                FINE_GRAIN_LOC_ONLY,
                                file_content=file_contents[pred_file]
                                if pred_file in file_contents
                                else '',
                            )
                            logger.info('context interval')
                            logger.info(context_intervals)
                        else:
                            _, context_intervals = [], []  # default values.

                except Exception as e:
                    logger.info('file loc interval error')
                    logger.info(e)
                    print(e)
                    raw_output_text = ''

                file_loc_intervals[pred_file] = context_intervals

                logger.info('RAW OUTPUT TEXT')
                logger.info(raw_output_text)

                if raw_output_text:
                    logger.info('FILE LOCAL INTERVAL')
                    logger.info(file_loc_intervals)
                    logger.info('FILE CONTENT')
                    logger.info(file_contents)
                    git_diffs, raw_git_diffs, content = self.post_process_raw_output(
                        raw_output_text, file_contents, logger, file_loc_intervals
                    )

                    # Setting 0 as the instance_id since this function doesn't
                    # actually use the instance_id for anything
                    logger.info('GIT DIFF BEFORE NORMALIZING')
                    logger.info(git_diffs)
                    patch_lines = git_diffs.split('\n')
                    patch_lines = [
                        line for line in patch_lines if not line.startswith('index')
                    ]
                    git_diffs = '\n'.join(patch_lines)

                    normalized_patch = normalize_patch(
                        0, git_diffs, original_file_content
                    )

                    normalized_lines = normalized_patch.split('\n')
                    normalized_lines = [
                        line
                        for line in normalized_lines
                        if not line.startswith('index')
                    ]
                    normalized_patch = '\n'.join(patch_lines)

                    if normalized_patch.lstrip():
                        processed_patches.append(
                            [
                                normalized_patch,
                                git_diffs.replace(
                                    '\\ No newline at end of file\n', ''
                                ).lstrip(),
                            ]
                        )

        return [patch for patch in processed_patches if patch[0].strip() != '']


def most_frequent_string(processed_patches):
    if not processed_patches:
        return None  # Return None if the list is empty

    # Count the frequency of each string in the list
    counter = Counter([patch[0] for patch in processed_patches])

    # Find the string with the highest frequency
    most_common_normalized_patch, freq = counter.most_common(1)[0]
    print('Number of times most frequent patch occured: ', freq)
    for patch in processed_patches:
        if patch[0] == most_common_normalized_patch:
            return patch[1]
