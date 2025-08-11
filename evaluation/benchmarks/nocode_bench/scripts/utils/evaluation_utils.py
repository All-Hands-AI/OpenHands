import json
import multiprocessing as mp
from typing import TextIO, Callable, Awaitable

import numpy as np
import pandas as pd
from pydantic import SecretStr
from tqdm import tqdm

from evaluation.utils.shared import EvalOutput, EvalMetadata, _process_instance_wrapper_mp, _process_instance_wrapper
from openhands.core.logger import openhands_logger as logger


def update_progress_nc(
        result: EvalOutput,
        pbar: tqdm,
        output_fp: TextIO,
):
    """Update the progress bar and write the result to the output file."""
    pbar.update(1)
    pbar.set_description(f"Instance {result.instance_id}")
    pbar.set_postfix_str(f"Test Result: {str(result.test_result)[:300]}...")
    logger.info(
        f"Finished evaluation for instance {result.instance_id}: "
        f"{str(result.test_result)[:300]}...\n"
    )

    def make_serializable(obj):
        if isinstance(obj, pd.Series):
            return make_serializable(obj.to_dict())

        if isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}

        elif isinstance(obj, (list, tuple, set)):
            converted = [make_serializable(v) for v in obj]
            if isinstance(obj, list):
                return converted
            elif isinstance(obj, tuple):
                return tuple(converted)
            else:  # set
                return converted

        elif isinstance(obj, np.ndarray):
            return obj.tolist()

        elif isinstance(obj, np.generic):
            return obj.item()

        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()

        elif SecretStr is not None and isinstance(obj, SecretStr):
            return str(obj)

        else:
            return obj

    try:
        raw_data = result.model_dump(mode="python", round_trip=False)
        safe_data = make_serializable(raw_data)
        output_fp.write(json.dumps(safe_data, ensure_ascii=False) + "\n")
        output_fp.flush()

    except Exception as e:
        logger.error(f"Failed to write full result: {e}")

        fallback = {
            "instance_id": result.instance_id,
            "model_patch": result.test_result.get("git_patch", ""),
        }
        try:
            output_fp.write(json.dumps(fallback, ensure_ascii=False) + "\n")
            output_fp.flush()
            logger.info(
                f"Wrote fallback result for instance {result.instance_id}: only instance_id and model_patch."
            )
        except Exception as e2:
            logger.error(f"Failed to write fallback result: {e2}")


def cleanup():
    print('Cleaning up child processes...')
    for process in mp.active_children():
        print(f'Terminating child process: {process.name}')
        process.terminate()
        process.join()


def run_evaluation_nocode_bench(
        dataset: pd.DataFrame,
        metadata: EvalMetadata | None,
        output_file: str,
        num_workers: int,
        process_instance_func: Callable[
            [pd.Series, EvalMetadata, bool], Awaitable[EvalOutput]
        ],
        max_retries: int = 5,  # number of retries for each instance
        timeout_seconds: int | None = None,
):
    use_multiprocessing = num_workers > 1

    if metadata is not None:
        logger.info(
            f'Evaluation started with Agent {metadata.agent_class}:\n'
            f'model {metadata.llm_config.model}, max iterations {metadata.max_iterations}.\n'
        )
    else:
        logger.warning('Running evaluation without metadata.')
        logger.info(f'Evaluation started with {num_workers} workers.')

    total_instances = len(dataset)
    pbar = tqdm(total=total_instances, desc='Instances processed')
    output_fp = open(output_file, 'a')

    try:
        if use_multiprocessing:
            with mp.Pool(num_workers) as pool:
                args_iter = (
                    (
                        process_instance_func,
                        instance,
                        metadata,
                        True,
                        max_retries,
                        timeout_seconds,
                    )
                    for _, instance in dataset.iterrows()
                )
                results = pool.imap_unordered(_process_instance_wrapper_mp, args_iter)
                for result in results:
                    update_progress_nc(result, pbar, output_fp)
        else:
            for _, instance in dataset.iterrows():
                result = _process_instance_wrapper(
                    process_instance_func=process_instance_func,
                    instance=instance,
                    metadata=metadata,
                    use_mp=False,
                    max_retries=max_retries,
                )
                update_progress_nc(result, pbar, output_fp)

    except KeyboardInterrupt:
        print('\nKeyboardInterrupt received. Cleaning up...\n')
        cleanup()

    output_fp.close()
    logger.info('\nEvaluation finished.\n')
