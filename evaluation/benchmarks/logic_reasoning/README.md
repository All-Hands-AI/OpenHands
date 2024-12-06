# Logic Reasoning Evaluation

This folder contains evaluation harness for evaluating agents on the logic reasoning benchmark [ProntoQA](https://github.com/asaparov/prontoqa) and [ProofWriter](https://allenai.org/data/proofwriter).

## Setup Environment and LLM Configuration

Please follow instruction [here](../../README.md#setup) to setup your local development environment and LLM.

## Run Inference on logic_reasoning

The following code will run inference on the first example of the ProofWriter dataset,

```bash
./evaluation/benchmarks/logic_reasoning/scripts/run_infer.sh eval_gpt4_1106_preview_llm ProofWriter
```
