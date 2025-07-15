set up llm in config.toml

[llm.gemini25-pro]
api_key = ...
model = ...

huggingface-cli login
docker login docker.io -u sweperf

evaluation/benchmarks/swe_perf/scripts/run_infer.sh llm.gemini25-pro HEAD CodeActAgent -1 100 4 sweperf/sweperf test

[model_config] [git-version] [agent] [eval_limit] [max_iter] [num_workers] [dataset] [dataset_split] [n_runs] [mode]
