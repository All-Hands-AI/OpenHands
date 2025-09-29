from pathlib import Path
pro_output = Path("evaluation/evaluation_outputs/outputs/swefficiency__swefficiency_lite-test/CodeActAgent/gemini-2.5-pro_maxiter_100_N_v0.51.1-no-hint-run_1/output.jsonl")
flash_output = Path("evaluation/evaluation_outputs/outputs/swefficiency__swefficiency-test/CodeActAgent/gemini-2.5-flash_maxiter_100_N_v0.51.1-no-hint-run_1/gemini25flash_raw.jsonl")


# Read in both jsonl files and filter out lines from flash where instance_id not in pro output.
import json

pro_instance_id_to_dict = {}

from datasets import load_dataset

ds_lite = load_dataset("swefficiency/swefficiency_lite", split="test")
ds_instance_ids = set([x["instance_id"] for x in ds_lite])

with open(pro_output, "r") as f:
    for line in f:
        data = json.loads(line)
        pro_instance_id_to_dict[data["instance_id"]] = data

flash_instance_id_to_dict = {}
with open(flash_output, "r") as f:
    for line in f:
        data = json.loads(line)
        print(data["metrics"].keys())
        if data["instance_id"] in ds_instance_ids:
            flash_instance_id_to_dict[data["instance_id"]] = data

total_flash_cost = 0
total_pro_cost = 0

total_model_latency_flash = 0
total_model_latency_pro = 0

for k in pro_instance_id_to_dict:
    pro_cost = (pro_instance_id_to_dict[k].get("metrics") or dict()).get("accumulated_cost", 0)

    flash_cost = (flash_instance_id_to_dict.get(k, {}).get("metrics") or dict()).get("accumulated_cost", 0)
    total_pro_cost += pro_cost
    total_flash_cost += flash_cost

    model_latency_flash = (flash_instance_id_to_dict.get(k, {}).get("metrics") or dict()).get("response_latencies", [])
    model_latency_pro = (pro_instance_id_to_dict.get(k, {}).get("metrics") or dict()).get("response_latencies", [])

    print(model_latency_flash)

    total_model_latency_flash += sum([d["latency"] for d in model_latency_flash])
    total_model_latency_pro += sum([d["latency"] for d in model_latency_pro])

print(f"Total Pro Cost: {total_pro_cost}")
print(f"Total Flash Cost: {total_flash_cost}")
print(f"Total Pro Model Latency: {total_model_latency_pro}")
print(f"Total Flash Model Latency: {total_model_latency_flash}")
