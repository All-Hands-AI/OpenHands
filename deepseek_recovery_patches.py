INSTANCES_ALREADY_RUN = set([
    "scikit-learn__scikit-learn-24856","pandas-dev__pandas-26721","numpy__numpy-21354","pandas-dev__pandas-53013","pandas-dev__pandas-30747","pandas-dev__pandas-37945","pandas-dev__pandas-33540","pandas-dev__pandas-52054","pandas-dev__pandas-43694","scipy__scipy-13107","pandas-dev__pandas-53088","astropy__astropy-12701","pandas-dev__pandas-45242","scikit-learn__scikit-learn-28064","pandas-dev__pandas-24308","pandas-dev__pandas-48504","pandas-dev__pandas-27669","pandas-dev__pandas-34199","pandas-dev__pandas-38353","pandas-dev__pandas-43353","pandas-dev__pandas-45247","scipy__scipy-10921","pandas-dev__pandas-36325","pandas-dev__pandas-49851","pandas-dev__pandas-48472","scipy__scipy-14625","dask__dask-6293","pandas-dev__pandas-26702","pandas-dev__pandas-43281","scikit-learn__scikit-learn-22106","pydata__xarray-7382","pandas-dev__pandas-43634","pandas-dev__pandas-46235","pandas-dev__pandas-42631","matplotlib__matplotlib-14504","pandas-dev__pandas-44943","numpy__numpy-24610","pandas-dev__pandas-43725","pandas-dev__pandas-31300","matplotlib__matplotlib-26164","pandas-dev__pandas-38148","pandas-dev__pandas-43010","dask__dask-6491","pandas-dev__pandas-57855","pandas-dev__pandas-41567","pandas-dev__pandas-54835","pandas-dev__pandas-59647","pandas-dev__pandas-52548","astropy__astropy-7643","pandas-dev__pandas-43237","astropy__astropy-7649","pandas-dev__pandas-56508","matplotlib__matplotlib-19760","astropy__astropy-7549","dask__dask-7403","numpy__numpy-12321","pandas-dev__pandas-37971","matplotlib__matplotlib-17994","pandas-dev__pandas-43308","pydata__xarray-7374","scikit-learn__scikit-learn-15834","matplotlib__matplotlib-29399","pandas-dev__pandas-44908","pandas-dev__pandas-56110","pydata__xarray-7824","pandas-dev__pandas-40840","pandas-dev__pandas-51518","numpy__numpy-19601","pandas-dev__pandas-55515","pydata__xarray-9808","pandas-dev__pandas-51784","pydata__xarray-9429","astropy__astropy-16813","pandas-dev__pandas-43510","pandas-dev__pandas-24023","pandas-dev__pandas-44857","matplotlib__matplotlib-17177","astropy__astropy-12699","scipy__scipy-11478","scipy__scipy-10564","numpy__numpy-25788","pandas-dev__pandas-32883","pandas-dev__pandas-42714","pandas-dev__pandas-56841","scikit-learn__scikit-learn-13290","scipy__scipy-10393","pandas-dev__pandas-56128","pandas-dev__pandas-36872","pandas-dev__pandas-49577","scipy__scipy-13611","pandas-dev__pandas-38379","scipy__scipy-16599","astropy__astropy-17004","pandas-dev__pandas-26015","dask__dask-7104","pandas-dev__pandas-36638","pandas-dev__pandas-48338","pandas-dev__pandas-43578","pandas-dev__pandas-25953","pandas-dev__pandas-40072","scipy__scipy-10477","pandas-dev__pandas-53731","dask__dask-5501","dask__dask-10428","scikit-learn__scikit-learn-25713","pandas-dev__pandas-24491","pandas-dev__pandas-42197","pandas-dev__pandas-56061","pandas-dev__pandas-42704","scikit-learn__scikit-learn-15615","scipy__scipy-10939","pandas-dev__pandas-44758","pandas-dev__pandas-37064","matplotlib__matplotlib-26899","matplotlib__matplotlib-18756","pandas-dev__pandas-43696","pandas-dev__pandas-46040","pandas-dev__pandas-44192","pandas-dev__pandas-34192","pandas-dev__pandas-46330","pandas-dev__pandas-23888","pandas-dev__pandas-40254","numpy__numpy-13250","pandas-dev__pandas-52672","pandas-dev__pandas-29134","astropy__astropy-6940","numpy__numpy-25299","numpy__numpy-18324","pandas-dev__pandas-41911","pandas-dev__pandas-36317","scikit-learn__scikit-learn-22206","matplotlib__matplotlib-13917","pandas-dev__pandas-56919","pandas-dev__pandas-37118","numpy__numpy-11720","pandas-dev__pandas-30768","dask__dask-7023","pandas-dev__pandas-49772","pandas-dev__pandas-34948","pandas-dev__pandas-33032","pandas-dev__pandas-25070","astropy__astropy-16670","astropy__astropy-13471","astropy__astropy-8998","scikit-learn__scikit-learn-17737","pandas-dev__pandas-43683","numpy__numpy-18203","matplotlib__matplotlib-22108","pandas-dev__pandas-47234","pandas-dev__pandas-44594","pandas-dev__pandas-43823","numpy__numpy-19620","scikit-learn__scikit-learn-25490","pandas-dev__pandas-29820","pandas-dev__pandas-57560","dask__dask-5890","pandas-dev__pandas-40035","pandas-dev__pandas-55898","pandas-dev__pandas-31037","astropy__astropy-16222","pandas-dev__pandas-39664","dask__dask-6186","numpy__numpy-13697","pandas-dev__pandas-39388","scikit-learn__scikit-learn-13310","pandas-dev__pandas-44666","dask__dask-5933","pandas-dev__pandas-44832","pandas-dev__pandas-46109","pandas-dev__pandas-24083","pandas-dev__pandas-43171","pandas-dev__pandas-57812","scipy__scipy-12001","pandas-dev__pandas-43059","pydata__xarray-9001","pandas-dev__pandas-34052","astropy__astropy-8502","matplotlib__matplotlib-23287","pandas-dev__pandas-59608","pandas-dev__pandas-42611","astropy__astropy-13899","pandas-dev__pandas-30797","dask__dask-5553","pandas-dev__pandas-42998","matplotlib__matplotlib-22875","matplotlib__matplotlib-23759","pandas-dev__pandas-27448","pandas-dev__pandas-51344","numpy__numpy-21832","pandas-dev__pandas-43274","astropy__astropy-7616","pandas-dev__pandas-40178","pandas-dev__pandas-32826","pydata__xarray-7735","scipy__scipy-11982","astropy__astropy-17425","astropy__astropy-6941","pandas-dev__pandas-25820","pandas-dev__pandas-43354","pandas-dev__pandas-41972","matplotlib__matplotlib-15834","pandas-dev__pandas-55839","pandas-dev__pandas-52145","pandas-dev__pandas-43558","scikit-learn__scikit-learn-23149","astropy__astropy-13497","pandas-dev__pandas-34737","pandas-dev__pandas-57034","pandas-dev__pandas-39332","scipy__scipy-13566","numpy__numpy-19608","pandas-dev__pandas-32825","numpy__numpy-21394","matplotlib__matplotlib-17995","astropy__astropy-7924","numpy__numpy-19609","astropy__astropy-16742","pandas-dev__pandas-52430","pydata__xarray-7472","astropy__astropy-16243","pandas-dev__pandas-53231","pandas-dev__pandas-27495","pandas-dev__pandas-26711","pandas-dev__pandas-43277","astropy__astropy-8428","matplotlib__matplotlib-26198","scikit-learn__scikit-learn-27344","pandas-dev__pandas-43073","pandas-dev__pandas-42268","scikit-learn__scikit-learn-15049","astropy__astropy-13898","astropy__astropy-16096","pandas-dev__pandas-26391","dask__dask-10356","pandas-dev__pandas-26605","pandas-dev__pandas-55131","pandas-dev__pandas-43332","pandas-dev__pandas-37569","astropy__astropy-15900","pandas-dev__pandas-42353","astropy__astropy-8349","dask__dask-5891","pydata__xarray-7796","scipy__scipy-10467","numpy__numpy-19599","numpy__numpy-24663","scikit-learn__scikit-learn-21837","pandas-dev__pandas-25665","scikit-learn__scikit-learn-17235","scikit-learn__scikit-learn-9843","pandas-dev__pandas-36432","pandas-dev__pandas-33324","pandas-dev__pandas-53955","pandas-dev__pandas-43524","pandas-dev__pandas-46349","scipy__scipy-10064","pandas-dev__pandas-56089","astropy__astropy-7422","pandas-dev__pandas-44566","pandas-dev__pandas-56806","numpy__numpy-26599","scipy__scipy-11757","scikit-learn__scikit-learn-10610","scikit-learn__scikit-learn-25186","astropy__astropy-16673","pandas-dev__pandas-34354","numpy__numpy-27830","pandas-dev__pandas-30171","astropy__astropy-16088","dask__dask-11625","pandas-dev__pandas-43285","pandas-dev__pandas-43760","scikit-learn__scikit-learn-15257","pandas-dev__pandas-57459","pandas-dev__pandas-48976","pandas-dev__pandas-51339","pandas-dev__pandas-52928","pandas-dev__pandas-60121","pandas-dev__pandas-57534","scikit-learn__scikit-learn-22235","pandas-dev__pandas-32856","pandas-dev__pandas-42486","pandas-dev__pandas-26776","dask__dask-7172","matplotlib__matplotlib-18018","pydata__xarray-4740","pandas-dev__pandas-50310","pandas-dev__pandas-55736","pandas-dev__pandas-55084","scipy__scipy-12474","pandas-dev__pandas-43160","pandas-dev__pandas-51592","astropy__astropy-8494","astropy__astropy-17461","pandas-dev__pandas-26697","pandas-dev__pandas-56997","pandas-dev__pandas-46107","pandas-dev__pandas-52836","pandas-dev__pandas-32821","dask__dask-10922","pandas-dev__pandas-53806","astropy__astropy-16295","pandas-dev__pandas-56062","pandas-dev__pandas-34178","pandas-dev__pandas-29469","dask__dask-6669","numpy__numpy-12575","scikit-learn__scikit-learn-17878","scikit-learn__scikit-learn-29060","pandas-dev__pandas-38560","pandas-dev__pandas-52685","pandas-dev__pandas-48611","pandas-dev__pandas-48502","pandas-dev__pandas-56345","scikit-learn__scikit-learn-29835","pandas-dev__pandas-48609","pandas-dev__pandas-37426","pandas-dev__pandas-40339","pandas-dev__pandas-42270","astropy__astropy-17043","scipy__scipy-12587","pandas-dev__pandas-43243","scipy__scipy-11358","pandas-dev__pandas-39972","pandas-dev__pandas-35166","pandas-dev__pandas-37450","pydata__xarray-5661","pandas-dev__pandas-38103","numpy__numpy-19618","pandas-dev__pandas-52111","pandas-dev__pandas-44610","dask__dask-5940","pandas-dev__pandas-37149","pandas-dev__pandas-37130","matplotlib__matplotlib-21564","scikit-learn__scikit-learn-19606","pandas-dev__pandas-32130","matplotlib__matplotlib-15346","pandas-dev__pandas-43335","pandas-dev__pandas-45708","pandas-dev__pandas-61014","pandas-dev__pandas-43352","pandas-dev__pandas-45854","pandas-dev__pandas-26773","pandas-dev__pandas-36280","pandas-dev__pandas-44827","pandas-dev__pandas-49596","pandas-dev__pandas-45931","matplotlib__matplotlib-19564","pandas-dev__pandas-43589","astropy__astropy-7010","pandas-dev__pandas-31409","dask__dask-5884","pandas-dev__pandas-27384","numpy__numpy-12596","pandas-dev__pandas-58992","pandas-dev__pandas-43370","pandas-dev__pandas-41924"
])

