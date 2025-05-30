import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from evaluation.utils.shared import EvalMetadata

def loc_output_archive(
        instance: pd.Series,
        metadata: EvalMetadata,
        histories: List,
        metrics: Dict,
    ):
    """Save loc outputs"""
    # Save dir
    llm_model_name = metadata.llm_config.model.replace('/', '_').replace('.', '_').strip()
    
    # History
    history_save_dir = os.path.join(metadata.details['loc_eval_save'], llm_model_name, "histories")
    os.makedirs(history_save_dir, exist_ok=True)
    history_save_pth = os.path.join(history_save_dir, f"instance_{instance.instance_id}.json")
    with open(history_save_pth, "w") as file:
        json.dump(histories, file, indent=4)

    # Metrics
    metric_save_dir = os.path.join(metadata.details['loc_eval_save'], llm_model_name, "metrics")
    os.makedirs(metric_save_dir, exist_ok=True)
    metric_save_pth = os.path.join(metric_save_dir, f"instance_{instance.instance_id}.json")
    with open(metric_save_pth, "w") as file:
        json.dump(metrics, file, indent=4)
        