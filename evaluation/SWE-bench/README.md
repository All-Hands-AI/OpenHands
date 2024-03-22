# SWE-Bench Evaluation

Work in-progress.

**TODOs**:

- [ ] Generate `predictions` files given an OpenDevin `Agent` implementation. We could borrow something from [devin's eval-harness implementation](https://github.com/CognitionAI/devin-swebench-results/tree/main/harness), for example, [how to generate `TestSpec`](https://github.com/CognitionAI/devin-swebench-results/blob/main/harness/scripts.py#L150-L160).
- [ ] Make sure the evaluation suite runs on all repos. I only tested on `matplotlib` so far, `scikit-learn` does not work for now (see [this issue](https://github.com/princeton-nlp/SWE-bench/issues/57))).


## Run tests for a prediction file inside a docker container

Currently, the docker container should be able to for running SWE-Bench. It was tested on `matplotlib`, but it requires further testing to make sure it works on other repositories. Currently, [it does not work for `scikit-learn`](https://github.com/princeton-nlp/SWE-bench/issues/57)).

### Setup example data

```bash
cd evaluation/SWE-bench
./scripts/prepare_devin_swe_bench_data.sh

# Clone the repo
# This is a fork that fixes some issues that stops matplotlib from running (see https://github.com/princeton-nlp/SWE-bench/pull/56)
git clone https://github.com/OpenDevin/SWE-bench.git

# Enter the docker container
./scripts/run_docker_interactive.sh
```

### Run evaluation

```bash
#!/bin/bash
rm -rf data/logs/ data/testbeds/ # (Optional) remove previous outputs
mkdir -p data/logs
mkdir -p data/testbeds

python SWE-bench/harness/run_evaluation.py \
    --predictions_path data/predictions/devin_swe_outputs.json \
    --swe_bench_tasks data/processed/swe-bench-test.json \
    --log_dir data/logs \
    --testbed data/testbeds \
    --skip_existing \
    --timeout 900 \
    --verbose
```

You will see the command line outputs similar to this (if success):

```log
swe-bench@2f3a6b9fcab2:/swe-bench$ ./harness/run_evaluation.sh
/swe-bench/harness/run_evaluation.py:101: SyntaxWarning: assertion is always true, perhaps remove parentheses?
  assert(temp, datasets.arrow_dataset.Dataset)
2024-03-20 09:21:18,796 - INFO - Found 1 predictions across 1 model(s) in predictions file
2024-03-20 09:21:18,796 - INFO - [claude-2/matplotlib__matplotlib/3.6] # of predictions to evaluate: 1 (0 already evaluated)
2024-03-20 09:21:18,797 - INFO - [Testbed] Creating log directory /swe-bench/data/logs/claude-2
2024-03-20 09:21:18,797 - INFO - [Testbed] Using conda path /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmp09wrm708
2024-03-20 09:21:18,797 - INFO - [Testbed] Using working directory /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmpfy1qth23 for testbed
2024-03-20 09:21:18,797 - INFO - [Testbed] Repo matplotlib/matplotlib: 1 versions
2024-03-20 09:21:18,797 - INFO - [Testbed]      Version 3.6: 1 instances
2024-03-20 09:21:18,797 - INFO - No conda path provided, creating temporary install in /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmp09wrm708/miniconda3...
2024-03-20 09:21:27,482 - INFO - [Testbed] Using conda path /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmp09wrm708/miniconda3
2024-03-20 09:21:27,942 - INFO - [Testbed] Setting up testbed for matplotlib__matplotlib__3.6
2024-03-20 09:21:44,257 - INFO - [Testbed] Cloned matplotlib/matplotlib to /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmpfy1qth23/matplotlib__matplotlib__3.6
2024-03-20 09:21:44,415 - INFO - [Testbed] Creating environment matplotlib__matplotlib__3.6; Command: /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmp09wrm708/miniconda3/bin/conda env create --file /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmpfy1qth23/environment.yml
2024-03-20 09:23:39,781 - INFO - [Testbed] Installing pip packages for matplotlib__matplotlib__3.6; Command: . /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmp09wrm708/miniconda3/bin/activate matplotlib__matplotlib__3.6 && pip install pytest
/swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmpfy1qth23/matplotlib__matplotlib__3.6: 1 instances
2024-03-20 09:23:42,309 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Reset task environment to aca6e9d5e98811ca37c442217914b15e78127c89
2024-03-20 09:23:42,314 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Apply patch successful (pred_try)
2024-03-20 09:23:42,318 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Revert patch successful (pred_try)
2024-03-20 09:23:42,318 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Installing with command: . /swe-bench/data/testbeds/claude-2/matplotlib__matplotlib/3.6/tmp09wrm708/miniconda3/bin/activate matplotlib__matplotlib__3.6 && echo 'activate successful' && python -m pip install -e .
2024-03-20 09:24:54,966 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Installation successful
2024-03-20 09:24:54,970 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Apply patch successful (test)
2024-03-20 09:24:54,974 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Apply patch successful (pred)
2024-03-20 09:25:04,775 - INFO - [matplotlib__matplotlib__3.6] [matplotlib__matplotlib-24362] Test script run successful
swe-bench@2f3a6b9fcab2:/swe-bench$ 
```

### Interpret Results

Then you may interpret the results under `data/logs`, and interpret it following [this guide](https://github.com/princeton-nlp/SWE-bench/blob/main/tutorials/evaluation.md#-metrics).
