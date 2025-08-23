#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.insert(0, '/workspace/project/OpenHands')

from evaluation.benchmarks.webarena.run_infer import initialize_runtime, get_config
from evaluation.utils.shared import EvalMetadata, make_metadata
from openhands.core.config import load_from_toml
from openhands.runtime.impl.docker.docker_runtime import DockerRuntime
from openhands.utils.async_utils import call_async_from_sync
import pandas as pd

def debug_webarena_goal():
    """Debug what the WebArena goal looks like"""
    
    # Create a minimal instance for testing
    instance = pd.Series({
        'instance_id': 'browsergym/webarena.247',
        'instruction': 'Test instruction'
    })
    
    # Load LLM config
    config_dict = load_from_toml('config.toml')
    llm_config = config_dict['llm']['claude-sonnet-4']
    
    # Create metadata
    metadata = make_metadata(
        llm_config=llm_config,
        dataset_name='webarena',
        agent_class='CodeActAgent',
        max_iterations=15,
        eval_note=None,
        eval_output_dir='evaluation/evaluation_outputs/outputs/webarena/CodeActAgent/debug',
        details=None,
    )
    
    config = get_config(metadata, instance.instance_id)
    
    # Create runtime
    runtime = DockerRuntime(config.sandbox_config)
    call_async_from_sync(runtime.connect)
    
    print("=== DEBUGGING WEBARENA GOAL ===")
    
    # Get the goal
    try:
        task_str = initialize_runtime(runtime)
        print(f"Goal text type: {type(task_str)}")
        print(f"Goal text length: {len(str(task_str))}")
        print(f"Goal text content: {repr(task_str)}")
        
        if task_str:
            print("✅ Goal text is not empty")
        else:
            print("❌ Goal text is empty!")
            
    except Exception as e:
        print(f"❌ Error getting goal: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            call_async_from_sync(runtime.close)
        except:
            pass

if __name__ == "__main__":
    debug_webarena_goal()