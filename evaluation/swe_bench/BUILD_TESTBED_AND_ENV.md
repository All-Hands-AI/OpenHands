# Pre-build Testbed and Env

In the original SWE-Bench implementation, conda environment for evaluation is typically installed from scratch while evaluating on a particular instance. This poses several challenges:

- Efficiency: most time of evaluation will be wasted on downloading packages
- Stability: setup could failed due to bad internet connectivity
- Reliability: it is possible that an instance is considered failed not because the agent did badly, but because the environment setup failed.

In OpenDevin-SWE-Bench fork, we try to pre-build the **testbed** (i.e., code of the repository we want the agent to edit) AND the **conda environment**, so that in evaluation (inference) time, we can directly leverage existing environments for efficient evaluation.

NOTE: We only support SWE-Bench lite for now. But modifying our existing scripts for full SWE-Bench should be quite straight forward.

## How to pre-build your testbed

### Setup Eval Workspace (Util + Data)

Setup your eval workspace by:
1. Clone OpenDevin SWE-Bench [fork](https://github.com/OpenDevin/OD-SWE-bench.git)
2. Prepare SWE-Bench data

Run the following command to do the above two steps. The results will be saved to `evaluation/SWE-bench/eval_workspace`.

```bash
./evaluation/swe_bench/scripts/setup/prepare_swe_utils.sh
```

### Pre-build Conda Env and Test Bed

```bash
./evaluation/swe_bench/scripts/setup/swe_env_setup.sh
```

### Build the pre-build conda env and testbed into ONE docker image

```bash
pushd evaluation/swe_bench
docker build -t ghcr.io/opendevin/eval-swe-bench:full-v1.2.1 -f ./scripts/docker/Dockerfile.full.v1.1 .
docker push ghcr.io/opendevin/eval-swe-bench:full-v1.2.1
```