# For already run instances.

from pathlib import Path
import re

infer_logs = Path("evaluation/evaluation_outputs/outputs/swefficiency__swefficiency-test/CodeActAgent/deepseek-reasoner_maxiter_100_N_v0.51.1-no-hint-run_1/infer_logs_backup")

pattern = re.compile(
    r'(?ms)^.*?-\s+INFO\s+-\s+Got git diff for instance[^\n]*:\s*\r?\n'
    r'(?P<hr>-{3,})\s*\r?\n'
    r'(?P<diff>.*?)'
    r'\r?\n(?P=hr)(?:\r?\n|$)'
)

output_file = Path("evaluation/evaluation_outputs/outputs/swefficiency__swefficiency-test/CodeActAgent/deepseek-reasoner_maxiter_100_N_v0.51.1-no-hint-run_1/output.jsonl")
trajectory_dir = Path("/home/ubuntu/OpenHands/evaluation/evaluation_outputs/outputs/swefficiency__swefficiency-test/CodeActAgent/deepseek-reasoner_maxiter_100_N_v0.51.1-no-hint-run_1/llm_completions")

import json

predictions = []
for line in output_file.read_text().splitlines():
    if line.strip():
        item = json.loads(line)

    history = item.get("history") or []
    history = [
        h
        for h in history
        if h.get("action") is not None and h.get("source") == "agent"
    ]
    traj_len = len(history)

    eval_entry = {
        "instance_id": item["instance_id"],
        "model_patch": item["test_result"].get("git_patch", ""),
        "model_name_or_path": item["metadata"]["eval_output_dir"].split("/")[-1],
        "trajectory_length": traj_len,
    }
    predictions.append(eval_entry)

