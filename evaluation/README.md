# Evaluation

This folder contains code and resources to run experiments and evaluations.

## Logistics
To better organize the evaluation folder, we should follow the rules below:
  - Each subfolder contains a specific benchmark or experiment. For example, `evaluation/SWE-bench` should contain
all the preprocessing/evaluation/analysis scripts.
  - Raw data and experimental records should not be stored within this repo (e.g. Google Drive or Hugging Face Datasets).
  - Important data files of manageable size and analysis scripts (e.g., jupyter notebooks) can be directly uploaded to this repo.

## Roadmap

- Sanity check. Reproduce Devin's scores on SWE-bench using the released outputs to make sure that our harness pipeline works.
- Open source model support.
  - Contributors are encouraged to submit their commits to our [forked SEW-bench repo](https://github.com/OpenDevin/SWE-bench).
  - Ensure compatibility with OpenAI interface for inference.
  - Serve open source models, prioritizing high concurrency and throughput.

## SWE-bench
- notebooks
  - `devin_eval_analysis.ipynb`: notebook analyzing devin's outputs
- scripts
  - `prepare_devin_outputs_for_evaluation.py`: script fetching and converting [devin's output](https://github.com/CognitionAI/devin-swebench-results/tree/main) into the desired json file for evaluation.
    - usage: `python prepare_devin_outputs_for_evaluation.py <setting>` where setting can be `passed`, `failed` or `all`
- resources
  - Devin related SWE-bench test subsets
    - [🤗 OpenDevin/SWE-bench-devin-passed](https://huggingface.co/datasets/OpenDevin/SWE-bench-devin-passed)
    - [🤗 OpenDevin/SWE-bench-devin-full-filtered](https://huggingface.co/datasets/OpenDevin/SWE-bench-devin-full-filtered)
  - Devin's outputs processed for evaluations is available on [Huggingface](https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output)
    - get predictions that passed the test: `wget https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output/raw/main/devin_swe_passed.json`
    - get all predictions `wget https://huggingface.co/datasets/OpenDevin/Devin-SWE-bench-output/raw/main/devin_swe_outputs.json`

See [`SWE-bench/README.md`](./SWE-bench/README.md) for more details on how to run SWE-Bench for evaluation.

### Results

We have refined the original SWE-bench evaluation pipeline to enhance its efficiency and reliability. The updates are as follows:
- Reuse testbeds and Conda environments.
- Additionally try `patch` command for patch application if `git apply` command fails.

#### Results on SWE-bench-devin-passed

[🤗 OpenDevin/SWE-bench-devin-passed](https://huggingface.co/datasets/OpenDevin/SWE-bench-devin-passed)

| Model/Agent            | #instances | #init | #apply | #resolve |
|------------------------|------------|-------|--------|----------|
| Gold                   | 79         | 79    | 79     | 79       |
| Devin                  | 79         | 79    | 76     | 76       |

#init: number of instances where testbeds have been successfully initialized.

In the 3 Devin-failed instances (see below), Devin has made changes to the tests, which are incomptible with the provided test patch and causes failures during patch application. The evaluation adopted by Devin does not seem to align with the original SWE-bench evaluation.

```shell
django__django-11244
scikit-learn__scikit-learn-10870
sphinx-doc__sphinx-9367
```

#### Results on SWE-bench-devin-failed

| Model/Agent            | #instances | #init | #apply | #resolve |
|------------------------|------------|-------|--------|----------|
| Gold                   | 491        | 491   | 491    | 371      |
| Devin                  | 491        | 491   | 463    | 7        |

Devin **passes** 7 instances on the `SWE-bench-devin-failed` subset. SWE-bench dataset appears to be noisy, evidenced by 120 instances where gold patches do not pass.

We have filtered out the problematic 120 instances, resulting in the creation of the `SWE-bench-devin-full-filtered` subset.

## Results on SWE-bench-devin-full-filtered

[🤗 OpenDevin/SWE-bench-devin-full-filtered](https://huggingface.co/datasets/OpenDevin/SWE-bench-devin-full-filtered)

| Model/Agent            | #instances | #init | #apply | #resolve |
|------------------------|------------|-------|--------|----------|
| Gold                   | 450        | 450   | 450    | 450      |
| Devin                  | 450        | 450   | 426    | 83       |