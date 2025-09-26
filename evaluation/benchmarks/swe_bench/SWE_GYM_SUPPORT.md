# SWE-Gym Support in OpenHands

This document describes how to use OpenHands with the SWE-Gym dataset, which extends SWE-bench with additional repositories.

## Overview

SWE-Gym is an extension of SWE-bench that includes 11 additional repositories:
- Project-MONAI/MONAI
- python/mypy
- conan-io/conan
- iterative/dvc
- getmoto/moto
- bokeh/bokeh
- pydantic/pydantic
- dask/dask
- facebookresearch/hydra
- modin-project/modin

## Setup

To use SWE-Gym with OpenHands, you need to install the modified SWE-bench that includes test specifications for SWE-Gym repositories:

```bash
pip install -r evaluation/benchmarks/swe_bench/requirements-swegym.txt
```

## Usage

### Running Evaluation with SWE-Gym

Use the standard evaluation script with the SWE-Gym dataset:

```bash
./evaluation/benchmarks/swe_bench/scripts/eval_infer.sh \
    path/to/your/output.jsonl \
    "" \
    "SWE-Gym/SWE-Gym" \
    "train" \
    modal
```

### Dataset Information

- **Dataset Name**: `SWE-Gym/SWE-Gym`
- **Total Instances**: 2,438
- **Repositories**: 11 (in addition to the original SWE-bench repositories)
- **Split**: `train` (currently the only available split)

## Technical Details

The SWE-Gym support includes:

1. **Test Specifications**: Added test specs for all 11 SWE-Gym repositories in the SWE-bench harness
2. **Requirements Mapping**: Configured proper requirements file paths for each repository
3. **Version Mapping**: Added all repository versions to the evaluation harness
4. **Environment Setup**: Configured Python versions and test commands for each repository

## Supported Repositories

| Repository | Versions | Requirements Files | Test Command |
|------------|----------|-------------------|--------------|
| Project-MONAI/MONAI | 20 versions | requirements-dev.txt | pytest |
| python/mypy | 20 versions | test-requirements.txt, mypy-requirements.txt | pytest |
| conan-io/conan | 20 versions | conans/requirements.txt, conans/requirements_dev.txt | pytest |
| iterative/dvc | 20 versions | pyproject.toml (no requirements) | pytest |
| getmoto/moto | 20 versions | requirements-dev.txt | pytest |
| bokeh/bokeh | 20 versions | pyproject.toml (no requirements) | pytest |
| pydantic/pydantic | 20 versions | pyproject.toml (no requirements) | pytest |
| dask/dask | 20 versions | pyproject.toml (no requirements) | pytest |
| facebookresearch/hydra | 20 versions | requirements/requirements.txt | pytest |
| modin-project/modin | 20 versions | requirements-dev.txt | pytest |

## Troubleshooting

If you encounter issues:

1. **Authentication**: Ensure you have proper Hugging Face authentication for accessing the SWE-Gym dataset
2. **Dependencies**: Make sure you've installed the modified SWE-bench using the requirements file
3. **Dataset Access**: Verify you can access the SWE-Gym dataset: `from datasets import load_dataset; load_dataset("SWE-Gym/SWE-Gym", split="train")`

## Changes Made

The SWE-Gym support required modifications to the SWE-bench evaluation harness:

1. **Added test specifications** for all 11 SWE-Gym repositories
2. **Updated repository mappings** to include SWE-Gym repositories
3. **Configured requirements paths** for each repository's dependency files
4. **Enhanced requirement handling** for repositories using pyproject.toml

These changes are available in the forked SWE-bench repository referenced in `requirements-swegym.txt`.