# Assume all predictions are from the same model.
run_name = predictions[0]["model_name_or_path"]

# Convert to SWE-fficiency format.
for instance_id in INSTANCES_ALREADY_RUN:
    print("Processing already run instance:", instance_id)

    log_file = infer_logs / f"instance_{instance_id}.log"
    full_log_text = log_file.read_text()

    m = re.search(pattern, full_log_text)
    diff_text = m.group("diff") if m else None

    if diff_text is None:
        print(f"  No diff found in log for instance {instance_id}, skipping.")
        print("  Log file content preview:", str(log_file))
        diff_text = ""

    trajectory_file = trajectory_dir / instance_id
    # Get the lexical last file in the trajectory directory.
    traj_files = sorted(trajectory_file.glob("*.json"))
    trajectory_actions = []
    if traj_files:
        last_traj_file = traj_files[-1]

        # Read in json, and count number of entries.
        trajectory = json.loads(last_traj_file.read_text())
        trajectory_actions = [
            msg for msg in trajectory["messages"] if msg.get("role") == "assistant"
        ]

    predictions.append({
        "instance_id": instance_id,
        "model_patch": diff_text,
        "model_name_or_path": run_name,
        "trajectory_length": len(trajectory_actions),
    })

# Save to a new jsonl.
output_recovered_file = output_file.parent / f"{output_file.stem}_with_recovered.jsonl"
with output_recovered_file.open("w") as f:
    for pred in predictions:
        f.write(json.dumps(pred) + "\n")

print(f"Saved combined results to {output_recovered_file}")
